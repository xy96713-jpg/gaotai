#!/usr/bin/env python3
"""Run the full article SOP and write a delivery contract manifest.

This wrapper exists to make the delivery rule unambiguous:

- `run_article_sop.py` is the complete gate controller.
- A serious article is deliverable only when this wrapper records `ALLOW`.
- Frontend `/api/full-draft` output is a controlled draft, not full SOP.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRITING_CACHE = ROOT / ".cache" / "writing"


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_report_path(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("Report: "):
            return line.removeprefix("Report: ").strip()
    return ""


def run_contract(topic_slug: str, draft: Path, report: Path | None = None) -> dict[str, object]:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_article_sop.py"),
        "--topic-slug",
        topic_slug,
        "--draft",
        str(draft),
    ]
    if report is not None:
        command.extend(["--report", str(report)])
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    combined_output = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
    decision = "ALLOW" if proc.returncode == 0 else "BLOCK"
    report_text = parse_report_path(proc.stdout) or (rel(report) if report else "")
    manifest = {
        "topicSlug": topic_slug,
        "draft": rel(draft),
        "decision": decision,
        "deliverable": decision == "ALLOW",
        "fullSop": True,
        "report": report_text,
        "controller": "tools/run_article_sop.py",
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    manifest_path = WRITING_CACHE / f"{topic_slug}_delivery_contract_latest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Decision: {decision}")
    print(f"Deliverable: {str(decision == 'ALLOW').lower()}")
    print(f"Report: {report_text}")
    print(f"Manifest: {rel(manifest_path)}")
    if combined_output:
        print("")
        print(combined_output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full SOP and write a delivery contract manifest.")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    draft = resolve_path(args.draft)
    report = resolve_path(args.report) if args.report else None
    manifest = run_contract(args.topic_slug, draft, report)
    return 0 if manifest["deliverable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
