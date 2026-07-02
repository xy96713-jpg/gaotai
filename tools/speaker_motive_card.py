#!/usr/bin/env python3
"""Create a speaker motive card for source-based writing."""

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


def build_card(topic: str, speakers: list[str]) -> str:
    speaker_blocks = []
    for speaker in speakers or ["TODO speaker"]:
        speaker_blocks.append(
            f"""### {speaker}

- What they said:
- Where / role:
- Who they are speaking to:
- Why now:
- What pressure or interest sits behind the statement:
- What problem this statement solves for them:
- What they avoid saying:
- What a skeptical reader should ask:
- How this should enter the article:
- What would be decorative and should be cut:
"""
        )

    return f"""# Speaker Motive Card

Generated: {datetime.now().isoformat(timespec="seconds")}
Topic: {topic}

## Speaker / Institution Map

{''.join(speaker_blocks)}
## Article Use

- Which speaker creates the opening tension:
- Which speaker supplies authority:
- Which speaker supplies suspicion or objection:
- Which quote or statement deserves direct treatment:
- Which statement should be paraphrased:
- Which speaker should not appear because they only add clutter:

## Ready-To-Draft Gate

- [ ] Every named speaker or institution has a role.
- [ ] Every important statement has a motive or pressure.
- [ ] The draft can explain why this person says this now.
- [ ] No biography appears unless it changes how the reader hears the statement.
- [ ] The article distinguishes motive, evidence, and speculation.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--speaker", action="append", default=[])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = args.out or args.out_dir / f"{slugify(args.topic)}_speaker_motive_card.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_card(args.topic, args.speaker), encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
