#!/usr/bin/env python3
"""Block low-grade first-line hooks in Chinese personal-IP drafts.

This gate catches openings that have enough "substance" to pass structural
checks but still sound cheap: fake contrast, tech-blog setup, empty cleverness,
and first-sentence abstractions that explain before entering a scene.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CHEAP_FIRST_LINE_PATTERNS = [
    (r"有些.*(产品|软件|工具|AI|人工智能).*?(坏|出问题).*不是.*(闪退|报错|宕机|崩溃)", "cheap tech-product contrast"),
    (r"不是.*(闪退|报错|宕机|崩溃).*也不是", "cheap negative-parallel tech contrast"),
    (r"你有没有想过", "generic question hook"),
    (r"如果我告诉你", "clickbait conditional hook"),
    (r"很多人以为", "generic crowd setup"),
    (r"真正(值得警惕|有意思|重要|关键)", "fake-depth opener"),
    (r"最(吓人|可怕|危险|麻烦)的.*不是", "cheap superlative inversion"),
    (r"这个(题目|选题|问题).*", "meta-topic opener"),
    (r".*背后的逻辑", "abstract logic opener"),
    (r".*不是.{0,30}而是", "binary-depth aphorism"),
    (r".*不在于.{0,30}在于", "binary-depth aphorism"),
    (r".*难的不是.{0,30}难的是", "binary-depth aphorism"),
    (r".*真正要(争|问|看|解决|面对)的", "binary-depth aphorism"),
    (r".*真正(的问题|的关键|的麻烦|要争|要问|要看)", "binary-depth aphorism"),
    (r".*瞄准的不是.{0,30}而是", "binary-depth aphorism"),
    (r".*一次体验.{0,18}持续使用", "binary-depth aphorism"),
    (r".*看[的得]就是后者", "binary-depth aphorism"),
]

CHEAP_OPENING_BLOCK_PATTERNS = [
    (r"不是.{0,18}，也不是.{0,18}。?\s*\n+\s*(而是|它只是)", "stacked negative setup"),
    (r"看似.{0,30}实则", "formulaic contrast"),
    (r"从来都不是.{0,40}而是", "grand formulaic inversion"),
    (r"问题不在.{0,40}而在", "formulaic thesis opening"),
    (r"不是.{0,40}而是", "binary-depth aphorism"),
    (r"难的不是.{0,40}难的是", "binary-depth aphorism"),
    (r"真正要(争|问|看|解决|面对)的", "binary-depth aphorism"),
    (r"一次体验.{0,30}持续使用", "binary-depth aphorism"),
]

REQUIRED_SCENE_MARKERS = [
    "你",
    "我",
    "他",
    "她",
    "用户",
    "孩子",
    "手机",
    "窗口",
    "消息",
    "对话",
    "房间",
    "现场",
    "文件",
    "报告",
    "会议",
    "打开",
    "看到",
    "收到",
    "发",
    "回",
    "改",
    "变",
]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def clean_line(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def first_sentence(paragraph: str) -> str:
    parts = re.split(r"(?<=[。！？!?])", paragraph.strip(), maxsplit=1)
    return clean_line(parts[0]) if parts else clean_line(paragraph)


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def count_markers(text: str, markers: list[str]) -> int:
    return sum(1 for marker in markers if marker in text)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    if not paras:
        return ["no opening paragraphs found"], warnings

    first = first_sentence(paras[0])
    opening_block = "\n\n".join(paras[:4])

    for pattern, reason in CHEAP_FIRST_LINE_PATTERNS:
        if re.search(pattern, first):
            failures.append(f"first line uses {reason}: `{first}`")

    for pattern, reason in CHEAP_OPENING_BLOCK_PATTERNS:
        if re.search(pattern, opening_block):
            failures.append(f"opening block uses {reason}: `{pattern}`")

    if chinese_len(first) <= 18 and count_markers(first, REQUIRED_SCENE_MARKERS) == 0:
        warnings.append(f"short first line has no scene/action marker: `{first}`")

    if "不是" in first and "而是" in first and count_markers(first, REQUIRED_SCENE_MARKERS) < 2:
        failures.append(f"first line relies on abstract negative parallelism: `{first}`")

    if count_markers("\n".join(paras[:3]), REQUIRED_SCENE_MARKERS) < 3:
        warnings.append("first three paragraphs may still be under-scened; add person/object/action before explanation")

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
