#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import StyleMemoryStore, quick_audit  # noqa: E402
from tools.model_longform_compare import (  # noqa: E402
    DEEPSEEK_DEFAULT_MODEL,
    KIMI_DEFAULT_MODEL,
    load_local_env,
    run_non_stream,
)

COMPARE_ROOT = ROOT / ".cache" / "writing" / "compare_ai_market_repricing_20260625"
OUTPUT_DIR = COMPARE_ROOT / "final_three"

TITLE = "AI 公司营收还在涨，为什么资本市场先开始怀疑了？"

HARD_BAN_PATTERNS = {
    "二段反转": r"不是.{0,16}而是",
    "真正的问题": r"真正的(问题|关键)",
    "底层逻辑": r"底层逻辑",
    "机遇与挑战": r"机遇与挑战",
    "前一句是真的": r"前一句是真的|后一句没有那么真",
    "轻重对照": r"看起来很轻，背后其实很重",
}

AI_TASTE_PATTERNS = {
    "随着发展": r"随着.{0,10}(发展|变化)",
    "深刻变化": r"深刻变化|深刻改变",
    "赋能": r"赋能",
    "闭环": r"闭环",
    "多维度": r"多维度",
    "重塑": r"重塑",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def extract_body(md_text: str) -> str:
    text = md_text.strip()
    if text.startswith("# "):
        parts = text.split("\n", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def count_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


def spoken_minutes(text: str) -> float:
    chars = count_chars(text)
    return round(chars / 340, 1) if chars else 0.0


def scan_patterns(body: str, patterns: dict[str, str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for name, pattern in patterns.items():
        found = re.findall(pattern, body)
        if found:
            hits[name] = [str(item) for item in found[:5]]
    return hits


def gate_result(script_name: str, draft_path: Path) -> dict[str, object]:
    import subprocess

    proc = subprocess.run(
        ["python3", str(ROOT / "tools" / script_name), str(draft_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return {
        "script": script_name,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "exitCode": proc.returncode,
        "output": lines,
    }


def skill_effect_level(*, hard_hits: dict[str, list[str]], ai_hits: dict[str, list[str]], audit_findings: int, gate_summary: dict[str, str]) -> tuple[str, str]:
    if hard_hits or ai_hits:
        return "明显", "这份稿子有明显表层问题，avoid-ai-writing 这类 skill 能直接清掉禁句、空话和 AI 口吻。"
    if audit_findings >= 2:
        return "中等", "这份稿子表层不算脏，但句子重心和表达姿势还有机器味，skill 作为二次审稿会有帮助。"
    if gate_summary.get("insight") == "FAIL" or gate_summary.get("oral_script") == "FAIL":
        return "有限", "这份稿子的主要问题在观点密度或口播结构，skill 只能修表层，不能替代重写主线。"
    return "有限", "这份稿子表层已经比较干净，skill 只能做小幅收口。"


def audit_text(title: str, body: str, draft_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        store = StyleMemoryStore(Path(temp_dir) / "style_memory.jsonl", Path(temp_dir) / "style_memory_deleted.jsonl")
        audit = quick_audit(title, body, store)
    hard_hits = scan_patterns(body, HARD_BAN_PATTERNS)
    ai_hits = scan_patterns(body, AI_TASTE_PATTERNS)
    gates = {
        "topic_viability": gate_result("topic_viability_gate.py", draft_path),
        "insight": gate_result("insight_gate.py", draft_path),
        "oral_script": gate_result("oral_script_gate.py", draft_path),
    }
    gate_summary = {name: str(info["status"]) for name, info in gates.items()}
    skill_level, skill_note = skill_effect_level(
        hard_hits=hard_hits,
        ai_hits=ai_hits,
        audit_findings=len(audit.get("findings") or []),
        gate_summary=gate_summary,
    )
    return {
        "chars": count_chars(body),
        "spokenMinutes": spoken_minutes(body),
        "quickAuditSummary": audit.get("summaryLine", ""),
        "quickAuditFindings": len(audit.get("findings") or []),
        "hardBanHits": hard_hits,
        "aiTasteHits": ai_hits,
        "gateSummary": gate_summary,
        "gates": gates,
        "skillEffect": {
            "level": skill_level,
            "note": skill_note,
        },
    }


def build_prompt(brief: str, style_context: str) -> str:
    return (
        f"标题：{TITLE}\n\n"
        f"{brief.strip()}\n\n"
        "补充要求：\n"
        "- 直接写成完整中文文章，不要提纲，不要 JSON，不要解释。\n"
        "- 开头必须从 2026 年 6 月这轮市场变冷切入。\n"
        "- 文中必须出现至少两个美股公司例子，并接上国内模型厂商。\n"
        "- 结尾必须落到一句明确判断：行业考题已经从模型能力切到现金流。\n"
        "- 一段只做一件事，口播友好，不要写成财报摘要。\n"
        f"- 风格约束：\n{style_context.strip()}\n"
    )


def generate_provider_body(provider: str, prompt: str) -> tuple[str, dict[str, object]]:
    system = "你是中文长文作者。直接输出完整正文，不要解释，不要 JSON，不要项目符号。"
    if provider == "kimi":
        payload = {
            "model": os.environ.get("KIMI_MODEL", KIMI_DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "thinking": {"type": "enabled"},
            "max_tokens": int(os.environ.get("KIMI_COMPARE_MAX_TOKENS", "8000")),
            "temperature": float(os.environ.get("KIMI_TEMPERATURE", "1")),
        }
        timeout = 420
    elif provider == "deepseek":
        payload = {
            "model": os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "thinking": {"type": "enabled"},
            "reasoning_effort": os.environ.get("DEEPSEEK_FULL_REASONING_EFFORT", "high"),
            "max_tokens": int(os.environ.get("DEEPSEEK_FULL_MAX_TOKENS", "8000")),
            "temperature": 0.55,
        }
        timeout = 300
    else:
        raise ValueError(provider)
    draft, meta = run_non_stream(provider, payload, timeout=timeout)
    return str(draft["body"]).strip(), meta


def write_skill_report(report: dict[str, dict[str, object]], output_path: Path) -> None:
    lines = ["# skill 优化判断", ""]
    lines.append("说明：这里只判断 `avoid-ai-writing` 这类 skill 对三份成稿有没有实际优化作用，不额外再生成第四套文章。")
    for name in ("codex", "kimi", "deepseek"):
        item = report[name]
        skill = item["skillEffect"]
        lines.extend(
            [
                "",
                f"## {name}",
                f"- 字数：{item['chars']} 字，约 {item['spokenMinutes']} 分钟",
                f"- quick audit：{item['quickAuditSummary'] or '无明显硬伤'}",
                f"- gates：topic={item['gateSummary'].get('topic_viability')} / insight={item['gateSummary'].get('insight')} / oral={item['gateSummary'].get('oral_script')}",
                f"- skill 作用：{skill['level']}",
                f"- 结论：{skill['note']}",
            ]
        )
        if item["hardBanHits"]:
            lines.append(f"- 命中禁句：{', '.join(item['hardBanHits'].keys())}")
        if item["aiTasteHits"]:
            lines.append(f"- 命中 AI 味：{', '.join(item['aiTasteHits'].keys())}")
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    load_local_env()
    brief = read(Path(os.environ.get("FINAL_COMPARE_BRIEF", COMPARE_ROOT / "brief_compact.md")))
    style_context = read(Path(os.environ.get("FINAL_COMPARE_STYLE", COMPARE_ROOT / "style_context.md")))
    codex_source = read(Path(os.environ.get("FINAL_COMPARE_CODEX", COMPARE_ROOT / "codex_final_source.md")))
    codex_body = extract_body(codex_source)
    prompt = build_prompt(brief, style_context)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)

    codex_path = OUTPUT_DIR / "codex_final.md"
    write_md(codex_path, TITLE, codex_body)

    print("[done] codex_final.md", flush=True)
    kimi_body, kimi_meta = generate_provider_body("kimi", prompt)
    kimi_path = OUTPUT_DIR / "kimi_final.md"
    write_md(kimi_path, TITLE, kimi_body)
    print("[done] kimi_final.md", flush=True)

    deepseek_body, deepseek_meta = generate_provider_body("deepseek", prompt)
    deepseek_path = OUTPUT_DIR / "deepseek_final.md"
    write_md(deepseek_path, TITLE, deepseek_body)
    print("[done] deepseek_final.md", flush=True)

    report = {
        "codex": audit_text(TITLE, codex_body, codex_path),
        "kimi": audit_text(TITLE, kimi_body, kimi_path),
        "deepseek": audit_text(TITLE, deepseek_body, deepseek_path),
    }
    report["codex"]["meta"] = {"provider": "codex", "mode": "manual"}
    report["kimi"]["meta"] = kimi_meta
    report["deepseek"]["meta"] = deepseek_meta

    (OUTPUT_DIR / "meta.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_skill_report(report, OUTPUT_DIR / "skill_effect.md")
    print(str(OUTPUT_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
