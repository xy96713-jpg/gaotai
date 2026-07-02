#!/usr/bin/env python3
"""Audit rhythm problems in Chinese personal-IP drafts.

This is not a beauty score. It catches common reasons a source-based article
feels unreadable: card-stacking, flat paragraph lengths, explanatory drift,
placeholder transitions, and too much abstract language before concrete entry.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ABSTRACT_WORDS = [
    "系统",
    "时代",
    "价值",
    "权力",
    "秩序",
    "文明",
    "风险",
    "效率",
    "技术",
    "机制",
    "伦理",
    "治理",
    "结构",
]

EXPLANATORY_OPENERS = [
    "这",
    "因此",
    "所以",
    "而",
    "但",
    "同时",
    "换句话说",
    "也就是说",
    "从这个角度",
    "问题在于",
]

PLACEHOLDER_TRANSITIONS = [
    "画面换了",
    "镜头一转",
    "接下来",
    "紧接着",
    "原文转向",
    "文章指出",
    "作者写到",
    "这说明",
    "这也说明",
    "由此可见",
]

CONCRETE_WORDS = [
    "教皇",
    "巴别塔",
    "耶路撒冷",
    "城",
    "塔",
    "房间",
    "公司",
    "工作",
    "医院",
    "贷款",
    "保险",
    "招聘",
    "武器",
    "战争",
    "孩子",
    "学校",
    "手机",
    "平台",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in paras if not p.startswith("#")]


def first_body_paragraph(paras: list[str]) -> str:
    for para in paras:
        if para and not para.startswith("- ") and not para.startswith("Title"):
            return para
    return paras[0] if paras else ""


def starts_with_explainer(para: str) -> bool:
    stripped = para.strip()
    return any(stripped.startswith(opener) for opener in EXPLANATORY_OPENERS)


def has_concrete_anchor(text: str) -> bool:
    return any(word in text for word in CONCRETE_WORDS)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    if not paras:
        return ["no body paragraphs found"], []

    lengths = [chinese_len(p) for p in paras]
    body = "\n\n".join(paras)
    first = first_body_paragraph(paras)
    first_180 = first[:180]

    if chinese_len(first_180) >= 80:
        abstract_hits = [word for word in ABSTRACT_WORDS if word in first_180]
        if len(abstract_hits) >= 4 and not has_concrete_anchor(first_180):
            failures.append("opening is abstract before concrete entry: " + "、".join(abstract_hits[:6]))

    placeholder_hits = [word for word in PLACEHOLDER_TRANSITIONS if re.search(word, body)]
    if placeholder_hits:
        failures.append("placeholder/source-navigation transitions: " + "、".join(placeholder_hits))

    if len(paras) >= 6:
        explainer_count = sum(1 for p in paras[:8] if starts_with_explainer(p))
        if explainer_count >= 4:
            warnings.append("too many early paragraphs start as explanation rather than movement")

    overlong = [i + 1 for i, length in enumerate(lengths) if length > 260]
    if overlong:
        warnings.append("overlong paragraphs at indexes: " + "、".join(map(str, overlong[:8])))

    very_short_run = 0
    max_short_run = 0
    for length in lengths:
        if 0 < length <= 18:
            very_short_run += 1
            max_short_run = max(max_short_run, very_short_run)
        else:
            very_short_run = 0
    if max_short_run >= 4:
        warnings.append("too many consecutive tiny paragraphs; rhythm may feel chopped")

    if len(lengths) >= 8:
        unique_buckets = len({min(length // 40, 6) for length in lengths})
        if unique_buckets <= 2:
            warnings.append("paragraph lengths have low variation; prose may feel mechanically paced")

    source_list_markers = len(re.findall(r"^\s*-\s+(Source|Claim|Section|Core action|Why|What|Useful|Risk):", body, re.M))
    if source_list_markers >= 5:
        failures.append("draft still looks like research cards, not article prose")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()

    failures, warnings = audit(read(args.draft))
    print("PASS" if not failures else "FAIL")
    for failure in failures:
        print(f"- FAIL: {failure}")
    for warning in warnings:
        print(f"- WARN: {warning}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
