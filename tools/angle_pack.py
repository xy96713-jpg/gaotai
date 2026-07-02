#!/usr/bin/env python3
"""Create a three-angle pre-draft pack for source-based personal-IP writing."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / ".cache" / "writing"


def slugify(value: str, fallback: str = "topic") -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip()).strip("-")
    return (value or fallback)[:80]


def read_text(path: Path | None) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def extract_signals(text: str, limit: int = 8) -> list[str]:
    candidates: list[tuple[int, int, str]] = []
    weak_headings = {
        "# combined source pack",
        "## full source map",
        "## material map",
        "## person context card",
        "## source reading card",
        "## reading evidence card",
        "## source language card",
        "## rhetorical engine card",
    }
    strong_terms = [
        "babel",
        "jerusalem",
        "tower",
        "city",
        "disarm",
        "technology is never neutral",
        "architecture of visibility",
        "moral",
        "dignity",
        "power",
        "war",
        "巴别",
        "耶路撒冷",
        "塔",
        "城",
        "解除武装",
        "不可能是中立",
        "人性尊严",
        "权力",
        "战争",
    ]
    weak_terms = ["published", "source:", "primary:", "official explainer", "secondary report", "blocked page"]
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        lowered = stripped.lower()
        if lowered in weak_headings or re.match(r"^(date|topic|source pack):\s", stripped, re.I):
            continue
        if stripped.startswith("#"):
            continue
        if any(term in lowered for term in weak_terms):
            continue
        if stripped.endswith(":") or "TODO" in stripped:
            continue
        if len(stripped) < 12:
            continue
        score = 0
        score += sum(3 for term in strong_terms if term in lowered or term in stripped)
        if "Core action" in stripped or "Story/metaphor/example" in stripped or "Relation to article" in stripped:
            score += 2
        if "must not be flattened" in lowered or "不要写成" in stripped:
            score += 2
        if score <= 0:
            score = 1 if len(candidates) < limit else 0
        if score > 0:
            candidates.append((score, -index, stripped[:220]))
    ranked = sorted(candidates, reverse=True)
    seen: set[str] = set()
    signals: list[str] = []
    for _, _, signal in ranked:
        if signal in seen:
            continue
        seen.add(signal)
        signals.append(signal)
        if len(signals) >= limit:
            break
    return signals


def build_pack(topic: str, source_pack: Path | None, source_text: str) -> str:
    signals = extract_signals(source_text)
    signal_block = "\n".join(f"- {signal}" for signal in signals) if signals else "- TODO: add source signals"
    source_line = str(source_pack) if source_pack else "manual / not provided"

    return f"""# Angle Pack

Generated: {datetime.now().isoformat(timespec="seconds")}
Topic: {topic}
Source pack: {source_line}

## Source Signals To Preserve

{signal_block}

## Candidate A: Conflict / Debate

- Title-hook:
- Opening 150-250 Chinese characters:
- Article engine:
- Source proof:
- Reader objection:
- Why this may work:
- Why this may fail:
- Platform fit:

## Candidate B: Person / Institution

- Title-hook:
- Opening 150-250 Chinese characters:
- Article engine:
- Person or institution context that matters:
- Source proof:
- Reader objection:
- Why this may work:
- Why this may fail:
- Platform fit:

## Candidate C: Mechanism / Image

- Title-hook:
- Opening 150-250 Chinese characters:
- Article engine:
- Concrete mechanism or source image:
- Source proof:
- Reader objection:
- Why this may work:
- Why this may fail:
- Platform fit:

## Editorial Pick

- Recommended angle:
- Why this angle is stronger than the other two:
- What must be cut from the losing angles:
- What must be verified before drafting:
- Not-ready condition:
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--source-pack", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_text = read_text(args.source_pack)
    out = args.out or args.out_dir / f"{slugify(args.topic)}_angle_pack.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_pack(args.topic, args.source_pack, source_text), encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
