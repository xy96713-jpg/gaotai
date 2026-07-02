#!/usr/bin/env python3
"""Check the Editorial Desk V2 evidence before serious draft delivery.

This is a structural preflight. It does not judge prose quality by itself.
It blocks the recurring failure where a complete-looking draft appears before
source, story, voice, opening, and first-section evidence exist.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRITING_CACHE = ROOT / ".cache" / "writing"
SOURCE_INGEST_CACHE = ROOT / ".cache" / "source-ingest"


@dataclass(frozen=True)
class DeskRule:
    desk: str
    key: str
    label: str
    patterns: tuple[str, ...]
    required: bool = True


DESK_RULES = [
    DeskRule(
        "Source Desk",
        "source_pack",
        "Source pack / reading notes",
        ("{slug}*source*pack*.md", "{slug}*reading*pack*.md", "{slug}*source*notes*.md"),
    ),
    DeskRule(
        "Source Desk",
        "close_reading",
        "Close reading / source language / rhetorical engine",
        (
            "{slug}*close*reading*.md",
            "{slug}*golden*excerpt*.md",
            "{slug}*source*language*.md",
            "{slug}*rhetorical*engine*.md",
        ),
    ),
    DeskRule(
        "Source Desk",
        "three_pass",
        "Writer three-pass reading",
        ("{slug}*three*pass*.md", "{slug}*writer*three*.md"),
    ),
    DeskRule(
        "Story Desk",
        "event_or_action_context",
        "Event / action / context card",
        (
            "{slug}*event*context*.md",
            "{slug}*action*chain*.md",
            "{slug}*fact*context*.md",
            "{slug}*context*gap*.md",
        ),
    ),
    DeskRule(
        "Story Desk",
        "article_engine",
        "Article engine / angle / lede-nut graf",
        (
            "{slug}*article*engine*.md",
            "{slug}*angle*pack*.md",
            "{slug}*direction*tree*.md",
            "{slug}*lede*nut*.md",
            "{slug}*nutgraf*.md",
        ),
    ),
    DeskRule(
        "Voice Desk",
        "mentor_or_style",
        "Mentor study / style reference / mature study",
        (
            "{slug}*style*reference*.md",
            "{slug}*mature*study*.md",
            "{slug}*voice*reference*.md",
            "{slug}*style*mimic*.md",
            "{slug}*structure*mimic*.md",
        ),
    ),
    DeskRule(
        "Voice Desk",
        "voice_memory",
        "Approved and rejected line memory",
        ("approved_lines_corpus.md", "bad_lines_corpus.md"),
    ),
    DeskRule(
        "Opening Desk",
        "opening_lab",
        "Opening pack / opening routes",
        ("{slug}*opening*pack*.md", "{slug}*opening*routes*.md", "{slug}*opening*gate*.md"),
    ),
    DeskRule(
        "Opening Desk",
        "wording_frames",
        "Wording frame set",
        ("{slug}*wording*frame*.md", "{slug}*expression*frame*.md"),
    ),
    DeskRule(
        "Prose Desk",
        "paragraph_jobs",
        "Paragraph job board / scene rhythm / beat board",
        (
            "{slug}*paragraph*job*.md",
            "{slug}*scene*rhythm*.md",
            "{slug}*rhythm*ladder*.md",
            "{slug}*beat*board*.md",
            "{slug}*section*beat*board*.md",
        ),
    ),
    DeskRule(
        "Prose Desk",
        "sample",
        "Sample or first-section draft",
        (
            "{slug}*sample*.md",
            "{slug}*first*section*.md",
            "{slug}*section*draft*.md",
            "{slug}*draft*sample*.md",
        ),
    ),
    DeskRule(
        "Prose Desk",
        "critique",
        "Hostile critique / reader test",
        (
            "{slug}*hostile*critique*.md",
            "{slug}*reader*critique*.md",
            "{slug}*reader*continuation*.md",
            "{slug}*critique*.md",
        ),
    ),
]


FULL_DRAFT_CHARS = 1200


def slug_aliases(slug: str) -> list[str]:
    aliases = [slug]
    hyphen = slug.replace("_", "-")
    compact = slug.replace("_", "")
    for alias in (hyphen, compact):
        if alias not in aliases:
            aliases.append(alias)
    return aliases


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def find_rule_matches(slug: str, rule: DeskRule, cache_dir: Path = WRITING_CACHE) -> list[Path]:
    matches: list[Path] = []
    search_dirs = [cache_dir]
    if rule.key == "source_pack":
        search_dirs.append(SOURCE_INGEST_CACHE)
        for alias in slug_aliases(slug):
            for folder_name in {alias, alias.replace("_", "-"), alias.replace("-", "_")}:
                candidate = SOURCE_INGEST_CACHE / folder_name / "source_pack.md"
                if candidate.is_file():
                    matches.append(candidate)

    for pattern in rule.patterns:
        if "{slug}" not in pattern:
            candidate = cache_dir / pattern
            if candidate.exists():
                matches.append(candidate)
            continue
        for alias in slug_aliases(slug):
            rendered = pattern.format(slug=alias)
            for directory in search_dirs:
                iterator = directory.rglob(rendered) if directory == SOURCE_INGEST_CACHE else directory.glob(rendered)
                matches.extend(path for path in iterator if path.is_file())

    unique = sorted(set(matches), key=lambda path: (-path.stat().st_mtime, str(path)))
    return unique


def collect_matches(slug: str, cache_dir: Path = WRITING_CACHE) -> dict[str, list[Path]]:
    return {rule.key: find_rule_matches(slug, rule, cache_dir) for rule in DESK_RULES}


def missing_rules(matches: dict[str, list[Path]]) -> list[DeskRule]:
    by_key = {rule.key: rule for rule in DESK_RULES}
    return [by_key[key] for key, paths in matches.items() if by_key[key].required and not paths]


def visible_text_len(draft: Path) -> int:
    if not draft.exists():
        return 0
    text = draft.read_text(encoding="utf-8", errors="replace")
    return len("".join(text.split()))


def build_report(slug: str, draft: Path, matches: dict[str, list[Path]], extra_failures: list[str]) -> tuple[str, bool]:
    missing = missing_rules(matches)
    blocked = bool(missing or extra_failures)
    decision = "BLOCK" if blocked else "ALLOW"

    lines: list[str] = []
    lines.append("# Editorial Desk V2 Preflight")
    lines.append("")
    lines.append(f"- Topic slug: `{slug}`")
    lines.append(f"- Draft: `{rel(draft)}`")
    lines.append(f"- Decision: **{decision}**")
    lines.append("")

    for desk in ["Source Desk", "Story Desk", "Voice Desk", "Opening Desk", "Prose Desk"]:
        lines.append(f"## {desk}")
        for rule in [rule for rule in DESK_RULES if rule.desk == desk]:
            paths = matches.get(rule.key, [])
            if paths:
                rendered = ", ".join(f"`{rel(path)}`" for path in paths[:3])
                lines.append(f"- PASS {rule.label}: {rendered}")
            else:
                lines.append(f"- FAIL {rule.label}: patterns `{', '.join(rule.patterns)}`")
        lines.append("")

    lines.append("## Extra Failures")
    if extra_failures:
        for failure in extra_failures:
            lines.append(f"- {failure}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Repair Route")
    if not blocked:
        lines.append("- Desk evidence exists. Continue to prose and mechanical gates.")
    else:
        for rule in missing:
            lines.append(f"- Repair {rule.desk}: create or mark unavailable `{rule.label}`.")
        for failure in extra_failures:
            lines.append(f"- Repair draft flow: {failure}")
    lines.append("")
    return "\n".join(lines), not blocked


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Editorial Desk V2 evidence for a serious writing run.")
    parser.add_argument("--topic-slug", required=True, help="Artifact slug, for example pope_ai.")
    parser.add_argument("--draft", required=True, help="Draft path to check.")
    parser.add_argument("--report", help="Optional report output path.")
    args = parser.parse_args()

    draft = resolve_path(args.draft)
    matches = collect_matches(args.topic_slug)
    extra_failures: list[str] = []

    if not draft.exists():
        extra_failures.append(f"draft missing: {rel(draft)}")
    elif visible_text_len(draft) > FULL_DRAFT_CHARS and not matches.get("sample"):
        extra_failures.append(
            f"draft is longer than {FULL_DRAFT_CHARS} non-space chars but no sample/first-section artifact exists"
        )

    report_text, allowed = build_report(args.topic_slug, draft, matches, extra_failures)
    if args.report:
        report = resolve_path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"RESULT: {'PASS' if allowed else 'FAIL'}")
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
