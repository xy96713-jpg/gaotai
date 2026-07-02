#!/usr/bin/env python3
"""Create STORM-style pre-writing research cards from a topic/source pack."""

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


def extract_anchors(text: str, limit: int = 12) -> list[str]:
    anchors: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in {"---", "# Combined Source Pack"}:
            continue
        if stripped.startswith("<!--"):
            continue
        if re.match(r"^(source|title|converter|ingested_at):\s", stripped):
            continue
        if stripped.startswith("#"):
            anchors.append(stripped)
        elif re.search(r"https?://", stripped):
            anchors.append(stripped[:220])
        elif len(stripped) >= 30 and len(anchors) < 4:
            anchors.append(stripped[:220])
        if len(anchors) >= limit:
            break
    return anchors


def build_cards(topic: str, source_pack: Path | None, source_text: str) -> str:
    anchors = extract_anchors(source_text)
    anchor_block = "\n".join(f"- {anchor}" for anchor in anchors) if anchors else "- TODO: add source anchors"
    source_line = str(source_pack) if source_pack else "manual / not provided"

    return f"""# STORM-Style Research Cards

Generated: {datetime.now().isoformat(timespec="seconds")}
Topic: {topic}
Source pack: {source_line}

## Source Anchors

{anchor_block}

## Perspective-Guided Question Map

Use this before drafting. Each perspective must produce questions that would change the angle, not just fill background.

### 1. Source author / institution

- What is this speaker trying to protect?
- What language or metaphor do they use before they explain?
- Which claim would be weakened if removed from its original context?

### 2. Skeptical reader

- What sounds exaggerated, moralizing, or unprovable?
- What would a smart reader push back on first?
- Which sentence could be true but still boring?

### 3. Affected person

- Who feels the consequence in daily life?
- What decision, form, score, job, product, app, hospital, school, or bill makes the issue visible?
- What detail would make the reader stop treating this as abstract AI discourse?

### 4. Builder / operator

- What mechanism turns the idea into an actual workflow?
- Who sets the rule, threshold, prompt, model, data source, or incentive?
- Where can responsibility hide?

### 5. Money / power / institution

- Who benefits if this interpretation becomes normal?
- Who loses bargaining power?
- What gets called efficiency because the cost lands somewhere else?

### 6. Historical / cultural echo

- Is there an older metaphor, law, ritual, crisis, or social pattern that gives this source weight?
- What comparison is tempting but too cheap?
- What comparison is precise enough to keep?

## Simulated Expert Interview Prompts

Ask these in order. Do not draft until at least three have concrete answers.

1. What is the strongest original idea in the source, in the source's own terms?
2. What is the lazy mainstream take, and why is it not enough?
3. What mechanism would make this claim true in the real world?
4. What is the best objection from someone who dislikes moral panic?
5. What one scene could carry the argument without explaining it?
6. Which source phrase should be quoted or closely paraphrased because Chinese paraphrase would weaken it?
7. What must not be claimed because the source does not prove it?

## Reader Doubt Card

- The reader may doubt:
- The strongest fair objection:
- Evidence needed before making the claim:
- What to say more modestly:
- What to cut entirely:

## Angle Stress Test

Reject an angle if any answer is "yes":

- Could this title fit five unrelated AI stories?
- Does it start from a summary instead of a person, image, decision, or conflict?
- Does it depend on vague words like "system", "时代", "风险", or "价值"?
- Does it flatten the source's strongest metaphor?
- Does it sound like a news brief or class note?

## Candidate Article Engines

Fill 2-3 only. Choose one before drafting.

### Engine A: source image

- Opening image:
- Turn:
- Modern consequence:
- Proof:
- Boundary:

### Engine B: person / institution

- Speaker context that matters:
- Why this speaker now:
- Source claim:
- Reader-facing scene:
- Objection:

### Engine C: concrete mechanism

- Real workflow:
- Hidden decision:
- Human cost:
- Source support:
- Counterpoint:

## Ready-To-Draft Gate

- [ ] Primary source has been read or access limits are recorded.
- [ ] At least three source anchors are usable.
- [ ] One reader objection is strong enough to change wording.
- [ ] One concrete scene exists.
- [ ] The chosen engine is not "summarize material -> state opinion -> explain".
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
    out = args.out or args.out_dir / f"{slugify(args.topic)}_storm_cards.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_cards(args.topic, args.source_pack, source_text), encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
