#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_REPORT = ROOT / ".cache" / "writing" / "workbench_paragraph_assist_matrix_latest.json"
DEFAULT_MD_REPORT = ROOT / ".cache" / "writing" / "workbench_paragraph_assist_matrix_latest.md"


BAD_SURFACE_RE = re.compile(
    r"口语化表达|自然引出下一段|短句节奏适合口播|编辑思路|改写思路|"
    r"顺是顺了|人也散了|[“\"「]…{2,}[”\"」]|[\"“]一些套话|「套话」|"
    r"套话.{0,18}套话|套话格局|competitiveness|against whom|"
    r"concretize|oralize|source-ground|change-frame",
    re.I,
)

AI_SLOP_SIGNAL_RE = re.compile(
    r"积极拥抱|提升竞争力|提效|赋能|闭环|降本增效|未来已来|正在改变|行业进入新阶段|"
    r"稳稳.{0,4}接住|不绕弯|最直接|懂你|delve|tapestry|landscape|leverage|"
    r"套话|空话|水词|AI 味|AI味",
    re.I,
)


BASE_PAYLOAD = {
    "title": "这可能是目前 AI 写作最好的方式",
    "contextBefore": (
        "Hi，在 2026 的今天，让 AI 撰写文章、论文或者报告，已经是 AI 应用场景里再基础不过的事情。"
        "但真的用下来，文章里的 AI 味、不说人话、通篇抓不住重点，这些情况还是常常发生。"
    ),
    "previousParagraph": (
        "比如它会写：“AI 正在改变内容生产，创作者需要提升自身竞争力。”这句话很稳，也很空。"
        "谁在用 AI？提升哪一部分？读者看完要做什么？它都没有回答。"
    ),
    "nextParagraph": (
        "我后来去查了一圈 AI 写作相关的研究和工具，发现问题比几个词更深。"
        "模型生成文字时，会优先走常见、稳妥、可复用的表达。"
    ),
    "contextAfter": (
        "AI 味可以拆开看。表面像词的问题，往下看，是几种写作动作缺席："
        "没有具体对象，没有真实材料，没有取舍，没有作者自己的判断。"
    ),
}


CASES: list[dict[str, Any]] = [
    {
        "name": "ai_slop_examples",
        "promptText": "找一些很有代表的 ai 词语和句子，比如稳稳地接住你、不绕弯、最直接，调研后补一段。",
        "requiresResearch": True,
        "requiresExamples": 2,
        "requiresAny": ("提效", "赋能", "闭环", "稳稳", "不绕弯", "delve", "tapestry", "提升竞争力", "懂你"),
    },
    {
        "name": "plain_research_bridge",
        "promptText": "把 STORM、PaperDebugger、CoAuthor 这些研究用人话解释一下，不要像论文罗列，承接上下文补一段。",
        "requiresAny": ("先", "材料", "反对意见", "审稿", "退稿", "动笔"),
        "banned": ("Stanford STORM 先检索材料、多视角提问、生成大纲", "2025 年关于学术写作的综述"),
    },
    {
        "name": "reader_objection",
        "promptText": "这里补一段普通观众可能会反驳什么，为什么他们会觉得这套工作台太麻烦。",
        "requiresAny": (
            "麻烦",
            "为什么",
            "直接",
            "模型",
            "多一步",
            "多步骤",
            "流程",
            "有人",
            "提示词",
            "约束",
            "退回",
            "复杂",
            "多余",
            "自己写",
            "想关页面",
            "像开厂",
            "累得多",
        ),
    },
    {
        "name": "workbench_demo",
        "promptText": "补一段具体演示：坏句怎么划选、记为讨厌、进入风格库、下次生成前怎么被拦。",
        "requiresAny": ("划选", "讨厌", "风格库", "下次", "拦"),
    },
    {
        "name": "personal_judgment",
        "promptText": "这里补一段我的个人判断：为什么我不再相信直接让 AI 交全文，而是先让它过门槛。",
        "requiresAny": ("我", "直接", "全文", "门槛", "退"),
    },
    {
        "name": "definition_ai_taste",
        "promptText": "补一段解释 AI 味到底是什么，要有定义，但别抽象，要能听懂。",
        "requiresAny": ("对象", "主语", "动作", "后果", "具体", "判断", "听", "给谁看", "信息"),
    },
    {
        "name": "transition_to_frontend",
        "promptText": "补一段从写作原因转到我的前端工作台，说明为什么按钮要少、正文要一直可见。",
        "requiresAny": ("前端", "按钮", "正文", "可见", "少"),
    },
    {
        "name": "before_after_contrast",
        "promptText": "补一段用了和没用的对比，要落到一句话的变化，不要讲大道理。",
        "requiresExamples": 1,
        "requiresAny": ("原句", "改后", "这句", "变化", "对象", "第一版", "第二版", "上一句", "这一句", "前后", "主语", "后果"),
    },
    {
        "name": "boundary",
        "promptText": "补一段这套系统的边界：它不能替我做什么，哪些仍然要人判断。",
        "requiresAny": ("不能", "替", "判断", "材料", "选题", "拍板", "边界", "省不掉"),
    },
    {
        "name": "closing",
        "promptText": "补一个结尾段，不要金句，不要二段式反转，要收在这个工作台为什么会越来越像我的写作习惯。",
        "requiresAny": ("记录", "习惯", "下一次", "判断", "留下"),
        "banned": ("不是", "而是", "真正", "最后还是"),
    },
]


def request_json(base: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    data = None
    headers = {"content-type": "application/json"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body[:800]}") from exc


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def quoted_or_list_example_count(text: str) -> int:
    quoted = [
        item
        for item in re.findall(r"[“\"「](.{2,40}?)[”\"」]", text)
        if item.strip() and item.strip() not in {"套话", "……", "..."}
    ]
    list_blocks = re.findall(
        r"(?:比如|例如|如|常见|原句|改后|句子|表达|词|词语)[^。！？!?]{0,28}[：:][^。！？!?]{4,120}",
        text,
    )
    comma_count = 0
    for block in list_blocks:
        tail = re.split(r"[：:]", block, maxsplit=1)[-1]
        comma_count += len([part for part in re.split(r"[、,，；;]", tail) if normalize_space(part)])
    return len(quoted) + min(comma_count, 8)


def variant_quality_issues(case: dict[str, Any], response: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    variants = response.get("variants", [])
    if len(variants) < 3:
        issues.append(f"candidate_count:{len(variants)}")
    if case.get("requiresResearch") and not response.get("researchUsed"):
        issues.append("research_not_used")
    for index, item in enumerate(variants[:3], 1):
        text = normalize_space(str(item.get("text", "")))
        if len(text) < 36:
            issues.append(f"v{index}:too_short")
        if BAD_SURFACE_RE.search(text):
            issues.append(f"v{index}:bad_surface")
        for banned in case.get("banned", ()):
            if banned and banned in text:
                issues.append(f"v{index}:banned:{banned[:16]}")
        required_examples = int(case.get("requiresExamples", 0) or 0)
        if required_examples and quoted_or_list_example_count(text) < required_examples:
            issues.append(f"v{index}:missing_examples")
        required_any = tuple(case.get("requiresAny", ()))
        if required_any and not any(marker in text for marker in required_any):
            issues.append(f"v{index}:missing_required_signal")
        if case["name"] == "ai_slop_examples" and not AI_SLOP_SIGNAL_RE.search(text):
            issues.append(f"v{index}:missing_ai_slop_signal")
    return issues


def run_case(base: str, case: dict[str, Any]) -> dict[str, Any]:
    payload = {**BASE_PAYLOAD, "promptText": case["promptText"]}
    started = time.time()
    try:
        response = request_json(base, "/api/paragraph-assist", payload, timeout=150)
        issues = variant_quality_issues(case, response)
        return {
            "name": case["name"],
            "ok": not issues,
            "ms": round((time.time() - started) * 1000),
            "issues": issues,
            "engine": response.get("engine"),
            "researchUsed": response.get("researchUsed"),
            "researchHits": response.get("researchHits"),
            "researchQuery": response.get("researchQuery"),
            "variants": [
                {
                    "label": item.get("label"),
                    "text": str(item.get("text", "")).strip(),
                }
                for item in response.get("variants", [])[:3]
            ],
        }
    except Exception as exc:  # noqa: BLE001 - matrix report should capture all failures
        return {
            "name": case["name"],
            "ok": False,
            "ms": round((time.time() - started) * 1000),
            "issues": [str(exc)],
            "variants": [],
        }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Workbench Paragraph Assist Matrix",
        "",
        f"- generatedAt: `{summary['generatedAt']}`",
        f"- base: `{summary['base']}`",
        f"- status: `{'PASS' if summary['ok'] else 'FAIL'}`",
        f"- cases: `{summary['passed']}/{summary['total']}`",
        "",
        "## Cases",
        "",
    ]
    for item in summary["results"]:
        status = "PASS" if item["ok"] else "FAIL"
        lines.extend(
            [
                f"### {item['name']} - {status}",
                "",
                f"- engine: `{item.get('engine', '')}`",
                f"- research: `{item.get('researchUsed')}` / hits `{item.get('researchHits')}`",
            ]
        )
        if item.get("issues"):
            lines.append(f"- issues: `{', '.join(item['issues'])}`")
        for index, variant in enumerate(item.get("variants", [])[:3], 1):
            text = normalize_space(str(variant.get("text", "")))
            lines.append(f"- v{index} {variant.get('label') or ''}: {text[:220]}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def run(base: str, json_report: Path, md_report: Path, max_cases: int | None = None) -> dict[str, Any]:
    cases = CASES[:max_cases] if max_cases else CASES
    results = []
    for case in cases:
        item = run_case(base, case)
        print(json.dumps({k: v for k, v in item.items() if k != "variants"}, ensure_ascii=False))
        results.append(item)
    passed = len([item for item in results if item["ok"]])
    summary = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": passed == len(results),
        "base": base,
        "total": len(results),
        "passed": passed,
        "results": results,
    }
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_report.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Pressure-test paragraph assist prompts across writing needs.")
    parser.add_argument("--base", default="http://127.0.0.1:8766")
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()

    summary = run(args.base.rstrip("/"), args.json_report, args.md_report, args.max_cases)
    print(json.dumps({"ok": summary["ok"], "passed": summary["passed"], "total": summary["total"], "json": str(args.json_report), "md": str(args.md_report)}, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
