#!/usr/bin/env python3
"""Block generic how-to/topic-summary angles before drafting.

For this workspace, a source-based personal-IP article needs tension, cost,
or a reversal. "X 怎么用 AI" and "不是只发 prompt" frames are often too
instructional unless the opening immediately names a concrete mistake,
consequence, or conflict.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


GENERIC_TITLE_PATTERNS = [
    r"怎么用\s*AI",
    r"如何用\s*AI",
    r"用\s*AI，不是",
    r"不是只发.*(prompt|提示词)",
    r"先给材料",
    r"再要答案",
    r"方法",
    r"技巧",
]

NEEDED_TENSION_MARKERS = [
    "为什么",
    "错",
    "骗",
    "平均答案",
    "没有辨识度",
    "站不住",
    "查错",
    "翻车",
    "失望",
    "漏洞",
    "反方",
    "代价",
    "风险",
]


def title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return ""


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    heading = title(text)
    opening = "\n".join(paragraphs(text)[:2])

    generic_hits = [pattern for pattern in GENERIC_TITLE_PATTERNS if re.search(pattern, heading, re.I)]
    if generic_hits:
        tension_count = sum(1 for marker in NEEDED_TENSION_MARKERS if marker in heading + opening)
        if tension_count < 2:
            failures.append(
                "generic how-to angle without enough reader tension: "
                + "、".join(generic_hits)
            )
        else:
            warnings.append("generic title pattern survived only because opening adds tension: " + "、".join(generic_hits))

    if "富人" in heading and "学者" in heading and not any(marker in heading for marker in ("为什么", "错", "骗", "平均", "答案", "查错")):
        failures.append("title names distant groups but lacks a reader-facing conflict")

    if ("prompt" in heading.lower() or "提示词" in heading) and not any(marker in heading + opening for marker in ("平均答案", "站不住", "失望", "漏洞")):
        failures.append("prompt/提示词 frame is too tutorial-like without a concrete failure")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    text = args.draft.read_text(encoding="utf-8", errors="replace")
    failures, warnings = audit(text)
    print("PASS" if not failures else "FAIL")
    for failure in failures:
        print(f"- FAIL: {failure}")
    for warning in warnings:
        print(f"- WARN: {warning}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
