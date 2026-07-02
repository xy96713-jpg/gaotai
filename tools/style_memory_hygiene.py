#!/usr/bin/env python3
"""Audit style-memory quality without deleting anything."""

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

from tools.style_memory import StyleMemoryEntry, StyleMemoryStore, normalize_space_for_memory  # noqa: E402

REPORT_DIR = ROOT / ".cache" / "writing" / "style_memory_hygiene"


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def entry_payload(entry: StyleMemoryEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "kind": entry.kind,
        "strength": entry.strength,
        "sourceText": entry.source_text,
        "replacementText": entry.replacement_text,
        "reason": entry.reason,
        "tags": entry.tags,
        "usageCount": entry.usage_count,
        "createdAt": entry.created_at,
        "updatedAt": entry.updated_at,
    }


def too_abstract(entry: StyleMemoryEntry) -> bool:
    text = normalize_space_for_memory(" ".join([entry.source_text, entry.replacement_text, entry.reason]))
    if len(text) < 12:
        return True
    concrete = r"(原句|改成|比如|划选|Kimi|DeepSeek|Codex|前端|风格库|报告|数据|视频|按钮|具体|对象|动作|后果|材料|读者)"
    abstract = r"(更好|自然|高级|有质感|有节奏|不水|不抽象|像人话|成熟|好文章|舒服|顺一点)"
    return bool(re.search(abstract, text)) and not re.search(concrete, text)


def audit_store(store: StyleMemoryStore, *, stale_days: int = 45) -> dict[str, Any]:
    entries = store.list()
    groups: dict[tuple[str, str, str], list[StyleMemoryEntry]] = {}
    for entry in entries:
        key = (entry.kind, normalize_space_for_memory(entry.source_text), entry.scope)
        groups.setdefault(key, []).append(entry)

    duplicates = [
        {"reason": "same kind/source/scope appears more than once", "entries": [entry_payload(item) for item in items]}
        for items in groups.values()
        if len(items) > 1
    ]

    by_source_scope: dict[tuple[str, str], list[StyleMemoryEntry]] = {}
    for entry in entries:
        by_source_scope.setdefault((normalize_space_for_memory(entry.source_text), entry.scope), []).append(entry)
    conflicts = []
    for items in by_source_scope.values():
        kinds = {item.kind for item in items}
        if "approved_line" in kinds and "banned_line" in kinds:
            conflicts.append(
                {
                    "reason": "same line is both liked and disliked",
                    "entries": [entry_payload(item) for item in items],
                }
            )

    now = dt.datetime.now(dt.timezone.utc)
    stale = []
    for entry in entries:
        updated = parse_time(entry.updated_at) or parse_time(entry.created_at)
        if updated and entry.usage_count == 0 and (now - updated).days >= stale_days:
            stale.append({"reason": f"unused for at least {stale_days} days", "entry": entry_payload(entry)})

    abstract = [
        {"reason": "too abstract to guide generation reliably", "entry": entry_payload(entry)}
        for entry in entries
        if too_abstract(entry)
    ]

    recommendations = []
    if duplicates:
        recommendations.append("合并重复记忆，保留 reason 更具体、updatedAt 更新的那条。")
    if conflicts:
        recommendations.append("人工决定冲突项：同一句不能同时作为喜欢和讨厌。")
    if abstract:
        recommendations.append("把抽象偏好改成可执行规则：原句、问题、改法、为什么。")
    if stale:
        recommendations.append("长期未用记录先保留，但可以移到低优先级或人工删除。")
    if not recommendations:
        recommendations.append("风格库当前没有明显卫生问题。")

    status = "needs_cleanup" if duplicates or conflicts or abstract else "ok"
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "entryCount": len(entries),
        "duplicates": duplicates,
        "conflicts": conflicts,
        "stale": stale[:50],
        "abstract": abstract[:50],
        "recommendations": recommendations,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# 风格库卫生检查",
        "",
        f"- 状态：{result['status']}",
        f"- 记录数：{result['entryCount']}",
        f"- 重复：{len(result['duplicates'])}",
        f"- 冲突：{len(result['conflicts'])}",
        f"- 过期未用：{len(result['stale'])}",
        f"- 太抽象：{len(result['abstract'])}",
        "",
        "## 建议",
        "",
        *[f"- {item}" for item in result["recommendations"]],
    ]
    for key, title in (("conflicts", "冲突项"), ("duplicates", "重复项"), ("abstract", "太抽象项"), ("stale", "过期未用项")):
        items = result.get(key) or []
        if not items:
            continue
        lines.extend(["", f"## {title}", ""])
        for item in items[:12]:
            entries = item.get("entries") or [item.get("entry")]
            lines.append(f"- {item.get('reason', '')}")
            for entry in [entry for entry in entries if entry]:
                lines.append(f"  - `{entry.get('id')}` {entry.get('kind')} {entry.get('sourceText')}")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--stale-days", type=int, default=45)
    args = parser.parse_args()

    result = audit_store(StyleMemoryStore(), stale_days=args.stale_days)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / f"style_memory_hygiene_{now_slug()}.json"
    report_path = summary_path.with_suffix(".md")
    result["summaryPath"] = str(summary_path.resolve().relative_to(ROOT))
    result["reportPath"] = str(report_path.resolve().relative_to(ROOT))
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(build_report(result))
        print(f"\nreport: {result['reportPath']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
