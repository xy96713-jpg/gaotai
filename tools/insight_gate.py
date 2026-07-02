#!/usr/bin/env python3
"""Require a draft to contain real insight, not only correct instruction.

An acceptable personal-IP draft should give the viewer at least one durable
idea: a mechanism, a reversal, a cost, a named phenomenon, or a concrete
personal judgment. This gate blocks scripts that only list steps.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NAMING_MARKERS = [
    "叫",
    "称为",
    "workslop",
    "工作废稿",
    "验证差",
    "平均答案",
    "坏句",
    "AI 味",
    "判断库",
    "反例库",
    "安全词",
    "判断缺位",
    "空洞感",
]

MECHANISM_MARKERS = [
    "根源",
    "来源",
    "因为",
    "所以",
    "模型",
    "公共语料",
    "最大公约数",
    "没有人负责",
    "无人负责",
    "缺少",
    "责任",
    "上下文",
    "反馈",
    "审计",
    "退稿",
    "命中",
    "上下文",
    "具体动作",
    "具体后果",
    "风格库",
]

REVERSAL_MARKERS = [
    "不是",
    "不在",
    "反而",
    "却",
    "看起来",
    "表面",
    "真正",
    "问题不在",
    "问题不是",
]

COST_MARKERS = [
    "代价",
    "成本",
    "浪费",
    "返工",
    "废稿",
    "重复",
    "抽奖",
    "救火",
    "从零起跑",
    "靠运气",
    "塌腰",
    "忘了",
    "忘记",
    "越来越长",
    "越来越重",
    "误判",
    "焦虑",
    "带偏",
    "外包",
    "转嫁",
    "没有推进",
    "看不下去",
    "打转",
    "省时间",
    "一上午",
    "挪不到",
    "费事",
    "从零开始",
    "从头审",
    "免费校对",
]

PERSONAL_JUDGMENT_MARKERS = [
    "我现在",
    "我判断",
    "我会",
    "我更愿意",
    "对我",
    "我的",
    "我自己",
    "这期",
    "这个频道",
    "我反对",
    "我保留",
    "我删掉",
]

EXAMPLE_MARKERS = [
    "比如",
    "例如",
    "合同",
    "体检报告",
    "论文",
    "周报",
    "老板",
    "评论区",
    "旧稿",
    "坏句",
    "开头",
]

INSTRUCTION_MARKERS = [
    "第一步",
    "第二步",
    "第三步",
    "第四步",
    "第五步",
    "第六步",
    "先",
    "再",
    "最后",
    "要",
    "不要",
    "流程",
    "方法",
]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def count_hits(text: str, items: list[str]) -> int:
    return sum(1 for item in items if item in text)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    paras = paragraphs(text)
    body = "\n".join(paras)
    opening_half = "\n".join(paras[: max(6, len(paras) // 2)])

    naming = count_hits(body, NAMING_MARKERS)
    mechanism = count_hits(body, MECHANISM_MARKERS)
    reversal = count_hits(body, REVERSAL_MARKERS)
    cost = count_hits(body, COST_MARKERS)
    personal = count_hits(body, PERSONAL_JUDGMENT_MARKERS)
    examples = count_hits(body, EXAMPLE_MARKERS)
    instructions = count_hits(body, INSTRUCTION_MARKERS)

    insight_score = naming + mechanism + reversal + cost + personal + min(examples, 4)

    if insight_score < 8:
        failures.append(
            f"low insight density: score={insight_score}; needs naming, mechanism, reversal, cost, examples, or personal judgment"
        )

    if instructions >= 8 and (mechanism + cost + personal) < 6:
        failures.append(
            f"too instructional without enough mechanism/cost/judgment: instruction={instructions}"
        )

    if naming == 0:
        warnings.append("no named phenomenon; consider naming the problem instead of only explaining it")

    if cost == 0:
        failures.append("no visible cost or consequence; the draft may feel like harmless advice")

    if personal == 0:
        warnings.append("no personal/editorial judgment marker; may read like a generic explainer")

    if count_hits(opening_half, COST_MARKERS + REVERSAL_MARKERS) < 2:
        warnings.append("the first half may not create enough pressure before advice begins")

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
