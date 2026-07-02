#!/usr/bin/env python3
"""Create a Chinese article style-route card before drafting.

The card forces a choice between concrete Chinese article routes instead of
letting a draft become a generic source summary.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROUTES = {
    "initium_scene": "端传媒深度报道式：一个异常场景打开系统",
    "initium_questions": "端传媒问题组式：欲望 / 法律 / 系统拆开",
    "hidden_worker": "端闻人力成本式：隐藏劳动者先入场",
    "number_explainer": "数说科技式：一个数字进入，再追问它能证明什么",
    "sanlian_profile": "三联访谈/思想人物式：人物气质决定文章节奏",
    "latepost_org": "晚点商业组织式：公司行为如何违背市场默认逻辑",
    "waves_interview": "暗涌访谈式：让反共识引语成为论证发动机",
}


def build_card(topic: str, primary: str, secondary: str, notes: str) -> str:
    primary_desc = ROUTES.get(primary, primary)
    secondary_desc = ROUTES.get(secondary, secondary)
    return f"""# Chinese Article Style Route Card

Topic: {topic}

## Primary Route

- Route: {primary_desc}
- Opening job:
  - Enter through one concrete scene, person, number, quote, behavior, or contradiction.
  - Do not start from topic definition or source summary.
- What this route forces:
  - A readable entry before concept.
  - Motive and pressure before interpretation.

## Secondary Route

- Route: {secondary_desc}
- Texture job:
  - Add rhythm, restraint, quote handling, or paragraph movement.
  - Do not override the primary route.

## Route Notes

{notes.strip() or "- No extra notes provided."}

## Drafting Constraints

- First visible paragraph must contain a concrete anchor.
- Named people/institutions need motive or pressure.
- Use only one primary engine; do not mix every reference style.
- If the draft becomes a source summary, return to this route card before line-editing.

## Ready-To-Draft Gate

- [x] Primary route chosen.
- [x] Secondary route chosen.
- [x] Opening anchor named.
- [x] Speaker/institution pressure named.
- [x] What to cut from other routes named.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--primary", required=True, choices=sorted(ROUTES))
    parser.add_argument("--secondary", required=True, choices=sorted(ROUTES))
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    card = build_card(args.topic, args.primary, args.secondary, args.notes)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(card, encoding="utf-8")
    else:
        print(card)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
