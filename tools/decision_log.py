#!/usr/bin/env python3
"""Build a decision log for a source-based article workflow."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRITING_CACHE = ROOT / ".cache" / "writing"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def read(path: Path | None) -> str:
    if path and path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def first_content_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def latest(slug: str, patterns: tuple[str, ...]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(WRITING_CACHE.glob(pattern.format(slug=slug)))
    matches = [path for path in matches if path.is_file()]
    if not matches:
        return None
    return sorted(matches, key=lambda p: (p.stat().st_mtime, str(p)), reverse=True)[0]


def matching_lines(text: str, keywords: tuple[str, ...], limit: int = 6) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip(" -\t")
        if not line:
            continue
        if any(keyword.lower() in line.lower() for keyword in keywords):
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def extract_bad_lines(text: str, limit: int = 12) -> list[str]:
    hits: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- Bad:"):
            phrase = stripped.removeprefix("- Bad:").strip()
            if phrase:
                hits.append(phrase)
        if len(hits) >= limit:
            break
    return hits


def extract_title(draft_text: str) -> str:
    for line in draft_text.splitlines():
        stripped = line.strip("# \t")
        if stripped:
            return stripped
    return "Untitled"


def extract_personal_layer(draft_text: str) -> list[str]:
    return matching_lines(draft_text, ("对我", "我还是会用", "我的工作流", "AI 可以帮我", "原文要自己读"), limit=6)


def build_decision_log(
    *,
    slug: str,
    draft: Path,
    angle_pack: Path | None = None,
    flow_card: Path | None = None,
    quality_report: Path | None = None,
    bad_lines_corpus: Path | None = None,
) -> str:
    draft_text = read(draft)
    angle_text = read(angle_pack)
    flow_text = read(flow_card)
    report_text = read(quality_report)
    bad_text = read(bad_lines_corpus)

    title = extract_title(draft_text)
    route_lines = matching_lines(angle_text + "\n" + flow_text, ("selected route", "editorial pick", "primary route", "route:"), limit=8)
    cut_lines = matching_lines(angle_text + "\n" + flow_text, ("cut", "discard", "losing", "not the route", "不用", "不要"), limit=8)
    boundary_lines = matching_lines(flow_text + "\n" + draft_text, ("boundary", "ending", "负责", "回答", "为什么", "judgment"), limit=8)
    personal_lines = extract_personal_layer(draft_text)
    report_lines = matching_lines(report_text, ("Decision:", "Source pack", "Angle pack", "Scene / rhythm", "writing_quality_gate"), limit=8)
    bad_lines = extract_bad_lines(bad_text)

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "# Article Decision Log",
        "",
        f"- Generated: {now}",
        f"- Topic slug: `{slug}`",
        f"- Draft: `{rel(draft)}`",
        f"- Title / hook: {title}",
        "",
        "## Locked Decisions",
        f"- Title/hook stays: {title}",
    ]

    if route_lines:
        lines.append("- Selected route / article engine:")
        lines.extend(f"  - {line}" for line in route_lines)
    else:
        lines.append("- Selected route / article engine: _not found in current artifacts_")

    if boundary_lines:
        lines.append("- Boundary / ending logic:")
        lines.extend(f"  - {line}" for line in boundary_lines)

    if personal_lines:
        lines.append("- Personal-IP layer:")
        lines.extend(f"  - {line}" for line in personal_lines)

    lines.extend(["", "## Cut / Avoid"])
    if cut_lines:
        lines.extend(f"- {line}" for line in cut_lines)
    if bad_lines:
        lines.append("- Known rejected lines/patterns:")
        lines.extend(f"  - {line}" for line in bad_lines)
    if not cut_lines and not bad_lines:
        lines.append("- _No cut or bad-line evidence found._")

    lines.extend(["", "## Gate Evidence"])
    if report_lines:
        lines.extend(f"- {line}" for line in report_lines)
    else:
        lines.append("- _No quality report linked yet._")

    lines.extend(
        [
            "",
            "## Open Risks",
            "- This log records editorial decisions; it does not prove source accuracy by itself.",
            "- If the title, route, or personal judgment changes, regenerate this file before drafting further.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--angle-pack")
    parser.add_argument("--flow-card")
    parser.add_argument("--quality-report")
    parser.add_argument("--bad-lines-corpus", default=str(WRITING_CACHE / "bad_lines_corpus.md"))
    parser.add_argument("--output")
    args = parser.parse_args()

    draft = resolve(args.draft)
    angle_pack = resolve(args.angle_pack) if args.angle_pack else latest(args.topic_slug, ("{slug}*angle*pack*.md", "{slug}*direction*tree*.md"))
    flow_card = resolve(args.flow_card) if args.flow_card else latest(args.topic_slug, ("{slug}*english*logic*flow*.md", "{slug}*argument*skeleton*.md"))
    quality_report = resolve(args.quality_report) if args.quality_report else latest(args.topic_slug, ("{slug}*sop*quality*report*.md",))
    bad_lines = resolve(args.bad_lines_corpus) if args.bad_lines_corpus else None
    output = resolve(args.output) if args.output else WRITING_CACHE / f"{args.topic_slug}_decision_log_latest.md"

    if not draft.exists():
        print(f"FAIL: draft missing: {rel(draft)}")
        return 1

    text = build_decision_log(
        slug=args.topic_slug,
        draft=draft,
        angle_pack=angle_pack,
        flow_card=flow_card,
        quality_report=quality_report,
        bad_lines_corpus=bad_lines,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"Wrote: {rel(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

