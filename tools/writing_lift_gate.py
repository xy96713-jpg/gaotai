#!/usr/bin/env python3
"""Gate whether a writing-workflow piece actually demonstrates quality lift.

This is for articles/videos about the user's own writing skill, SOP, or AI
writing workflow. It blocks drafts that only describe process without proving
why the process makes the writing better.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FAILURE_MARKERS = [
    "发不出去",
    "骗过",
    "失望",
    "退稿",
    "站不住",
    "不好",
    "无聊",
    "像新闻稿",
    "像摘要",
    "套话",
]

BEFORE_AFTER_MARKERS = [
    "以前",
    "现在",
    "后来",
    "原来",
    "改完",
    "直接让",
    "这套",
    "之后",
    "变化",
    "对比",
]

SYSTEM_DETAIL_MARKERS = [
    "资料卡",
    "角度卡",
    "开头卡",
    "反方卡",
    "节奏卡",
    "source map",
    "来源地图",
    "坏句",
    "口播",
    "门槛",
    "审计",
    "退稿",
    "拦截",
]

CONCRETE_FAILURE_OPENING_MARKERS = [
    "第一屏",
    "标题",
    "段落",
    "总结",
    "删除键",
    "删哪一句",
    "套话",
    "初稿",
    "发不出去",
    "不知道该从哪里开始改",
]

RESEARCH_BRIDGE_MARKERS = [
    "为什么",
    "原因",
    "模型",
    "主流",
    "STORM",
    "PaperDebugger",
    "CoAuthor",
    "写作工作流",
    "提示词",
]

DEMO_MARKERS = [
    "比如",
    "举个",
    "拿",
    "用",
    "教皇",
    "巴别塔",
    "报告",
    "视频",
    "论文",
    "旧稿",
    "这一题",
    "这篇",
]

BEFORE_AFTER_DEMO_MARKERS = [
    "原稿",
    "原句",
    "改后",
    "改成",
    "之前",
    "之后",
    "第一版",
    "第二版",
    "旧稿",
    "新稿",
    "被拦下",
    "退回",
    "这一版",
    "对照",
]

READER_PAYOFF_MARKERS = [
    "你可以",
    "观众",
    "创作者",
    "发出去",
    "少走",
    "避免",
    "判断",
    "拿去用",
    "下次",
    "复用",
]

LISTY_MARKERS = [
    "第一道门",
    "第二道门",
    "第三道门",
    "第四道门",
    "第五道门",
    "第六道门",
    "第一步",
    "第二步",
    "第三步",
    "第四步",
    "第五步",
]


def body_text(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", body_text(text)) if p.strip()]


def count_hits(text: str, markers: list[str]) -> int:
    return sum(text.count(marker) for marker in markers)

def first_marker_paragraph_index(paras: list[str], markers: list[str]) -> int | None:
    for index, para in enumerate(paras):
        if count_hits(para, markers):
            return index
    return None


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    body = body_text(text)
    paras = paragraphs(text)
    opening = "\n".join(paras[:5])

    failure_count = count_hits(body, FAILURE_MARKERS)
    before_after_count = count_hits(body, BEFORE_AFTER_MARKERS)
    system_detail_count = count_hits(body, SYSTEM_DETAIL_MARKERS)
    demo_count = count_hits(body, DEMO_MARKERS)
    before_after_demo_count = count_hits(body, BEFORE_AFTER_DEMO_MARKERS)
    payoff_count = count_hits(body, READER_PAYOFF_MARKERS)
    listy_count = count_hits(body, LISTY_MARKERS)

    if failure_count < 3:
        failures.append("weak origin story: show the failed drafts or specific pain that forced this workflow")
    if before_after_count < 3:
        failures.append("missing before/after contrast: explain what changed after the skill existed")
    if system_detail_count < 5:
        failures.append("workflow is too abstract: name actual gates/cards/scripts or decision points")
    if demo_count < 4:
        failures.append("no operational demo: show one topic or draft passing through the workflow")
    if before_after_demo_count < 3:
        failures.append("no before/after demo: show a bad line, blocked draft, or topic transformed by the workflow")
    if payoff_count < 3:
        failures.append("reader payoff is unclear: say what creators can avoid, do, or reuse")

    if listy_count >= 5 and before_after_demo_count < listy_count:
        failures.append("too list-like: gates are listed more than demonstrated with before/after evidence")
    elif listy_count >= 5:
        warnings.append("many numbered gates; keep only the gates that are demonstrated in action")

    if chinese_len(opening) > 0 and count_hits(opening, CONCRETE_FAILURE_OPENING_MARKERS) < 3:
        failures.append("opening lacks a concrete failed-draft scene before the system appears")

    first_system_index = first_marker_paragraph_index(paras, SYSTEM_DETAIL_MARKERS)
    first_research_index = first_marker_paragraph_index(paras, RESEARCH_BRIDGE_MARKERS)
    if first_system_index is not None and first_system_index <= 2:
        failures.append("system/workbench appears too early: show failure and cause before product mechanics")
    if (
        first_system_index is not None
        and first_research_index is not None
        and first_system_index < first_research_index
    ):
        failures.append("workbench appears before the research/cause bridge")

    abstract_title_like = re.search(r"最(好|靠谱).*方式", text[:120]) and count_hits(body, ["退稿", "审计", "拦截", "门槛"]) < 3
    if abstract_title_like:
        failures.append("title promises best method but the body lacks a concrete mechanism like退稿/审计/拦截")

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
