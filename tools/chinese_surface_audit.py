#!/usr/bin/env python3
"""Block unnecessary bare English in user-visible Chinese drafts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BARE_ENGLISH_REPLACEMENTS = {
    "prompt": "提示词 / 提问",
    "Forbes": "《福布斯》",
    "Nature": "《自然》",
    "Stanford": "斯坦福",
    "Wiley": "威立",
    "Wharton": "沃顿",
}

# Product/model names can stay when necessary, but common words and publication
# names should not appear as bare English in Chinese personal-IP prose.
ALLOWED_BARE = {
    "AI",
    "Codex",
    "ChatGPT",
    "OpenAI",
    "Anthropic",
    "Claude",
    "NBER",
    "STORM",
}


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    for word, replacement in BARE_ENGLISH_REPLACEMENTS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            failures.append(f"bare English `{word}` should be Chinese in user-visible prose: use {replacement}")

    tokens = sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9+-]{2,}\b", text)))
    unknown = [token for token in tokens if token not in ALLOWED_BARE and token not in BARE_ENGLISH_REPLACEMENTS]
    if unknown:
        warnings.append("other bare English tokens need justification or first-use Chinese gloss: " + "、".join(unknown[:20]))

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
