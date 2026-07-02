#!/usr/bin/env python3
"""Audit prose that sounds childish, classroom-like, or mechanically explanatory.

This is a bottom gate for the user's Chinese personal-IP drafts. It does not
judge whether a piece is beautiful. It catches patterns that repeatedly made
drafts feel like school essays: topic-introduction openings, safe binaries,
source-navigation prose, and self-important explanation without scene or motive.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HARD_PATTERNS: list[tuple[str, str]] = [
    ("classroom topic opener", r"通常是在告诉世界"),
    ("empty importance marker", r"这个选择本身"),
    ("fake sharpness marker", r"锋利的地方就在这里"),
    ("fake sharpness marker", r"刺人的地方"),
    ("fake sharpness marker", r"真正锋利"),
    ("safe binary", r"乐观一点看[\s\S]{0,80}悲观一点看"),
    ("source navigation", r"紧接着[，,]?\s*原文"),
    ("source navigation", r"原文转向"),
    ("fake cinematic transition", r"画面换了"),
    ("fake cinematic transition", r"镜头一转"),
    ("director note", r"（[^）]{0,80}(视频开场|画面|镜头|混剪|字幕|B-roll|配图|切入|切到)[^）]{0,80}）"),
    ("director note", r"\([^)]{0,80}(视频开场|画面|镜头|混剪|字幕|B-roll|配图|切入|切到)[^)]{0,80}\)"),
    ("director note", r"(视频开场|画面可以是|镜头切入|镜头切到|快节奏.*混剪|字幕打出|B-roll|配图建议)"),
    ("school-essay conclusion", r"这个比喻告诉我们"),
    ("school-essay conclusion", r"这给我们的启示"),
    ("generic topic intro", r"随着[\s\S]{0,12}的发展"),
    ("generic topic intro", r"在当今时代"),
    ("self-entry filler", r"我读了"),
    ("self-entry filler", r"我看了"),
    ("self-entry filler", r"我发现"),
    ("binary-depth aphorism", r"不是[\s\S]{0,35}而是"),
    ("binary-depth aphorism", r"不在于[\s\S]{0,35}在于"),
    ("binary-depth aphorism", r"难的不是[\s\S]{0,35}难的是"),
    ("binary-depth aphorism", r"真正要(争|问|看|解决|面对)的"),
    ("binary-depth aphorism", r"真正(要争|要问|要看|的问题|的关键|的麻烦)"),
    ("binary-depth aphorism", r"瞄准的不是[\s\S]{0,35}而是"),
    ("binary-depth aphorism", r"一次体验[\s\S]{0,20}持续使用"),
    ("binary-depth aphorism", r"看[的得]就是后者"),
]

SOFT_PATTERNS: list[tuple[str, str]] = [
    ("formula turn", r"也正因为这样"),
    ("formula turn", r"也就是说"),
    ("formula turn", r"换句话说"),
    ("formula turn", r"某种意义上"),
    ("formula turn", r"从这个角度看"),
    ("fake depth", r"本质上"),
    ("fake depth", r"真正的问题"),
    ("fake depth", r"核心问题"),
    ("soft landing", r"麻烦就在这里"),
    ("overbalanced structure", r"一方面[\s\S]{0,120}另一方面"),
    ("overused contrast frame", r"不只是[\s\S]{0,80}更是"),
    ("binary-depth residue", r"核心不是[\s\S]{0,50}而是"),
    ("binary-depth residue", r"重点不是[\s\S]{0,50}而是"),
    ("binary-depth residue", r"关键不是[\s\S]{0,50}而是"),
]

CONCRETE_ANCHORS = [
    "教皇",
    "Anthropic",
    "Olah",
    "梵蒂冈",
    "发布会",
    "巴别塔",
    "耶路撒冷",
    "公司",
    "模型",
    "学校",
    "医院",
    "战场",
    "招聘",
    "贷款",
    "平台",
    "数据",
]

ABSTRACT_WORDS = [
    "时代",
    "系统",
    "价值",
    "秩序",
    "权力",
    "文明",
    "风险",
    "技术",
    "伦理",
    "治理",
    "定义",
    "结构",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def hits(patterns: list[tuple[str, str]], text: str) -> list[str]:
    found: list[str] = []
    for label, pattern in patterns:
        if re.search(pattern, text):
            found.append(f"{label}:{pattern}")
    return found


def first_sentence(text: str) -> str:
    cleaned = re.sub(r"^#+\s*.*$", "", text, flags=re.M).strip()
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[。！？!?])\s*", cleaned, maxsplit=1)
    return parts[0].strip()


def concrete_count(text: str) -> int:
    return sum(1 for word in CONCRETE_ANCHORS if word in text)


def abstract_count(text: str) -> int:
    return sum(1 for word in ABSTRACT_WORDS if word in text)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    hard = hits(HARD_PATTERNS, text)
    if hard:
        failures.append("juvenile/classroom patterns: " + "、".join(hard[:10]))

    soft = hits(SOFT_PATTERNS, text)
    if len(soft) >= 3:
        warnings.append("many formulaic explanatory turns: " + "、".join(soft[:10]))
    elif soft:
        warnings.append("suspect explanatory turns: " + "、".join(soft[:6]))

    opening = first_sentence(text)
    if opening:
        if concrete_count(opening) == 0 and abstract_count(opening) >= 2 and chinese_len(opening) >= 18:
            failures.append("opening starts from abstract topic rather than person/scene/decision")
        if concrete_count(opening) == 0 and re.search(r"^.{0,8}(AI|人工智能).{0,12}(时代|技术|风险|机会)", opening):
            failures.append("opening is topic framing, not article entry")

    paras = paragraphs(text)
    if len(paras) >= 5:
        short_explainers = 0
        for para in paras[:6]:
            if re.match(r"^(这|所以|但|而|问题在于|关键在于|换句话说|也就是说)", para):
                short_explainers += 1
        if short_explainers >= 4:
            warnings.append("early paragraphs lean on explanatory starts instead of movement")

    # If a draft names institutions but never gives a pressure verb, it tends to
    # read like a report rather than a mature article.
    if any(name in text for name in ("教皇", "Anthropic", "梵蒂冈")):
        pressure_words = ["需要", "试图", "避免", "证明", "承认", "回避", "争取", "警告", "约束", "借用"]
        if sum(1 for word in pressure_words if word in text) < 2:
            warnings.append("named actors appear without enough motive or pressure verbs")

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
