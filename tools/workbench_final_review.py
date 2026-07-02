#!/usr/bin/env python3
"""Run a local final-review pass for a workbench document."""

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

from tools.inline_editor_server import (  # noqa: E402
    ai_flavor_audit,
    build_style_invocation_proof,
    quality_gate_for_generated_body,
    quick_audit,
    taste_audit,
)
from tools.style_memory import StyleMemoryStore  # noqa: E402

DOCUMENT_ROOT = ROOT / ".cache" / "writing" / "documents"
REPORT_DIR = ROOT / ".cache" / "writing" / "final_reviews"


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def html_to_text(value: str) -> str:
    text = re.sub(r"<h[1-6][^>]*>", "\n\n", value)
    text = re.sub(r"</h[1-6]>", "\n\n", text)
    text = re.sub(r"<p[^>]*>", "\n\n", text)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_document(document_id: str) -> dict[str, str]:
    path = DOCUMENT_ROOT / f"{document_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"document not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    title = str(data.get("title") or document_id)
    text = str(data.get("content_text") or "").strip()
    if not text and data.get("content_html"):
        text = html_to_text(str(data.get("content_html") or ""))
    if text.startswith(title):
        body = text[len(title):].strip()
    else:
        body = text
    return {"title": title, "body": body, "path": str(path)}


def run_review(document_id: str, *, brief: str = "") -> dict[str, Any]:
    doc = load_document(document_id)
    store = StyleMemoryStore()
    title = doc["title"]
    body = doc["body"]
    review_brief = brief or f"正式交付前终审：{title}"
    quick = quick_audit(title, body, store)
    taste = taste_audit(title, body, store)
    flavor = ai_flavor_audit(title, body, store)
    proof = build_style_invocation_proof(title=title, body=body, brief=review_brief, style_store=store)
    gate = quality_gate_for_generated_body(
        body=body,
        title=title,
        brief=review_brief,
        material_card={"claim": title, "sources": "workbench document", "noInvent": "不能新增材料。"},
        minimal_edit={"auditAfter": {"findings": []}},
        personal_material_allowed=True,
    )
    blockers: list[str] = []
    if gate.get("status") != "allow":
        blockers.extend(str(item) for item in gate.get("reasons", [])[:8])
    if (proof.get("memoryCounts") or {}).get("currentBannedFindings", 0):
        blockers.append("风格库硬禁命中，必须修完再交付。")
    for item in taste.get("findings", []):
        if item.get("level") == "high":
            blockers.append(str(item.get("reason", "高优先级口味问题")))
    status = "allow_for_human_final" if not blockers else "blocked"
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "documentId": document_id,
        "documentPath": doc["path"],
        "title": title,
        "status": status,
        "blockers": blockers[:12],
        "quickAudit": quick,
        "tasteAudit": taste,
        "aiFlavor": flavor,
        "styleProof": {
            "status": proof.get("status"),
            "effectiveness": proof.get("effectiveness"),
            "memoryCounts": proof.get("memoryCounts"),
            "usedThisRun": (proof.get("memoryHits") or {}).get("usedThisRun", [])[:8],
        },
        "qualityGate": gate,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# 工作台正式交付前终审",
        "",
        f"- 文档：`{result['documentId']}`",
        f"- 标题：{result['title']}",
        f"- 状态：{result['status']}",
        f"- 快审：{result['quickAudit'].get('score')} / {result['quickAudit'].get('summary')}",
        f"- 口味审稿：{result['tasteAudit'].get('score')} / {result['tasteAudit'].get('summary')}",
        f"- AI味：{result['aiFlavor'].get('score')} / {result['aiFlavor'].get('summary')}",
        f"- 风格库：{result['styleProof'].get('effectiveness', {}).get('label')}",
        "",
        "## 阻断项",
        "",
    ]
    blockers = result.get("blockers") or []
    lines.extend([f"- {item}" for item in blockers] or ["- 无自动阻断项；仍需要人工通读。"])
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document-id", default="first_video_rewrite_final_20260616")
    parser.add_argument("--brief", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()

    result = run_review(args.document_id, brief=args.brief)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / f"{args.document_id}_{now_slug()}.json"
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
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
