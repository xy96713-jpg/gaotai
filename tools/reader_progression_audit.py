#!/usr/bin/env python3
"""Audit whether a Chinese personal-IP draft actually moves for the reader.

This catches failures that mechanical rhythm tags miss: repeated title-as-first
paragraph, too many short bridge paragraphs, and navigation phrases that
announce movement instead of creating it.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NAVIGATION_PHRASES = [
    "到这里",
    "这条线",
    "这一下",
    "这句话放到",
    "放到我自己的工作里",
    "回到",
    "接上了",
    "开始露出来",
]

WEAK_BRIDGE_PATTERNS = [
    r"^那.*为什么.*[？?]?$",
    r"^这.*同一件事[。.]?$",
    r"^这更像.*[。.]?$",
    r"^这.*压低了[。.]?$",
    r"^别先问.*[。.]?$",
    r"^先问.*[。.]?$",
]


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def clean_heading(line: str) -> str:
    return re.sub(r"^#+\s*", "", line.strip()).strip()


def paragraphs(text: str) -> list[str]:
    paras: list[str] = []
    for raw in re.split(r"\n\s*\n", text):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        paras.append(re.sub(r"\s+", " ", stripped))
    return paras


def title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return clean_heading(stripped)
    return ""


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    heading = title(text)

    if heading and paras:
        first = paras[0].strip("。.!！?？ ")
        head = heading.strip("。.!！?？ ")
        if first == head:
            failures.append("title is repeated verbatim as the first paragraph; this creates template rhythm")

    short_bridges = []
    for index, para in enumerate(paras, 1):
        length = chinese_len(para)
        weak_bridge = any(re.search(pattern, para) for pattern in WEAK_BRIDGE_PATTERNS)
        if length <= 18 or weak_bridge:
            short_bridges.append((index, para))

    if len(paras) >= 8:
        ratio = len(short_bridges) / max(len(paras), 1)
        if len(short_bridges) > 5 or ratio > 0.28:
            preview = "；".join(f"{i}:{p[:24]}" for i, p in short_bridges[:8])
            failures.append(f"too many short bridge/navigation paragraphs ({len(short_bridges)}/{len(paras)}): {preview}")

    nav_hits = []
    for phrase in NAVIGATION_PHRASES:
        count = text.count(phrase)
        if count:
            nav_hits.append(f"{phrase}×{count}")
    if nav_hits:
        failures.append("navigation phrases announce structure instead of moving the argument: " + "、".join(nav_hits))

    # A mature piece should change the reader's question, not only add sources.
    questionish = [p for p in paras if "？" in p or "为什么" in p or "怎么" in p]
    if len(paras) >= 10 and len(questionish) <= 1:
        warnings.append("reader-question movement is thin; consider adding a real objection or reversal, not a rhetorical bridge")

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
