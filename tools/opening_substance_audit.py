#!/usr/bin/env python3
"""Audit whether a Chinese article opening enters through substance, not meta-talk."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


META_OPENING_PATTERNS = [
    r"这个题目",
    r"这个选题",
    r"第一眼看上去",
    r"看上去.*有点大",
    r"听起来.*夸张",
    r"听上去.*夸张",
    r"三个词放在一起",
    r"很容易像",
    r"往.*上靠的标题",
    r"今天聊聊",
    r"分享一个",
    r"最近看到",
]

ACTOR_ANCHORS = [
    "教皇",
    "Leo",
    "Vatican",
    "梵蒂冈",
    "Anthropic",
    "Olah",
    "公司",
    "平台",
    "学校",
    "医院",
    "医生",
    "律师",
    "用户",
    "你",
]

EVENT_ANCHORS = [
    "发布",
    "通谕",
    "现场",
    "Synod Hall",
    "2026",
    "5 月",
    "第一封",
    "会议",
    "报告",
    "签字",
    "复核",
    "查错",
    "查漏洞",
]

IMAGE_ANCHORS = [
    "巴别塔",
    "耶路撒冷",
    "塔",
    "城",
    "墙",
    "废墟",
    "门",
    "算法",
    "模型",
    "简历",
    "拒信",
    "合同",
    "体检报告",
    "论文",
    "论文摘要",
    "引用",
    "化学结构",
]

CONTRADICTION_MARKERS = [
    "没有",
    "却",
    "反而",
    "不是",
    "先",
    "反常",
    "但",
]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def chinese_chars(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9 ]", text))


def hit_any(text: str, items: list[str]) -> bool:
    return any(item in text for item in items)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    if not paras:
        return ["no opening paragraphs found"], []

    first = paras[0]
    body_start = "\n".join(paras[:5])
    first_120 = chinese_chars(body_start)[:120]

    meta_hits = [p for p in META_OPENING_PATTERNS if re.search(p, first_120)]
    if meta_hits:
        failures.append("opening starts with meta-commentary: " + "、".join(meta_hits))

    anchor_count = 0
    anchor_count += 1 if hit_any(first_120, ACTOR_ANCHORS) else 0
    anchor_count += 1 if hit_any(first_120, EVENT_ANCHORS) else 0
    anchor_count += 1 if hit_any(first_120, IMAGE_ANCHORS) else 0
    anchor_count += 1 if hit_any(first_120, CONTRADICTION_MARKERS) else 0

    if anchor_count < 2:
        failures.append(f"opening lacks concrete substance anchors: count={anchor_count}, first_120={first_120}")

    if len(first) <= 12 and not hit_any(first, IMAGE_ANCHORS + ACTOR_ANCHORS):
        warnings.append("first paragraph is very short without a strong image or actor")

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
