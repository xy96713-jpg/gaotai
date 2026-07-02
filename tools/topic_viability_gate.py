#!/usr/bin/env python3
"""Block topics that are likely to become correct but boring drafts.

This gate is intentionally about the article/video idea, not sentence polish.
It catches a recurring failure in this workspace: a draft can pass anti-slop
checks while the underlying topic still only says common advice.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


GENERIC_TOPIC_PATTERNS = [
    r"怎么用\s*AI",
    r"如何用\s*AI",
    r"AI\s*写作",
    r"AI\s*写稿",
    r"提示词",
    r"技巧",
    r"方法",
    r"SOP",
    r"流程",
    r"富人.*学者",
]

COMMON_ADVICE_PATTERNS = [
    "多给材料",
    "先给材料",
    "先读材料",
    "不要太早要正文",
    "要有流程",
    "要有判断",
    "要查错",
    "要批判",
    "要润色",
    "要有个人风格",
    "人机协作",
    "AI 只是工具",
]

NOVELTY_MARKERS = [
    "反而",
    "不是",
    "却",
    "代价",
    "成本",
    "骗",
    "漏洞",
    "外包",
    "转嫁",
    "验证",
    "校验",
    "workslop",
    "工作废稿",
    "验证差",
    "平均答案",
    "没人负责",
    "不值得写",
]

MECHANISM_MARKERS = [
    "因为",
    "来源",
    "根源",
    "机制",
    "模型",
    "公共语料",
    "最大公约数",
    "责任",
    "上下文",
    "流程",
    "反馈",
    "审计",
    "复核",
]

EVIDENCE_MARKERS = [
    "研究",
    "报告",
    "综述",
    "论文",
    "调查",
    "STORM",
    "PaperDebugger",
    "OpenAI",
    "NBER",
    "斯坦福",
    "Frontiers",
    "哈佛商业评论",
    "BetterUp",
    "GitHub",
]

READER_COST_MARKERS = [
    "读者",
    "观众",
    "划走",
    "浪费",
    "返工",
    "误判",
    "焦虑",
    "看不下去",
    "没有推进",
    "废话",
    "套话",
    "站不住",
]


def title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return ""


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def count_hits(text: str, items: list[str]) -> int:
    return sum(1 for item in items if re.search(item, text, flags=re.I))


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    heading = title(text)
    paras = paragraphs(text)
    opening = "\n".join(paras[:6])
    sample = heading + "\n" + opening
    body_start = "\n".join(paras[:12])

    generic_count = count_hits(heading + "\n" + opening, GENERIC_TOPIC_PATTERNS)
    common_count = count_hits(body_start, COMMON_ADVICE_PATTERNS)
    novelty_count = count_hits(sample, NOVELTY_MARKERS)
    mechanism_count = count_hits(body_start, MECHANISM_MARKERS)
    evidence_count = count_hits(body_start, EVIDENCE_MARKERS)
    cost_count = count_hits(sample + "\n" + body_start, READER_COST_MARKERS)

    if generic_count and novelty_count < 2 and cost_count < 2:
        failures.append(
            "generic topic without enough reversal/cost; likely to become correct advice rather than a video/article"
        )

    if common_count >= 4 and novelty_count < 3:
        failures.append(
            f"too much common AI-writing advice before a distinctive claim: common={common_count}, novelty={novelty_count}"
        )

    if evidence_count == 0 and generic_count:
        warnings.append("generic AI-writing topic has no visible source/research pressure in the opening section")

    if mechanism_count < 2 and generic_count:
        failures.append("topic names a workflow but does not expose a mechanism yet")

    if not any(marker in sample for marker in ("为什么", "错", "骗", "代价", "废话", "套话", "漏洞", "不值得写")):
        warnings.append("title/opening may not contain a strong viewer-facing problem")

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
