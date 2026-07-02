#!/usr/bin/env python3
"""Audit Chinese drafts for pulpit tone: stiff, over-serious, lecture-like prose."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PULPIT_PHRASES = [
    "问题是",
    "问题在于",
    "重点不在于",
    "真正的问题",
    "真正值得警惕",
    "真正有意思的是",
    "这也是为什么",
    "这也正是",
    "它指向的是",
    "它说明",
    "由此可见",
    "这不是简单的同框",
    "这个选择本身",
    "锋利的地方就在这里",
    "我们必须认识到",
    "这给我们的启示",
]

FAKE_CASUAL_FILLER = [
    "今天聊聊",
    "分享一个",
    "有个很有意思的",
    "说实话",
    "其实",
    "我读了",
    "我发现",
    "我看了",
]

ABSTRACT_NOUNS = [
    "时代",
    "技术",
    "系统",
    "权力",
    "价值",
    "秩序",
    "文明",
    "风险",
    "伦理",
    "治理",
    "结构",
    "机制",
    "定义",
    "判断",
]

CONCRETE_ANCHORS = [
    "人",
    "公司",
    "平台",
    "学校",
    "医院",
    "简历",
    "拒信",
    "贷款",
    "保险",
    "手机",
    "账号",
    "教皇",
    "巴别塔",
    "发布",
    "现场",
    "房间",
    "战争",
    "模型",
]


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def count_hits(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


def has_concrete(text: str) -> bool:
    return any(anchor in text for anchor in CONCRETE_ANCHORS)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    body = "\n\n".join(paras)

    pulpit_hits = count_hits(body, PULPIT_PHRASES)
    if len(pulpit_hits) >= 3:
        failures.append("pulpit phrase cluster: " + "、".join(pulpit_hits[:10]))
    elif pulpit_hits:
        warnings.append("pulpit phrases present: " + "、".join(pulpit_hits[:10]))

    fake_casual_hits = count_hits(body, FAKE_CASUAL_FILLER)
    if len(fake_casual_hits) >= 3:
        failures.append("fake-casual filler cluster: " + "、".join(fake_casual_hits[:10]))
    elif fake_casual_hits:
        warnings.append("fake-casual filler present: " + "、".join(fake_casual_hits[:10]))

    if paras:
        early = "\n\n".join(paras[:8])
        abstract_count = sum(early.count(word) for word in ABSTRACT_NOUNS)
        concrete_count = sum(early.count(word) for word in CONCRETE_ANCHORS)
        if chinese_len(early) >= 450 and abstract_count >= 18 and concrete_count < 8:
            failures.append(
                f"early section is abstract-heavy before concrete scenes: abstract={abstract_count}, concrete={concrete_count}"
            )

    abstract_runs = 0
    max_abstract_runs = 0
    for para in paras:
        abstract_count = sum(para.count(word) for word in ABSTRACT_NOUNS)
        concrete = has_concrete(para)
        if chinese_len(para) >= 35 and abstract_count >= 4 and not concrete:
            abstract_runs += 1
            max_abstract_runs = max(max_abstract_runs, abstract_runs)
        else:
            abstract_runs = 0
    if max_abstract_runs >= 2:
        failures.append("consecutive abstract paragraphs without concrete anchors")

    long_formal = []
    for index, para in enumerate(paras, 1):
        comma_like = len(re.findall(r"[，；、]", para))
        abstract_count = sum(para.count(word) for word in ABSTRACT_NOUNS)
        if chinese_len(para) > 170 and comma_like >= 8 and abstract_count >= 6:
            long_formal.append(index)
    if long_formal:
        warnings.append("long formal paragraphs: " + "、".join(map(str, long_formal[:8])))

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
