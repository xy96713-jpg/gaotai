#!/usr/bin/env python3
"""Taste gate for Chinese personal-IP openings and endings.

This gate catches drafts that pass factual/mechanical checks but still feel
flat: thesis-summary titles, over-explained openings, and aphoristic endings.
It is intentionally conservative and should block weak candidates for this
workspace.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


THESIS_TITLE_PATTERNS = [
    r"把.*交给.*，.*留在",
    r"怎么用",
    r"如何使用",
    r"启示",
    r"方法论",
    r"底层逻辑",
]

APHORISM_ENDING_PATTERNS = [
    r"^因为.+时候[。.]?$",
    r"^是.+时候[。.]?$",
    r"^但.+最好.+[。.]?$",
    r"^最后.+还在.+[。.]?$",
    r"^真正.+不是.+而是.+[。.]?$",
]

ABSTRACT_ENDING_PATTERNS = [
    r"(抵抗素养|亲密供给缺口|判断力|边界感|安全感|关系能力|表达能力|修复能力).{0,12}的(日常|起点|答案|出口|落点|落脚处|开始)[。.]?$",
    r"这或许(就)?是.{0,18}的(日常|起点|答案|出口|落点|落脚处|开始)[。.]?$",
    r"这(就|才)?是.{0,18}的(日常|起点|答案|出口|落点|落脚处|开始)[。.]?$",
]

OPENING_META_PATTERNS = [
    "这个数字不能证明",
    "样本也不该被夸大",
    "但它提出了一个更好的问题",
    "答案不在",
    "更像是",
]

OPENING_CLARITY_ANCHORS = [
    "普通人",
    "你",
    "我",
    "写",
    "稿",
    "合同",
    "报告",
    "论文",
    "代码",
    "查",
    "错",
    "结论",
    "工具",
    "prompt",
    "提示词",
    "材料",
    "手机",
    "孩子",
    "产品",
    "软件",
    "消息",
    "聊天",
    "朋友",
    "AI 伴侣",
    "陪伴",
    "关系",
    "孤独",
    "平台",
    "药品",
    "汽车",
]

VAGUE_OPENING_PATTERNS = [
    "最会请人的那群人",
    "那群人",
    "先读材料",
    "材料排队",
    "另一种速度",
]


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return ""


def paragraphs(text: str) -> list[str]:
    result = []
    for raw in re.split(r"\n\s*\n", text):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        result.append(re.sub(r"\s+", " ", stripped))
    return result


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    heading = title(text)
    paras = paragraphs(text)

    if heading:
        for pattern in THESIS_TITLE_PATTERNS:
            if re.search(pattern, heading):
                failures.append(f"title explains the thesis too early or uses formula pattern: `{pattern}`")

    if paras:
        first = paras[0]
        first_len = chinese_len(first)
        opening = "\n".join(paras[:2])
        anchor_count = sum(1 for anchor in OPENING_CLARITY_ANCHORS if anchor in opening)
        if first_len > 95 and "？" not in first and "为什么" not in first:
            failures.append("opening paragraph is long and explanatory before it creates a reader question")
        vague_hits = [pattern for pattern in VAGUE_OPENING_PATTERNS if pattern in opening]
        if vague_hits:
            failures.append("opening uses vague clever phrasing before the reader understands the topic: " + "、".join(vague_hits))
        if anchor_count < 4:
            failures.append("opening is not concrete enough for a cold reader; add ordinary-user pain, object, action, and stakes")
        if "富人" in opening and not any(word in opening for word in ("普通人", "你", "我", "写稿", "报告", "合同", "论文", "代码")):
            failures.append("opening starts with elite category but does not translate why a normal reader should care")
        if sum(1 for phrase in OPENING_META_PATTERNS if phrase in "\n".join(paras[:3])) >= 3:
            failures.append("opening section leans on editorial meta-explanation instead of source pressure")
        if any(name in "\n".join(paras[:2]) for name in ("Forbes", "《福布斯》")) and "富豪" in "\n".join(paras[:2]) and "真人助理" not in "\n".join(paras[:2]):
            warnings.append("Forbes/billionaire hook appears before the human contradiction is vivid enough")

    if len(paras) >= 2:
        last_two = paras[-2:]
        for para in last_two:
            if any(re.search(pattern, para) for pattern in APHORISM_ENDING_PATTERNS):
                failures.append(f"ending uses aphoristic split-line pattern: `{para}`")
            if any(re.search(pattern, para) for pattern in ABSTRACT_ENDING_PATTERNS):
                failures.append(f"ending lands on an abstract concept label instead of concrete speech/action: `{para}`")
        if all(chinese_len(para) <= 28 for para in last_two):
            failures.append("ending relies on two short punchline paragraphs; likely feels like a reusable AI close")
        if "判断" in last_two[-1] and chinese_len(last_two[-1]) <= 24:
            failures.append("ending lands on abstract `判断` instead of a concrete action or unresolved pressure")

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
