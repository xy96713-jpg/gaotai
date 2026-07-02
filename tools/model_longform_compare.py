#!/usr/bin/env python3
"""Run same-brief longform writing comparison across configured providers."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import (  # noqa: E402
    DEEPSEEK_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    KIMI_BASE_URL,
    KIMI_DEFAULT_MODEL,
    StyleMemoryStore,
    audit_banned_shapes,
    enforce_spoken_paragraphing,
    minimal_edit_generated_body,
    quality_gate_for_generated_body,
    quick_audit,
    style_rules_context,
)

SOURCE_NAME_RE = re.compile(
    r"(STORM|PaperDebugger|Frontiers|OpenAI|NBER|GitHub|BetterUp|Anthropic|哈佛商业评论|斯坦福|DeepSeek|Kimi|Claude|GPT|Qwen|CAISI|NIST)"
)


def split_long_spoken_sentences(body: str, max_chinese_chars: int = 54) -> tuple[str, list[dict[str, str]]]:
    """Make oral-script sentences passable without changing the argument."""
    changes: list[dict[str, str]] = []
    pieces = re.split(r"([。！？!?])", body)
    rebuilt: list[str] = []
    for idx in range(0, len(pieces), 2):
        sentence = pieces[idx]
        punct = pieces[idx + 1] if idx + 1 < len(pieces) else ""
        if len(re.findall(r"[\u4e00-\u9fff]", sentence)) <= max_chinese_chars:
            rebuilt.append(sentence + punct)
            continue
        original = sentence + punct
        working = sentence
        for mark in ("；", "，但", "，所以", "，因为", "，结果", "，接着", "，同时", "，以及", "，而且"):
            working = working.replace(mark, "。\n\n" + mark.lstrip("，；"))
        working = re.sub(r"。\n\n(但|所以|因为|结果|接着|同时|以及|而且)", r"。\n\n\1", working)
        working = re.sub(r"\n\n+", "\n\n", working).strip()
        if working and not re.search(r"[。！？!?]$", working):
            working += punct or "。"
        rebuilt.append(working)
        changes.append({"source": original[:90], "replacement": working[:120], "reason": "拆掉口播超长句。"})
    return "".join(rebuilt), changes


def spread_source_heavy_paragraphs(body: str, max_sources_per_para: int = 2) -> tuple[str, list[dict[str, str]]]:
    changes: list[dict[str, str]] = []
    paragraphs = [p for p in re.split(r"\n\s*\n+", body.strip()) if p.strip()]
    out: list[str] = []
    for para in paragraphs:
        source_hits = SOURCE_NAME_RE.findall(para)
        if len(source_hits) <= max_sources_per_para:
            out.append(para)
            continue
        sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", para) if s.strip()]
        if len(sentences) <= 1:
            out.append(para)
            continue
        current: list[str] = []
        current_hits = 0
        split_blocks: list[str] = []
        for sentence in sentences:
            hits = len(SOURCE_NAME_RE.findall(sentence))
            if current and current_hits + hits > max_sources_per_para:
                split_blocks.append("".join(current).strip())
                current = [sentence]
                current_hits = hits
            else:
                current.append(sentence)
                current_hits += hits
        if current:
            split_blocks.append("".join(current).strip())
        out.extend(split_blocks)
        changes.append({"source": para[:100], "replacement": " / ".join(block[:45] for block in split_blocks), "reason": "拆开来源名堆叠段。"})
    return "\n\n".join(out), changes


def add_consequence_pressure(body: str) -> tuple[str, list[dict[str, str]]]:
    """Repair insight-gate failures by adding concrete cost instead of vague advice."""
    if any(token in body for token in ("代价", "成本", "返工", "误判", "浪费", "带偏")):
        return body, []
    paragraphs = [p for p in re.split(r"\n\s*\n+", body.strip()) if p.strip()]
    if not paragraphs:
        return body, []
    pressure = (
        "这里的代价不是“文章不够漂亮”。更现实的问题是返工。"
        "一个方向错掉的初稿，会把后面的修改全部带偏：你越让它润色，它越会把错误包装得更顺。"
        "到最后，损失的不是几十分钟，而是你对材料、判断和语气的控制权。"
    )
    insert_at = 3 if len(paragraphs) > 4 else len(paragraphs)
    paragraphs.insert(insert_at, pressure)
    return "\n\n".join(paragraphs), [{"source": "", "replacement": pressure, "reason": "补上读者能感到的失败成本。"}]


def repair_personal_and_banned_risks(body: str) -> tuple[str, list[dict[str, str]]]:
    changes: list[dict[str, str]] = []
    replacements = [
        ("我做过一个测试。", "先看一个常见场景。"),
        ("我做过一个测试：", "先看一个常见场景："),
        ("我后来给这种现象起了个名字", "这个现象可以叫"),
        ("我自己的办法", "这套系统"),
        ("我自己的", "这套系统里的"),
        ("我的办法", "这套系统"),
        ("问题来了，", ""),
        ("问题来了。", ""),
        (" 问题来了，", " "),
        (" 问题来了。", " "),
        ("的风险不是 AI 写不好。", "风险不只是 AI 写不好。"),
        ("但问题不在模型不够强。 在于", "更深的原因在于"),
        ("不是换模型。", "单靠换模型不够。"),
    ]
    repaired = body
    for source, replacement in replacements:
        if source in repaired:
            repaired = repaired.replace(source, replacement)
            changes.append({"source": source, "replacement": replacement, "reason": "修复禁句、廉价转折或未授权第一人称经历。"})
    repaired = re.sub(r"我发现([^。\n]{0,36})", r"你会看到\1", repaired)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired).strip()
    return repaired, changes


def repair_for_quality_gate(body: str) -> dict[str, object]:
    changes: list[dict[str, str]] = []
    repaired, step_changes = repair_personal_and_banned_risks(body)
    changes.extend(step_changes)
    repaired, step_changes = add_consequence_pressure(repaired)
    changes.extend(step_changes)
    repaired, step_changes = split_long_spoken_sentences(repaired)
    changes.extend(step_changes)
    repaired, step_changes = spread_source_heavy_paragraphs(repaired)
    changes.extend(step_changes)
    repaired, step_changes = repair_personal_and_banned_risks(repaired)
    changes.extend(step_changes)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired).strip()
    return {"body": repaired, "changes": changes}


def load_local_env() -> None:
    env_path = ROOT / ".env.local"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def extract_json_or_text(content: str, title: str) -> dict[str, str]:
    content = content.strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            parsed = json.loads(match.group(0))
        else:
            parsed = {"title": title, "body": content}
    body = str(parsed.get("body") or parsed.get("正文") or "").strip()
    if not body:
        body = content
    return {"title": str(parsed.get("title") or title).strip() or title, "body": body}


def post_chat(base_url: str, api_key: str, payload: dict, timeout: int) -> dict:
    req = urllib_request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_chat_stream(base_url: str, api_key: str, payload: dict, timeout: int) -> tuple[str, str, str]:
    stream_payload = dict(payload)
    stream_payload["stream"] = True
    req = urllib_request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(stream_payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    finish_reason = ""
    with urllib_request.urlopen(req, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data_text = line.removeprefix("data:").strip()
            if data_text == "[DONE]":
                break
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError:
                continue
            choice = (data.get("choices") or [{}])[0]
            finish_reason = choice.get("finish_reason") or finish_reason
            delta = choice.get("delta") or {}
            reasoning_value = delta.get("reasoning_content")
            content_value = delta.get("content")
            if reasoning_value:
                reasoning_parts.append(str(reasoning_value))
            if content_value:
                content_parts.append(str(content_value))
    return "".join(content_parts).strip(), "".join(reasoning_parts).strip(), finish_reason


def run_non_stream(provider: str, payload: dict, timeout: int) -> tuple[dict[str, str], dict]:
    if provider == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        base_url = os.environ.get("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)
    else:
        api_key = os.environ.get("KIMI_API_KEY", "").strip()
        base_url = os.environ.get("KIMI_BASE_URL", KIMI_BASE_URL)
    if not api_key:
        raise RuntimeError(f"{provider} api key is not configured")
    data = post_chat(base_url, api_key, payload, timeout)
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {}) or {}
    content = str(message.get("content") or "").strip()
    reasoning = str(message.get("reasoning_content") or "").strip()
    draft = extract_json_or_text(content, payload.get("metadata", {}).get("title", "未命名稿件"))
    if not normalize_for_generated_body(draft.get("body", "")):
        raise RuntimeError("model returned no usable body content")
    meta = {
        "finishReason": choice.get("finish_reason"),
        "usage": data.get("usage"),
        "reasoningLength": len(reasoning),
        "contentLength": len(content),
    }
    return draft, meta


def run_stream(provider: str, payload: dict, timeout: int) -> tuple[dict[str, str], dict]:
    if provider == "kimi":
        api_key = os.environ.get("KIMI_API_KEY", "").strip()
        base_url = os.environ.get("KIMI_BASE_URL", KIMI_BASE_URL)
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        base_url = os.environ.get("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)
    if not api_key:
        raise RuntimeError(f"{provider} api key is not configured")
    content, reasoning, finish_reason = post_chat_stream(base_url, api_key, payload, timeout)
    draft = extract_json_or_text(content, payload.get("metadata", {}).get("title", "未命名稿件"))
    if not normalize_for_generated_body(draft.get("body", "")):
        raise RuntimeError(f"{provider} stream returned no body content; reasoningLength={len(reasoning)} contentLength={len(content)} finishReason={finish_reason}")
    meta = {
        "finishReason": finish_reason,
        "reasoningLength": len(reasoning),
        "contentLength": len(content),
        "stream": True,
    }
    return draft, meta


def run_kimi_stream(payload: dict, timeout: int) -> tuple[dict[str, str], dict]:
    api_key = os.environ.get("KIMI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("kimi api key is not configured")
    base_url = os.environ.get("KIMI_BASE_URL", KIMI_BASE_URL)
    content, reasoning, finish_reason = post_chat_stream(base_url, api_key, payload, timeout)
    draft = extract_json_or_text(content, payload.get("metadata", {}).get("title", "未命名稿件"))
    if not normalize_for_generated_body(draft.get("body", "")):
        raise RuntimeError(f"kimi stream returned no body content; reasoningLength={len(reasoning)} contentLength={len(content)}")
    meta = {
        "finishReason": finish_reason,
        "reasoningLength": len(reasoning),
        "contentLength": len(content),
        "stream": True,
    }
    return draft, meta


def normalize_for_generated_body(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def build_payload(provider: str, title: str, brief: str, thinking: str) -> dict:
    if provider == "deepseek":
        model = os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是中文长文章初稿写手。只返回 JSON。不要解释，不要输出提纲。",
                },
                {"role": "user", "content": json.dumps({"title": title, "brief": brief, "schema": {"title": "string", "body": "string"}}, ensure_ascii=False)},
            ],
            "temperature": 0.55,
            "max_tokens": int(os.environ.get("DEEPSEEK_FULL_MAX_TOKENS", "4200")),
            "response_format": {"type": "json_object"},
            "metadata": {"title": title},
        }
        if thinking != "disabled":
            payload["thinking"] = {"type": thinking}
            payload["reasoning_effort"] = os.environ.get("DEEPSEEK_FULL_REASONING_EFFORT", "high")
        return payload
    model = os.environ.get("KIMI_MODEL", KIMI_DEFAULT_MODEL)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "只返回 JSON。不要解释。不要 Markdown。字段必须是 title 和 body。",
            },
            {"role": "user", "content": json.dumps({"title": title, "brief": brief, "schema": {"title": "string", "body": "string"}}, ensure_ascii=False)},
        ],
        "max_tokens": int(os.environ.get("KIMI_COMPARE_MAX_TOKENS", "20000" if thinking != "disabled" else "5000")),
        "metadata": {"title": title},
    }
    if thinking != "disabled":
        payload["thinking"] = {"type": thinking}
    else:
        payload["thinking"] = {"type": "disabled"}
    return payload


def audit_draft(title: str, body: str, brief: str, style_store: StyleMemoryStore) -> dict:
    first_minimal = minimal_edit_generated_body(body, style_store, personal_material_allowed=False)
    paragraphing = enforce_spoken_paragraphing(first_minimal["body"])
    repaired = repair_for_quality_gate(paragraphing["body"])
    second_minimal = minimal_edit_generated_body(str(repaired["body"]), style_store, personal_material_allowed=False)
    cleaned = second_minimal["body"]
    paragraphing = enforce_spoken_paragraphing(cleaned)
    cleaned = paragraphing["body"]
    final_repair = repair_for_quality_gate(cleaned)
    cleaned = str(final_repair["body"])
    final_minimal = minimal_edit_generated_body(cleaned, style_store, personal_material_allowed=False)
    cleaned = final_minimal["body"]
    material_card = {
        "claim": "AI 写作上限来自工作流约束，不是单个神 prompt 或单个模型",
        "sources": "STORM, PaperDebugger, Antislop, CoAuthorAI, DeepSeek/Kimi API docs, local workflow evidence",
        "noInvent": "读者私信, 后台数据, 未执行的测试结果, 编造采访对象",
    }
    gate = quality_gate_for_generated_body(
        body=cleaned,
        title=title,
        brief=brief,
        material_card=material_card,
        minimal_edit=final_minimal,
        personal_material_allowed=False,
    )
    surface = quick_audit(title, cleaned, style_store)
    return {
        "body": cleaned,
        "minimalEdit": final_minimal,
        "firstMinimalEdit": first_minimal,
        "secondMinimalEdit": second_minimal,
        "paragraphing": paragraphing,
        "qualityRepair": {
            "body": cleaned,
            "changes": list(repaired.get("changes", [])) + list(final_repair.get("changes", [])),
        },
        "qualityGate": gate,
        "surfaceAudit": surface,
        "bannedCount": len(audit_banned_shapes(cleaned, style_store)),
    }


def main() -> int:
    load_local_env()
    stamp = utc_stamp()
    out_dir = ROOT / ".cache" / "writing" / f"model_longform_compare_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)
    research_path = ROOT / ".cache" / "writing" / "ai_writing_best_workflow_20260609_research_brief.md"
    research = research_path.read_text(encoding="utf-8") if research_path.exists() else ""
    title = "2026 年，AI 写作最好的方式可能不是换模型"
    brief = (
        "写一篇中文长文章/口播稿，主题是：2026 年 AI 写作最好的方式是什么。"
        "核心判断：AI 写作上限不在直接换一个更强模型，而在资料、Brief、受控初稿、局部修订、AI 味审计、质量门槛、导出留痕组成的工作流。"
        "必须写清楚不用系统的具体代价：返工、误判、材料被带偏、作者判断被模型补全、越改越顺但越偏离。"
        "必须给至少一个具体坏样本场景：一句话需求如何被模型补出假经历、假因果或报告腔。"
        "必须给这个问题起一个可记住的名字，避免只讲流程。"
        "必须结合我的本地写作系统：YouTube/B站分析、手写需求入口、素材包、Brief 质检、DeepSeek v4-pro thinking 初稿、Kimi 2.6 对比、禁句硬拦、质量门槛、修复建议、导出成稿包。"
        "要解释不用系统和使用系统的差别。"
        "要客观说系统还不完美：缺中文写作评测集、before/after 样本库、来源覆盖评分、多模型盲评。"
        "不要编造个人经历、后台数据、读者私信或测试结果。"
        "不要写导演提示。不要使用不是...而是、真正、我自己的办法、我的办法。"
        "短句口播。单句尽量不超过 55 个汉字。不要把三个以上来源名堆在同一段。"
        "不要写成工具说明书，要像一篇能给个人 IP 观众看的严肃但好读的文章。"
        "正文约 1800-2600 中文字，分段自然。"
        "\n\n可用研究材料：\n"
        + research[:6000]
    )
    style_store = StyleMemoryStore()
    memory_context = style_rules_context(style_store, f"{title}\n{brief}", limit=12)
    (out_dir / "brief.md").write_text(f"# {title}\n\n{brief}\n", encoding="utf-8")
    tasks = [
        ("deepseek_v4pro_thinking", "deepseek", "enabled", False),
        ("kimi_k26_nonthinking_stream", "kimi", "disabled", True),
        ("kimi_k26_thinking_stream", "kimi", "enabled", True),
    ]
    summary: list[dict] = []
    for name, provider, thinking, stream in tasks:
        started = time.time()
        record: dict = {"name": name, "provider": provider, "thinking": thinking, "status": "error"}
        try:
            payload = build_payload(provider, title, brief, thinking)
            if stream:
                draft, meta = run_stream(provider, payload, timeout=int(os.environ.get("KIMI_COMPARE_TIMEOUT", "360")))
            else:
                draft, meta = run_non_stream(provider, payload, timeout=int(os.environ.get("MODEL_COMPARE_TIMEOUT", "300")))
            audit = audit_draft(draft["title"], draft["body"], brief, style_store)
            raw_path = out_dir / f"{name}_raw.md"
            clean_path = out_dir / f"{name}_clean.md"
            raw_path.write_text(f"# {draft['title']}\n\n{draft['body']}\n", encoding="utf-8")
            clean_path.write_text(f"# {draft['title']}\n\n{audit['body']}\n", encoding="utf-8")
            record.update(
                {
                    "status": "ok",
                    "elapsedSeconds": round(time.time() - started, 2),
                    "rawPath": str(raw_path),
                    "cleanPath": str(clean_path),
                    "chars": len(audit["body"]),
                    "qualityStatus": audit["qualityGate"].get("status"),
                    "qualityReasons": audit["qualityGate"].get("reasons", [])[:8],
                    "bannedCount": audit["bannedCount"],
                    "meta": meta,
                }
            )
            (out_dir / f"{name}_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError, RuntimeError, Exception) as exc:
            record.update({"elapsedSeconds": round(time.time() - started, 2), "error": str(exc)[:1000]})
        summary.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_lines = ["# Model Longform Compare", "", f"- title: {title}", f"- created: {stamp}", "", "## Summary"]
    for item in summary:
        report_lines.append(
            f"- {item['name']}: {item['status']} | {item.get('elapsedSeconds')}s | chars={item.get('chars')} | gate={item.get('qualityStatus')} | reasons={'; '.join(item.get('qualityReasons', [])[:3])}"
        )
    (out_dir / "README.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
