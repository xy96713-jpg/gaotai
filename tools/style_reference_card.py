#!/usr/bin/env python3
"""Create a compact style-reference card from one or more reference texts."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / ".cache" / "writing"


def slugify(value: str, fallback: str = "voice") -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip()).strip("-")
    return (value or fallback)[:80]


def read_many(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        chunks.append(f"\n\n<!-- style-source: {path} -->\n")
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def reference_units(text: str) -> list[str]:
    timestamp_units = re.findall(r"\[\d{2}:\d{2}\]\s*([^\[]+)", text)
    if timestamp_units:
        raw_units = timestamp_units
    else:
        raw_units = re.split(r"\n+|[。！？!?]\s*", text)

    units: list[str] = []
    for unit in raw_units:
        stripped = re.sub(r"\s+", " ", unit).strip()
        stripped = re.sub(r"<!--.*?-->", "", stripped).strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("- "):
            continue
        if re.search(r"https?://", stripped):
            continue
        if re.match(r"^(URL|Video ID|Channel|Duration|Upload date|View count|Cookies used|Transcript source):", stripped):
            continue
        if len(stripped) > 120:
            continue
        units.append(stripped)
    return units


def sentence_lengths(text: str) -> tuple[int, int, int]:
    units = reference_units(text)
    if not units:
        return 0, 0, 0
    lengths = [len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", s)) for s in units]
    return min(lengths), round(sum(lengths) / len(lengths)), max(lengths)


def extract_examples(text: str, limit: int = 8) -> list[str]:
    examples: list[str] = []
    for stripped in reference_units(text):
        if 6 <= len(stripped) <= 90:
            examples.append(stripped)
        if len(examples) >= limit:
            break
    return examples


def build_card(name: str, reference_text: str) -> str:
    min_len, avg_len, max_len = sentence_lengths(reference_text)
    examples = extract_examples(reference_text)
    example_block = "\n".join(f"- {example}" for example in examples) if examples else "- TODO: add reference examples"

    return f"""# Style Reference Card

Generated: {datetime.now().isoformat(timespec="seconds")}
Voice name: {name}

## Reference Signals

- Sentence length range: {min_len}-{max_len}
- Average sentence length: {avg_len}
- Example lines:
{example_block}

## Voice Rules

- Opening habit:
- Evidence habit:
- Transition habit:
- Humor / irony level:
- Judgment level:
- How personal experience enters:
- How sources enter:
- How endings land:

## Must Keep

- Concrete nouns before abstractions.
- Source evidence after the reader has a reason to care.
- Serious argument, lighter entry.
- Blogger judgment, not institutional summary.

## Must Avoid

- News brief rhythm.
- Explaining the reading process inside the article.
- Over-smooth AI transitions.
- Empty self-entry phrases.
- One-size-fits-all AI trend language.

## Ready-To-Draft Gate

- [ ] At least three reference lines or observed habits are written.
- [ ] One opening habit is chosen.
- [ ] One transition habit is chosen.
- [ ] One source-citation habit is chosen.
- [ ] One ending habit is chosen.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("references", nargs="*", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_text = read_many(args.references) if args.references else ""
    out = args.out or args.out_dir / f"{slugify(args.name)}_style_reference_card.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_card(args.name, reference_text), encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
