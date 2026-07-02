#!/usr/bin/env python3
"""Preflight manifest for serious Chinese source-based writing.

This is a hard "did we actually run the workflow?" check. It does not certify
that prose is good. It blocks visible drafts when required prep artifacts are
missing or when known bad frames appear in the draft.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRITING_CACHE = ROOT / ".cache" / "writing"
SOURCE_INGEST_CACHE = ROOT / ".cache" / "source-ingest"


@dataclass(frozen=True)
class ArtifactRule:
    name: str
    patterns: tuple[str, ...]
    required: bool = True


BASE_RULES = [
    ArtifactRule("source_or_reading_notes", ("{slug}*source*pack*.md", "{slug}*source*notes*.md", "{slug}*reading*evidence*.md", "{slug}*reading*pack*.md")),
    ArtifactRule("event_context", ("{slug}*event*context*.md", "{slug}*fact*context*.md")),
    ArtifactRule("source_language_or_rhetorical_engine", ("{slug}*source*language*.md", "{slug}*rhetorical*engine*.md", "{slug}*close*reading*.md")),
    ArtifactRule("close_reading_golden_excerpts", ("{slug}*close*reading*.md", "{slug}*golden*excerpt*.md")),
    ArtifactRule("writer_three_pass", ("{slug}*three*pass*.md", "{slug}*writer*three*.md")),
    ArtifactRule("reporter_notebook", ("{slug}*reporter*notebook*.md",)),
    ArtifactRule("comment_pressure_or_gap", ("{slug}*comment*pressure*.md", "{slug}*public*discussion*.md", "{slug}*comment*gap*.md")),
    ArtifactRule("style_reference", ("{slug}*style*reference*.md", "{slug}*voice*reference*.md", "{slug}*mature*study*.md")),
    ArtifactRule("speaker_motive", ("{slug}*speaker*motive*.md",)),
    ArtifactRule("direction_tree_or_angle_pack", ("{slug}*direction*tree*.md", "{slug}*angle*pack*.md", "{slug}*opening*routes*.md")),
    ArtifactRule("lede_nutgraf", ("{slug}*lede*nut*.md", "{slug}*nutgraf*.md")),
    ArtifactRule("chinese_article_route", ("{slug}*chinese*style*route*.md", "{slug}*article*route*.md")),
    ArtifactRule("paragraph_job_board", ("{slug}*paragraph*job*.md", "{slug}*beat*board*.md")),
    ArtifactRule("wording_frame_set", ("{slug}*wording*frame*.md", "{slug}*expression*frame*.md")),
    ArtifactRule("opening_gate", ("{slug}*opening*gate*.md", "{slug}*opening*pack*.md")),
    ArtifactRule("sample_or_section_draft", ("{slug}*sample*.md", "{slug}*draft*.md")),
    ArtifactRule("hostile_critique_or_reader_test", ("{slug}*hostile*critique*.md", "{slug}*reader*continuation*.md", "{slug}*critique*.md")),
]


FALLBACK_BAD_PATTERNS = [
    r"我读了",
    r"我看了",
    r"我发现",
    r"最近看到",
    r"值得注意的是",
    r"这意味着",
    r"真正的问题",
    r"真正有意思的是",
    r"最吓人",
    r"最可怕",
    r"最危险",
    r"原文转向",
    r"原文提到",
    r"文章指出",
    r"画面换了",
    r"镜头一转",
    r"不只是.*更是",
    r"真正.+不是.+而是",
    r"问题.+不是.+而是",
]


def import_quality_gate_patterns() -> tuple[list[str], list[str]]:
    try:
        sys.path.insert(0, str(ROOT))
        from tools import writing_quality_gate as gate  # type: ignore

        patterns: list[str] = []
        patterns.extend(getattr(gate, "HARD_BAD_PATTERNS", []))
        patterns.extend(
            pattern
            for _, pattern in getattr(gate, "AI_TELL_PATTERNS_ZH", [])
            if pattern not in {"不是.*而是", "不只是.*而是", "不仅.*而且"}
        )
        patterns.extend(getattr(gate, "SOURCE_NAVIGATION_PATTERNS", []))
        patterns.extend(getattr(gate, "PLACEHOLDER_TRANSITION_PATTERNS", []))
        patterns.extend(getattr(gate, "EXPLANATORY_EMOTION_FRAMES", []))
        bad_lines = gate.load_bad_lines()
        return patterns, bad_lines
    except Exception:
        return FALLBACK_BAD_PATTERNS, []


def slug_aliases(slug: str) -> list[str]:
    aliases = [slug]
    hyphen = slug.replace("_", "-")
    if hyphen not in aliases:
        aliases.append(hyphen)
    compact = slug.replace("_", "")
    if compact not in aliases:
        aliases.append(compact)
    return aliases


def find_matches(slug: str, rule: ArtifactRule) -> list[Path]:
    matches: list[Path] = []
    for slug_alias in slug_aliases(slug):
        for pattern in rule.patterns:
            rendered = pattern.format(slug=slug_alias)
            matches.extend(WRITING_CACHE.glob(rendered))
            if rule.name == "source_or_reading_notes":
                matches.extend(SOURCE_INGEST_CACHE.rglob(rendered))
                matches.extend(SOURCE_INGEST_CACHE.glob(f"{slug_alias}/source_pack.md"))
                matches.extend(SOURCE_INGEST_CACHE.glob(f"{slug_alias}/reading_pack.md"))
    return sorted(set(matches))


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def scan_draft(draft: Path) -> list[str]:
    text = draft.read_text(encoding="utf-8")
    patterns, bad_lines = import_quality_gate_patterns()
    failures: list[str] = []

    for phrase in bad_lines:
        if phrase and phrase in text:
            failures.append(f"exact bad line: {phrase}")

    for pattern in patterns:
        if re.search(pattern, text):
            failures.append(f"blocked pattern: {pattern}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check serious-writing SOP artifacts before showing a draft.")
    parser.add_argument("--topic-slug", required=True, help="Artifact slug, for example pope_ai.")
    parser.add_argument("--draft", required=True, help="Draft path to scan.")
    parser.add_argument("--allow-missing-comments", action="store_true", help="Allow comment pressure artifact to be absent.")
    parser.add_argument("--allow-missing-style-reference", action="store_true", help="Reserved compatibility flag.")
    args = parser.parse_args()

    slug = args.topic_slug
    draft = Path(args.draft)
    if not draft.is_absolute():
        draft = ROOT / draft

    failures: list[str] = []
    passed: list[str] = []

    if not draft.exists():
        failures.append(f"draft missing: {relative(draft)}")
    else:
        passed.append(f"draft exists: {relative(draft)}")

    for rule in BASE_RULES:
        if args.allow_missing_comments and rule.name == "comment_pressure_or_gap":
            passed.append(f"{rule.name}: skipped by explicit flag")
            continue
        matches = find_matches(slug, rule)
        if matches:
            passed.append(f"{rule.name}: {', '.join(relative(path) for path in matches[:3])}")
        elif rule.required:
            failures.append(f"missing artifact: {rule.name} ({', '.join(rule.patterns)})")

    if draft.exists():
        failures.extend(scan_draft(draft))

    print("# Writing SOP Preflight")
    print(f"topic_slug: {slug}")
    print(f"draft: {relative(draft)}")
    print()
    print("## Passed")
    for item in passed:
        print(f"- {item}")
    print()
    print("## Failures")
    if failures:
        for item in failures:
            print(f"- {item}")
        print()
        print("RESULT: FAIL")
        return 1
    print("- none")
    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
