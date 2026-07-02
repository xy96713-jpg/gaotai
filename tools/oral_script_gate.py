#!/usr/bin/env python3
"""Audit whether a Chinese personal-IP draft can work as a spoken video script."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SOURCE_NAMES = [
    "STORM",
    "PaperDebugger",
    "Frontiers",
    "OpenAI",
    "NBER",
    "GitHub",
    "BetterUp",
    "Anthropic",
    "哈佛商业评论",
    "斯坦福",
]

ORAL_ANCHORS = [
    "你",
    "我",
    "比如",
    "举个",
    "合同",
    "报告",
    "稿子",
    "周报",
    "评论",
    "老板",
    "读者",
    "观众",
]

WRITTEN_ONLY_PHRASES = [
    "本文",
    "如下",
    "综上",
    "由此可见",
    "值得注意的是",
    "从多个维度",
    "进行深入探讨",
]

STAGE_DIRECTION_PATTERNS = [
    r"（[^）]{0,100}(视频开场|画面|镜头|混剪|字幕|B-roll|配图|切入|切到)[^）]{0,100}）",
    r"\([^)]{0,100}(视频开场|画面|镜头|混剪|字幕|B-roll|配图|切入|切到)[^)]{0,100}\)",
    r"视频开场",
    r"画面可以是",
    r"镜头切入",
    r"镜头切到",
    r"快节奏.{0,20}混剪",
    r"字幕打出",
    r"B-roll",
    r"配图建议",
]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[。！？!?]", text) if s.strip()]


def count_hits(text: str, items: list[str]) -> int:
    return sum(text.count(item) for item in items)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    body = "\n".join(paras)
    sents = sentences(body)

    if not paras:
        return ["no script body found"], []

    long_sentences = [(idx + 1, chinese_len(sent), sent[:36]) for idx, sent in enumerate(sents) if chinese_len(sent) > 58]
    if len(long_sentences) >= 3:
        failures.append(
            "too many long spoken sentences: "
            + "；".join(f"{idx}:{length}:{preview}" for idx, length, preview in long_sentences[:5])
        )
    elif long_sentences:
        warnings.append(
            "long spoken sentence(s): "
            + "；".join(f"{idx}:{length}:{preview}" for idx, length, preview in long_sentences[:5])
        )

    dense_paras = [(idx + 1, chinese_len(para)) for idx, para in enumerate(paras) if chinese_len(para) > 180]
    if dense_paras:
        warnings.append("dense oral paragraphs may need pauses: " + "、".join(f"{i}:{n}" for i, n in dense_paras[:6]))

    source_heavy = [idx + 1 for idx, para in enumerate(paras) if count_hits(para, SOURCE_NAMES) >= 3]
    if source_heavy:
        failures.append("too many source names in one spoken paragraph: " + "、".join(map(str, source_heavy[:6])))

    written_hits = [phrase for phrase in WRITTEN_ONLY_PHRASES if phrase in body]
    if written_hits:
        failures.append("written-report phrases in oral script: " + "、".join(written_hits[:8]))

    stage_hits = [pattern for pattern in STAGE_DIRECTION_PATTERNS if re.search(pattern, body)]
    if stage_hits:
        failures.append("director/stage directions should not appear in prose-only scripts: " + "、".join(stage_hits[:6]))

    early = "\n".join(paras[:5])
    if count_hits(early, ORAL_ANCHORS) < 3:
        failures.append("opening lacks spoken anchors like you/I/example/object; viewer may not enter fast enough")

    if len(paras) >= 12:
        tiny_run = 0
        max_tiny_run = 0
        for para in paras:
            if chinese_len(para) <= 16:
                tiny_run += 1
                max_tiny_run = max(max_tiny_run, tiny_run)
            else:
                tiny_run = 0
        if max_tiny_run >= 3:
            warnings.append("three or more tiny paragraphs in a row; may sound like slogan stacking")

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
