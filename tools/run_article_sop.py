#!/usr/bin/env python3
"""Run the serious-writing SOP gates and produce one quality report.

This is the workflow controller. It does not decide taste by itself; it makes
the existing reading artifacts and audit tools visible, then blocks delivery
when a required artifact or hard gate is missing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRITING_CACHE = ROOT / ".cache" / "writing"
SOURCE_INGEST_CACHE = ROOT / ".cache" / "source-ingest"


@dataclass(frozen=True)
class ArtifactSelector:
    key: str
    label: str
    patterns: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    required: bool = True

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class GeneratedArtifact:
    key: str
    label: str
    path: Path


QUALITY_SELECTORS = [
    ArtifactSelector("source_pack", "Source pack / reading pack", ("{slug}*reading*pack*.md", "{slug}*source*pack*.md")),
    ArtifactSelector(
        "source_coverage",
        "Source coverage table",
        ("{slug}*source*coverage*.md", "{slug}*coverage*table*.md"),
    ),
    ArtifactSelector("research_cards", "STORM-style research cards", ("{slug}*storm*cards*.md", "{slug}*research*cards*.md")),
    ArtifactSelector("angle_pack", "Angle pack / direction tree", ("{slug}*angle*pack*.md", "{slug}*direction*tree*.md")),
    ArtifactSelector(
        "comment_pressure_card",
        "Comment pressure / public discussion",
        ("{slug}*comment*pressure*.md", "{slug}*public*discussion*.md", "{slug}*comment*gap*.md"),
    ),
    ArtifactSelector(
        "style_reference_card",
        "Style reference / mature study",
        ("{slug}*style*reference*.md", "{slug}*mature*study*.md", "{slug}*voice*reference*.md"),
    ),
    ArtifactSelector("chinese_style_card", "Chinese article route", ("{slug}*chinese*style*route*.md",)),
    ArtifactSelector("speaker_motive_card", "Speaker motive", ("{slug}*speaker*motive*.md",)),
    ArtifactSelector("opening_pack", "Opening pack", ("{slug}*opening*pack*.md", "{slug}*opening*gate*.md")),
    ArtifactSelector("scene_pack", "Scene / rhythm pack", ("{slug}*scene*rhythm*.md", "{slug}*rhythm*ladder*.md")),
    ArtifactSelector(
        "critique",
        "Hostile critique / reader test",
        ("{slug}*hostile*critique*.md", "{slug}*reader*critique*.md", "{slug}*critique*.md"),
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def slug_aliases(slug: str) -> list[str]:
    aliases = [slug]
    hyphen = slug.replace("_", "-")
    if hyphen not in aliases:
        aliases.append(hyphen)
    compact = slug.replace("_", "")
    if compact not in aliases:
        aliases.append(compact)
    return aliases


def find_candidates(slug: str, selector: ArtifactSelector, cache_dir: Path = WRITING_CACHE) -> list[Path]:
    ranked: list[tuple[int, float, str, Path]] = []
    seen: set[Path] = set()
    cache_dirs = [cache_dir]
    if selector.key == "source_pack":
        cache_dirs.append(SOURCE_INGEST_CACHE)
        for slug_alias in slug_aliases(slug):
            for folder_name in {slug_alias, slug_alias.replace("_", "-"), slug_alias.replace("-", "_")}:
                candidate = SOURCE_INGEST_CACHE / folder_name / "source_pack.md"
                if candidate.is_file() and candidate not in seen:
                    seen.add(candidate)
                    ranked.append((-1, -candidate.stat().st_mtime, str(candidate), candidate))
    for directory in cache_dirs:
        for slug_alias in slug_aliases(slug):
            for pattern_index, pattern in enumerate(selector.patterns):
                search_pattern = pattern.format(slug=slug_alias)
                for path in directory.rglob(search_pattern) if directory == SOURCE_INGEST_CACHE else directory.glob(search_pattern):
                    if not path.is_file() or path in seen:
                        continue
                    seen.add(path)
                    ranked.append((pattern_index, -path.stat().st_mtime, str(path), path))
    return [path for _, _, _, path in sorted(ranked)]


def draft_text(draft: Path) -> str:
    return draft.read_text(encoding="utf-8", errors="replace") if draft.exists() else ""


def is_writing_workflow_topic(slug: str, draft: Path) -> bool:
    text = draft_text(draft)
    haystack = f"{slug}\n{text}"
    direct_markers = [
        "writing",
        "写作",
        "写稿",
        "稿子",
        "文章",
        "SOP",
        "skill",
        "退稿",
        "before/after",
    ]
    workflow_markers = ["workflow", "工作流", "流程"]
    return any(marker in haystack for marker in direct_markers) or (
        any(marker in haystack for marker in workflow_markers)
        and any(marker in haystack for marker in ("写作", "写稿", "稿子", "文章", "skill", "SOP"))
    )


def select_artifacts(slug: str, cache_dir: Path = WRITING_CACHE) -> dict[str, Path | None]:
    selected: dict[str, Path | None] = {}
    for selector in QUALITY_SELECTORS:
        candidates = find_candidates(slug, selector, cache_dir)
        selected[selector.key] = candidates[0] if candidates else None
    return selected


def missing_required(selected: dict[str, Path | None]) -> list[ArtifactSelector]:
    by_key = {selector.key: selector for selector in QUALITY_SELECTORS}
    missing: list[ArtifactSelector] = []
    for key, path in selected.items():
        selector = by_key[key]
        if selector.required and path is None:
            missing.append(selector)
    return missing


def generated_artifacts(slug: str) -> list[GeneratedArtifact]:
    return [
        GeneratedArtifact("editorial_desk_preflight", "Editorial Desk V2 preflight", WRITING_CACHE / f"{slug}_editorial_desk_preflight_latest.md"),
        GeneratedArtifact("decision_log", "Decision log", WRITING_CACHE / f"{slug}_decision_log_latest.md"),
        GeneratedArtifact("section_beat_board", "Section beat board", WRITING_CACHE / f"{slug}_section_beat_board_latest.md"),
        GeneratedArtifact("citation_map", "Citation / source support map", WRITING_CACHE / f"{slug}_citation_map_latest.md"),
    ]


def run_command(name: str, command: list[str], required: bool = True) -> CommandResult:
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return CommandResult(name=name, command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, required=required)


def gate_commands(slug: str, draft: Path, selected: dict[str, Path | None], allow_quality_skip: bool) -> list[tuple[str, list[str], bool]]:
    py = sys.executable
    generated = {artifact.key: artifact.path for artifact in generated_artifacts(slug)}
    commands: list[tuple[str, list[str], bool]] = [
        (
            "editorial_desk_preflight",
            [
                py,
                str(ROOT / "tools" / "editorial_desk_preflight.py"),
                "--topic-slug",
                slug,
                "--draft",
                str(draft),
                "--report",
                str(generated["editorial_desk_preflight"]),
            ],
            True,
        ),
        (
            "decision_log",
            [
                py,
                str(ROOT / "tools" / "decision_log.py"),
                "--topic-slug",
                slug,
                "--draft",
                str(draft),
                "--output",
                str(generated["decision_log"]),
            ],
            True,
        ),
        (
            "section_beat_check",
            [
                py,
                str(ROOT / "tools" / "section_beat_check.py"),
                str(draft),
                "--board-output",
                str(generated["section_beat_board"]),
            ],
            True,
        ),
        ("topic_viability_gate", [py, str(ROOT / "tools" / "topic_viability_gate.py"), str(draft)], True),
        ("opening_substance_audit", [py, str(ROOT / "tools" / "opening_substance_audit.py"), str(draft)], True),
        ("opening_line_taste_gate", [py, str(ROOT / "tools" / "opening_line_taste_gate.py"), str(draft)], True),
        ("pulpit_tone_audit", [py, str(ROOT / "tools" / "pulpit_tone_audit.py"), str(draft)], True),
        ("oral_script_gate", [py, str(ROOT / "tools" / "oral_script_gate.py"), str(draft)], True),
        ("rhythm_audit", [py, str(ROOT / "tools" / "rhythm_audit.py"), str(draft)], True),
        ("reader_progression_audit", [py, str(ROOT / "tools" / "reader_progression_audit.py"), str(draft)], True),
        ("opening_ending_taste_audit", [py, str(ROOT / "tools" / "opening_ending_taste_audit.py"), str(draft)], True),
        ("chinese_surface_audit", [py, str(ROOT / "tools" / "chinese_surface_audit.py"), str(draft)], True),
        ("boring_angle_audit", [py, str(ROOT / "tools" / "boring_angle_audit.py"), str(draft)], True),
        ("article_engine_audit", [py, str(ROOT / "tools" / "article_engine_audit.py"), str(draft)], True),
        ("insight_gate", [py, str(ROOT / "tools" / "insight_gate.py"), str(draft)], True),
        ("juvenile_audit", [py, str(ROOT / "tools" / "juvenile_audit.py"), str(draft)], True),
        ("writing_sop_preflight", [py, str(ROOT / "tools" / "writing_sop_preflight.py"), "--topic-slug", slug, "--draft", str(draft)], True),
    ]

    if selected.get("source_coverage") is not None:
        commands.append(
            (
                "source_coverage_gate",
                [
                    py,
                    str(ROOT / "tools" / "source_coverage_gate.py"),
                    str(selected["source_coverage"]),
                ],
                True,
            )
        )

    if is_writing_workflow_topic(slug, draft):
        commands.insert(
            -2,
            ("writing_lift_gate", [py, str(ROOT / "tools" / "writing_lift_gate.py"), str(draft)], True),
        )

    if selected["source_pack"] is not None:
        commands.append(
            (
                "citation_map",
                [
                    py,
                    str(ROOT / "tools" / "citation_map.py"),
                    "--draft",
                    str(draft),
                    "--source-pack",
                    str(selected["source_pack"]),
                    "--output",
                    str(generated["citation_map"]),
                ],
                True,
            )
        )

    quality_required = not allow_quality_skip
    quality_missing = any(
        selected[key] is None
        for key in [
            "source_pack",
            "source_coverage",
            "research_cards",
            "angle_pack",
            "comment_pressure_card",
            "style_reference_card",
            "chinese_style_card",
            "speaker_motive_card",
            "opening_pack",
            "scene_pack",
            "critique",
        ]
    )
    if not quality_missing:
        commands.append(
            (
                "writing_quality_gate",
                [
                    py,
                    str(ROOT / "tools" / "writing_quality_gate.py"),
                    "--source-pack",
                    str(selected["source_pack"]),
                    "--research-cards",
                    str(selected["research_cards"]),
                    "--angle-pack",
                    str(selected["angle_pack"]),
                    "--comment-pressure-card",
                    str(selected["comment_pressure_card"]),
                    "--style-reference-card",
                    str(selected["style_reference_card"]),
                    "--chinese-style-card",
                    str(selected["chinese_style_card"]),
                    "--speaker-motive-card",
                    str(selected["speaker_motive_card"]),
                    "--opening-pack",
                    str(selected["opening_pack"]),
                    "--scene-pack",
                    str(selected["scene_pack"]),
                    "--draft",
                    str(draft),
                    "--critique",
                    str(selected["critique"]),
                ],
                quality_required,
            )
        )
    return commands


def command_text(command: list[str]) -> str:
    return " ".join(str(part) for part in command)


def summarize_output(text: str, limit: int = 3000) -> str:
    stripped = text.strip()
    if not stripped:
        return "_no output_"
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit].rstrip() + "\n... [truncated]"


def build_report(
    *,
    slug: str,
    draft: Path,
    selected: dict[str, Path | None],
    missing: list[ArtifactSelector],
    results: list[CommandResult],
    allow_quality_skip: bool,
    generated: list[GeneratedArtifact] | None = None,
) -> tuple[str, bool]:
    hard_failures = [result for result in results if result.required and not result.passed]
    blocked = bool(missing or hard_failures)
    decision = "BLOCK" if blocked else "ALLOW"
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = []
    lines.append("# Article SOP Quality Report")
    lines.append("")
    lines.append(f"- Generated: {now}")
    lines.append(f"- Topic slug: `{slug}`")
    lines.append(f"- Draft: `{rel(draft)}`")
    lines.append(f"- Decision: **{decision}**")
    lines.append(f"- Quality gate skip allowed: `{allow_quality_skip}`")
    lines.append("")

    lines.append("## Artifact Map")
    by_key = {selector.key: selector for selector in QUALITY_SELECTORS}
    for key, path in selected.items():
        selector = by_key[key]
        value = f"`{rel(path)}`" if path else "_missing_"
        lines.append(f"- {selector.label}: {value}")
    lines.append("")

    lines.append("## Generated Control Artifacts")
    for artifact in generated or []:
        value = f"`{rel(artifact.path)}`" if artifact.path.exists() else "_not generated_"
        lines.append(f"- {artifact.label}: {value}")
    if not generated:
        lines.append("- none")
    lines.append("")

    lines.append("## Missing Required Artifacts")
    if missing:
        for selector in missing:
            lines.append(f"- {selector.label}: patterns `{', '.join(selector.patterns)}`")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Gate Results")
    for result in results:
        status = "PASS" if result.passed else ("FAIL" if result.required else "WARN")
        lines.append(f"### {result.name}: {status}")
        lines.append("")
        lines.append(f"`{command_text(result.command)}`")
        lines.append("")
        if result.stdout.strip():
            lines.append("```text")
            lines.append(summarize_output(result.stdout))
            lines.append("```")
        if result.stderr.strip():
            lines.append("stderr:")
            lines.append("```text")
            lines.append(summarize_output(result.stderr))
            lines.append("```")
        lines.append("")

    lines.append("## Next Repair")
    if not blocked:
        lines.append("- Draft may be shown as a candidate. Human taste review still decides whether it is publishable.")
    else:
        if missing:
            lines.append("- Create or mark unavailable the missing artifacts before showing a full draft.")
        for result in hard_failures:
            lines.append(f"- Repair `{result.name}` failure and rerun this controller.")
    lines.append("")
    return "\n".join(lines), not blocked


def default_report_path(slug: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return WRITING_CACHE / f"{slug}_sop_quality_report_{stamp}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full article SOP controller and write a quality report.")
    parser.add_argument("--topic-slug", required=True, help="Artifact slug, for example pope_ai.")
    parser.add_argument("--draft", required=True, help="Draft file to evaluate.")
    parser.add_argument("--report", help="Report output path. Defaults to .cache/writing/<slug>_sop_quality_report_<timestamp>.md")
    parser.add_argument(
        "--allow-quality-skip",
        action="store_true",
        help="Do not fail solely because writing_quality_gate cannot be assembled. Other gates remain required.",
    )
    args = parser.parse_args()

    draft = resolve_path(args.draft)
    report = resolve_path(args.report) if args.report else default_report_path(args.topic_slug)
    selected = select_artifacts(args.topic_slug)
    missing = missing_required(selected)
    generated = generated_artifacts(args.topic_slug)

    results: list[CommandResult] = []
    if not draft.exists():
        missing = [*missing, ArtifactSelector("draft", "Draft file", (args.draft,))]
    else:
        for name, command, required in gate_commands(args.topic_slug, draft, selected, args.allow_quality_skip):
            results.append(run_command(name, command, required))

    report_text, allowed = build_report(
        slug=args.topic_slug,
        draft=draft,
        selected=selected,
        missing=missing,
        results=results,
        allow_quality_skip=args.allow_quality_skip,
        generated=generated,
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(report_text, encoding="utf-8")

    print(f"Decision: {'ALLOW' if allowed else 'BLOCK'}")
    print(f"Report: {rel(report)}")
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
