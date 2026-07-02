#!/usr/bin/env python3
"""Build the formal writing handoff artifacts for the workbench.

The workbench UI is intentionally light. Serious writing runs need a backend
handoff instead of more frontend buttons: source_pack.md, kimi_brief.md, and
gate_report.md. This script creates those files from a saved workbench topic
without calling any model or mutating the draft.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.style_memory import StyleMemoryEntry, StyleMemoryStore, normalize_space_for_memory
from tools.workbench_topic_context import build_context, load_records


FORMAL_RUN_DIR = ROOT / ".cache" / "writing" / "formal_runs"
DEFAULT_DOCUMENT_ID = "first_video_concise_strengthened_20260617"

HARD_BANS = [
    "不是...而是...",
    "而不是",
    "不只是...更是...",
    "真正的问题",
    "真正的关键",
    "这说明",
    "这意味着",
    "随着...发展",
    "深刻变化",
    "重塑",
    "底层逻辑",
    "赋能",
]

WORKBENCH_LAYER_SCAN = [
    ("failure_scene", "写作失败现场", ("废稿", "AI 味", "不说人话", "抓不住重点", "不能直接用")),
    ("cause_research", "原因/主流解法", ("研究", "材料", "反对意见", "先找材料", "先定")),
    ("workbench_action_chain", "工作台动作链", ("工作台", "Codex", "Kimi", "DeepSeek", "改句")),
    ("style_memory", "风格记忆", ("喜欢", "讨厌", "风格库", "记录")),
    ("before_after_proof", "前后对比证明", ("原句", "改后", "比如", "候选", "提升竞争力")),
    ("boundary", "边界", ("边界", "不能替", "不能保证", "仍然要人")),
]

EVENT_LAYER_SCAN = [
    ("event_chain", "事件/行动链", ("财报", "投入", "价格", "开源", "成本", "付费")),
    ("why_now", "为什么现在", ("现在", "开始", "过去", "这两年", "最近")),
    ("conflict_cost", "冲突/代价", ("成本", "利润", "现金流", "价格战", "续费", "capex")),
    ("evidence_chain", "证据链", ("Stanford", "NVIDIA", "Microsoft", "Alphabet", "DeepSeek", "阿里", "百度", "字节")),
    ("author_judgment", "作者判断", ("我", "判断", "更准确", "不能写成", "要看")),
    ("next_watch", "后续观察", ("接下来", "观察", "信号", "续费", "推理成本", "工作流")),
]

WORKBENCH_TOPIC_MARKERS = ("写作工作台", "AI 写作", "AI写作", "风格库", "改句")
WORKBENCH_SPECIFIC_MARKERS = (
    "写作工作台",
    "AI写作最佳方式",
    "AI 写作最佳方式",
    "locked-opening",
    "frontend-workbench",
    "author-led",
)


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def slugify(value: str, fallback: str = "formal_topic") -> str:
    normalized = re.sub(r"\s+", "_", value.strip())
    normalized = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_-")
    return normalized[:80] or fallback


def normalize_line(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def is_workbench_topic(title: str, body: str = "") -> bool:
    text = f"{title}\n{body}"
    return any(marker in text for marker in WORKBENCH_TOPIC_MARKERS)


def route_profile(title: str, body: str = "") -> dict[str, Any]:
    if is_workbench_topic(title, body):
        return {
            "key": "workbench_method",
            "label": "方法/SOP/工作台",
            "layer_scan": WORKBENCH_LAYER_SCAN,
            "movement": [
                "先写失败现场：为什么直接 AI 写出来不能用。",
                "再写原因/研究：模型为什么容易给安全、常见、可复用的句子。",
                "再写主流解法：材料、角度、反对意见、批判、风格记忆。",
                "再写工作台动作链：全文编辑、选句改、记喜欢/讨厌、补段、收稿检查、导出/演示。",
                "必须给 before/after：坏句、被拦原因、改后为什么能留下。",
                "最后写边界：它减少返工，不替人选题和判断。",
            ],
        }
    return {
        "key": "event_hot_analysis",
        "label": "事件/热点分析",
        "layer_scan": EVENT_LAYER_SCAN,
        "movement": [
            "从一个具体市场反差进入：模型还在变强，但钱开始问回报。",
            "交代行动链：大科技持续投入算力/数据中心，模型厂商降价或开源，投资者和客户开始追问利润。",
            "解释为什么是现在：capex、估值、推理成本、企业续费和价格战同时被摆上桌面。",
            "分两层写：美股看投入回报和估值压力，国内看开源、价格战、云生态和应用付费。",
            "补普通使用者视角：模型越来越便宜不等于公司有护城河，关键看工作流粘性。",
            "结尾给后续观察：单位推理成本、企业续费、具体业务流留存。",
        ],
    }


def find_document(document_id: str = "") -> dict[str, Any]:
    records = load_records()
    if document_id:
        for record in records:
            if str(record.get("_documentId") or record.get("document_id") or "") == document_id:
                return record
        raise FileNotFoundError(f"document not found: {document_id}")
    for record in records:
        if str(record.get("_documentId") or record.get("document_id") or "") == DEFAULT_DOCUMENT_ID:
            return record
    if not records:
        raise FileNotFoundError("no saved workbench documents found")
    return records[0]


def read_source_ref(source: str) -> dict[str, str]:
    source = source.strip()
    if not source:
        return {"kind": "empty", "ref": "", "title": "", "excerpt": "", "status": "empty"}
    if re.match(r"https?://", source):
        return {
            "kind": "url",
            "ref": source,
            "title": source,
            "excerpt": "",
            "status": "referenced_only_not_ingested",
        }
    path = Path(source).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    if not path.exists() or not path.is_file():
        return {
            "kind": "file",
            "ref": str(path),
            "title": path.name,
            "excerpt": "",
            "status": "missing",
        }
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {
            "kind": "file",
            "ref": str(path),
            "title": path.name,
            "excerpt": "",
            "status": f"read_error:{type(exc).__name__}",
        }
    excerpt = text.strip()
    if len(excerpt) > 2400:
        excerpt = excerpt[:2400].rstrip() + "\n\n[excerpt truncated]"
    return {
        "kind": "file",
        "ref": str(path),
        "title": path.name,
        "excerpt": excerpt,
        "status": "ingested_excerpt",
    }


def memory_entry_line(entry: StyleMemoryEntry) -> str:
    source = normalize_space_for_memory(entry.source_text)
    replacement = normalize_space_for_memory(entry.replacement_text)
    reason = normalize_space_for_memory(entry.reason)
    tags = " / ".join(entry.tags)
    body = source
    if replacement:
        body += f" -> {replacement}"
    notes = "；".join(item for item in (reason, tags) if item)
    if notes:
        body += f"（{notes}）"
    return body


def relevant_style_card(
    style_store: StyleMemoryStore,
    topic: str,
    limit: int = 16,
    *,
    workbench_topic: bool = False,
) -> dict[str, Any]:
    entries = style_store.search(topic, limit=limit)
    if not workbench_topic:
        entries = [
            entry
            for entry in entries
            if not any(
                marker in "\n".join([entry.source_text, entry.replacement_text, entry.reason, " ".join(entry.tags)])
                for marker in WORKBENCH_SPECIFIC_MARKERS
            )
        ]
    hard = [entry for entry in entries if entry.kind == "banned_line" or entry.strength == "hard"]
    good = [entry for entry in entries if entry.kind == "approved_line"]
    pairs = [entry for entry in entries if entry.kind == "rewrite_pair"]
    rules = [entry for entry in entries if entry.kind == "rule"]
    return {
        "count": len(entries),
        "hard_bans": [memory_entry_line(entry) for entry in hard[:8]],
        "approved": [memory_entry_line(entry) for entry in good[:5]],
        "rewrite_pairs": [memory_entry_line(entry) for entry in pairs[:5]],
        "rules": [memory_entry_line(entry) for entry in rules[:5]],
    }


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def layer_status(body: str, *, route: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for key, label, needles in route["layer_scan"]:
        ok = contains_any(body, needles)
        result.append(
            {
                "key": key,
                "label": label,
                "status": "pass" if ok else "missing",
                "evidence": " / ".join(needle for needle in needles if needle in body)[:120],
            }
        )
    return result


def hard_ban_hits(text: str) -> list[str]:
    hits: list[str] = []
    for item in HARD_BANS:
        if "..." in item:
            left, right = item.split("...", 1)
            if left in text and right in text:
                hits.append(item)
        elif item in text:
            hits.append(item)
    return hits


def build_source_pack(*, context: dict[str, Any], body: str, source_refs: list[dict[str, str]]) -> str:
    fields = context.get("fields") or {}
    lines = [
        f"# Source Pack: {context['title']}",
        "",
        "## Topic Metadata",
        f"- documentId: `{context['documentId']}`",
        f"- title: {context['title']}",
        f"- updatedAt: {context.get('updatedAt') or 'unknown'}",
        f"- workbenchDocument: {context.get('path') or 'unknown'}",
        "",
        "## Current Workbench Draft / Notes",
        body.strip() or "（当前主题没有正文。）",
        "",
        "## Structured Fields From Draft",
    ]
    if fields:
        lines.extend(f"- {key}: {value or '（未填）'}" for key, value in fields.items())
    else:
        lines.append("- （未发现结构化写作字段。）")
    lines.extend(["", "## Ingested / Referenced Sources"])
    if source_refs:
        for index, source in enumerate(source_refs, 1):
            lines.extend(
                [
                    f"### Source {index}: {source['title'] or source['ref']}",
                    f"- kind: {source['kind']}",
                    f"- status: {source['status']}",
                    f"- ref: {source['ref']}",
                ]
            )
            if source.get("excerpt"):
                lines.extend(["", source["excerpt"].strip()])
    else:
        lines.append("- 暂无外部资料已导入。本 source pack 只包含当前工作台正文；正式写作前仍需补资料或搜索。")
    lines.extend(
        [
            "",
            "## Evidence Boundaries",
            "- 当前文件不能把未导入资料当成已验证事实。",
            "- 如果主题涉及“今天 / 最新 / 主流 / 股价 / 公司 / 模型厂商”，下一步必须先补最新来源和讨论热度。",
            "- 评论、论坛和社媒只能提供读者压力，不能当事实证明。",
            "",
            "## Research Questions For Codex",
            "- 这篇文章的真实事件链或操作链是什么？",
            "- 读者第一反应会反驳什么？",
            "- 哪些句子只是顺口但没有对象、动作、后果？",
            "- 哪个例子能证明工作流真的减少返工？",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_kimi_brief(
    *,
    context: dict[str, Any],
    style_card: dict[str, Any],
    source_pack_path: Path,
    route: dict[str, Any],
) -> str:
    title = context["title"]
    fields = context.get("fields") or {}
    lines = [
        f"# Kimi Brief: {title}",
        "",
        "## Model Route",
        "- 主笔模型：Kimi thinking。",
        "- Codex 已整理 source_pack；Kimi 只负责根据 brief 写正文，不发明事实。",
        "- DeepSeek 只做后续局部改句/补句，不接管全文。",
        "",
        "## Source Pack",
        f"- {source_pack_path}",
        "",
        "## Writing Task",
        f"- 标题/主题：{title}",
        f"- 这篇想讲：{fields.get('这篇想讲') or '从当前正文和 source pack 中提炼，不要另起主题。'}",
        f"- 我的判断：{fields.get('我的判断') or '必须从材料和工作流动作中落地，不写泛泛总结。'}",
        f"- 已有材料/例子：{fields.get('已有材料/例子') or '优先使用 source_pack 中已明确的例子；没有就标记缺口。'}",
        f"- 不想写成：{fields.get('不想写成') or '不要写成产品说明书、泛 AI 技巧、报告腔。'}",
        f"- 文章路由：{route['label']}",
        "- 正文字数建议：900-1300 字；可以短，但必须完成所有 paragraph jobs。",
        "",
        "## Required Movement",
    ]
    lines.extend(f"{index}. {item}" for index, item in enumerate(route["movement"], 1))
    lines.extend(["", "## Hard Bans"])
    lines.extend(f"- {item}" for item in HARD_BANS)
    lines.extend(["", "## Style Memory To Apply"])
    if style_card["count"]:
        lines.append(f"- matched entries: {style_card['count']}")
        for label, items in (
            ("必须避开", style_card["hard_bans"]),
            ("可以借用", style_card["approved"]),
            ("有效改法", style_card["rewrite_pairs"]),
            ("额外规则", style_card["rules"]),
        ):
            lines.append(f"### {label}")
            lines.extend(f"- {item}" for item in items) if items else lines.append("- 暂无。")
    else:
        lines.append("- 暂无命中的风格记忆。Kimi 必须优先遵守 hard bans 和 paragraph jobs。")
    lines.extend(
        [
            "",
            "## Output Contract",
            "- 只输出正文，不输出编辑说明、镜头、B-roll、括号里的导演提示。",
            "- 不要解释你怎么写；直接写文章。",
            "- 如果 source_pack 没有资料，不要补编造事实；用当前稿件里的个人经验和工作流动作写。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_gate_report(
    *,
    context: dict[str, Any],
    body: str,
    source_refs: list[dict[str, str]],
    style_card: dict[str, Any],
    paths: dict[str, Path],
    route: dict[str, Any],
) -> tuple[str, str, list[str]]:
    layers = layer_status(body, route=route)
    missing_layers = [item for item in layers if item["status"] != "pass"]
    bans = hard_ban_hits(body)
    source_ready = any(item["status"] == "ingested_excerpt" for item in source_refs)
    title_ready = bool(normalize_line(context.get("title")))
    body_ready = len(normalize_line(body)) >= 80
    warnings: list[str] = []
    if not source_ready:
        warnings.append("暂无已导入外部资料；如主题依赖最新事实，必须先研究。")
    if bans:
        warnings.append("当前稿命中硬禁表达，Kimi brief 已列入避让。")
    if missing_layers:
        warnings.append("当前稿缺少部分正式写作层，Kimi brief 已要求补齐。")
    if not style_card["count"]:
        warnings.append("本主题未命中风格库，先按通用 hard bans 执行。")

    if not title_ready or not body_ready:
        status = "BLOCKED_NEEDS_TOPIC"
    elif source_ready:
        status = "READY_FOR_KIMI"
    else:
        status = "NEEDS_RESEARCH_OR_LAYER_REPAIR"

    lines = [
        f"# Gate Report: {context['title']}",
        "",
        f"- status: `{status}`",
        f"- documentId: `{context['documentId']}`",
        f"- source_pack: `{paths['source_pack']}`",
        f"- kimi_brief: `{paths['kimi_brief']}`",
        f"- route: {route['label']}",
        "",
        "## Gate Checklist",
        f"- title present: {'pass' if title_ready else 'missing'}",
        f"- draft/body material: {'pass' if body_ready else 'missing'}",
        f"- ingested external source: {'pass' if source_ready else 'missing'}",
        f"- style memory matched: {'pass' if style_card['count'] else 'missing'}",
        "",
        "## Required Layer Scan",
    ]
    for item in layers:
        evidence = f" — {item['evidence']}" if item["evidence"] else ""
        lines.append(f"- {item['label']}: {item['status']}{evidence}")
    lines.extend(["", "## Hard Ban Hits"])
    lines.extend(f"- {item}" for item in bans) if bans else lines.append("- none")
    lines.extend(["", "## Warnings / Next Action"])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- 可以进入 Kimi thinking 主笔。")
    return "\n".join(lines).rstrip() + "\n", status, warnings


def generate_artifacts(
    *,
    record: dict[str, Any],
    out_dir: Path,
    source_inputs: list[str],
    style_store: StyleMemoryStore,
) -> dict[str, Any]:
    context = build_context(record)
    body = str(record.get("content_text") or "").strip()
    topic_query = " ".join([context["title"], body[:500]])
    source_refs = [read_source_ref(item) for item in source_inputs if item.strip()]
    route = route_profile(context["title"], body)
    style_card = relevant_style_card(
        style_store,
        topic_query,
        workbench_topic=route["key"] == "workbench_method",
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "source_pack": out_dir / "source_pack.md",
        "kimi_brief": out_dir / "kimi_brief.md",
        "gate_report": out_dir / "gate_report.md",
        "manifest": out_dir / "manifest.json",
    }
    source_pack = build_source_pack(context=context, body=body, source_refs=source_refs)
    paths["source_pack"].write_text(source_pack, encoding="utf-8")
    kimi_brief = build_kimi_brief(
        context=context,
        style_card=style_card,
        source_pack_path=paths["source_pack"],
        route=route,
    )
    paths["kimi_brief"].write_text(kimi_brief, encoding="utf-8")
    gate_report, status, warnings = build_gate_report(
        context=context,
        body=body,
        source_refs=source_refs,
        style_card=style_card,
        paths=paths,
        route=route,
    )
    paths["gate_report"].write_text(gate_report, encoding="utf-8")
    manifest = {
        "status": status,
        "documentId": context["documentId"],
        "title": context["title"],
        "createdAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "warnings": warnings,
        "paths": {key: str(value) for key, value in paths.items()},
        "sourceCount": len(source_refs),
        "styleMemoryCount": style_card["count"],
        "route": route["key"],
        "routeLabel": route["label"],
    }
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document-id", default="", help="Workbench documentId. Defaults to the core formal draft or latest saved document.")
    parser.add_argument("--source", action="append", default=[], help="Local source file or URL reference. Repeatable.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory. Defaults to .cache/writing/formal_runs/<timestamp>_<slug>.")
    parser.add_argument("--json", action="store_true", help="Print manifest JSON only.")
    args = parser.parse_args()

    record = find_document(args.document_id)
    document_id = str(record.get("_documentId") or record.get("document_id") or "")
    title = normalize_line(record.get("title"))
    slug = slugify(document_id or title)
    out_dir = args.out_dir or FORMAL_RUN_DIR / f"{now_stamp()}_{slug}"
    manifest = generate_artifacts(
        record=record,
        out_dir=out_dir,
        source_inputs=args.source,
        style_store=StyleMemoryStore(),
    )
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"status: {manifest['status']}")
        print(f"source_pack: {manifest['paths']['source_pack']}")
        print(f"kimi_brief: {manifest['paths']['kimi_brief']}")
        print(f"gate_report: {manifest['paths']['gate_report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
