#!/usr/bin/env python3
"""Create a comment-pressure card from public discussion snippets."""

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


def read_many(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        chunks.append(f"\n\n<!-- comment-source: {path} -->\n")
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def extract_comment_signals(text: str, limit: int = 12) -> list[str]:
    signals: list[str] = []
    for line in text.splitlines():
        stripped = re.sub(r"\s+", " ", line).strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        if len(stripped) < 18:
            continue
        signals.append(stripped[:260])
        if len(signals) >= limit:
            break
    return signals


def build_card(topic: str, comments_text: str, unavailable: str | None = None) -> str:
    signals = extract_comment_signals(comments_text)
    signal_block = "\n".join(f"- {signal}" for signal in signals) if signals else "- TODO: add comment signals or mark unavailable"
    unavailable_line = unavailable or ""

    return f"""# Comment Pressure Card

Generated: {datetime.now().isoformat(timespec="seconds")}
Topic: {topic}
Unavailable reason: {unavailable_line}

## Public Discussion Sources

- TODO: list Reddit/HN/YouTube/article comments/forum links, or explain why unavailable.

## Raw Reader-Language Signals

{signal_block}

## Reader Objections

- Strongest fair objection:
- Most likely misunderstanding:
- What sounds like moral panic:
- What sounds like source summary:
- What would make a skeptical reader keep reading:

## Plain-Language Hooks From Comments

- Phrase or discomfort worth translating:
- Phrase to avoid because it is shallow:
- Question a normal reader would ask:

## Editorial Pressure

- How the angle should change after reading comments:
- What claim must become more modest:
- What concrete example should enter the draft:
- What cannot be used as factual proof:

## Ready-To-Draft Gate

- [ ] At least one fair objection is written.
- [ ] At least one reader-language signal is written.
- [ ] Comments are used as audience pressure, not evidence.
- [ ] If comments are unavailable, the access gap is stated.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("comments", nargs="*", type=Path)
    parser.add_argument("--unavailable", help="Reason public discussion could not be read")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    comments_text = read_many(args.comments) if args.comments else ""
    out = args.out or args.out_dir / f"{slugify(args.topic)}_comment_pressure_card.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_card(args.topic, comments_text, args.unavailable), encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
