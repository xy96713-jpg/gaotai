#!/usr/bin/env python3
"""Block drafts whose article engine is only a topic or tutorial.

The user often rejects drafts that are factually organized but still boring.
This gate checks for the thing those drafts miss: a reader-facing problem,
concrete material, and a reason to keep reading before the article becomes
explanation.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TITLE_READER_TENSION = [
    "为什么",
    "怎么",
    "错",
    "骗",
    "套话",
    "平均答案",
    "写不出",
    "看不懂",
    "站不住",
    "翻车",
    "漏洞",
    "代价",
    "差距",
    "研究员",
]

ORDINARY_READER_ANCHORS = [
    "你",
    "我",
    "普通人",
    "创作者",
    "写稿",
    "稿子",
    "报告",
    "论文",
    "合同",
    "会议纪要",
    "代码",
    "资料",
    "原文",
    "旧稿",
    "prompt",
    "提示词",
    "手机",
    "聊天框",
    "AI 伴侣",
    "朋友",
    "恋人",
    "家人",
    "关系",
    "孩子",
    "产品",
    "软件",
    "消息",
    "聊天",
    "陪伴",
    "关系",
    "孤独",
    "平台",
]

CONCRETE_OBJECTS = [
    "合同",
    "会议纪要",
    "邮件",
    "投资备忘录",
    "市场消息",
    "医疗报告",
    "论文",
    "代码",
    "报告",
    "数据",
    "原文",
    "旧稿",
    "反方",
    "评论",
    "简历",
    "账单",
    "截图",
    "手机",
    "聊天框",
    "AI 伴侣",
    "朋友",
    "恋人",
    "家人",
    "关系",
    "孩子",
    "产品",
    "软件",
    "消息",
    "角色",
    "药品",
    "汽车",
    "医疗设备",
    "平台",
    "模型",
]

ACTION_VERBS = [
    "写",
    "读",
    "问",
    "查",
    "核",
    "改",
    "整理",
    "压缩",
    "对照",
    "挑漏洞",
    "复核",
    "签字",
    "判断",
    "发出去",
    "输入",
    "发",
    "汇报",
    "交给",
    "打开",
    "聊天",
    "回",
    "记住",
    "卸载",
    "留住",
    "召回",
    "改掉",
    "证明",
    "处理",
    "记住",
    "回应",
    "安抚",
    "接住",
    "训练",
    "放大",
    "断开",
    "依赖",
]

VAGUE_GROUPS = [
    "有些人",
    "高手",
    "富人",
    "学者",
    "精英",
    "聪明人",
    "最会",
]

PURE_EXPLAINER_PHRASES = [
    "本质上",
    "核心在于",
    "真正的差别",
    "关键不是",
    "更大的差别",
    "答案可能是",
    "这说明",
    "这意味着",
    "从这个角度",
]

PAYOFF_MARKERS = [
    "没有辨识度",
    "不踏实",
    "站不住",
    "查错",
    "复核",
    "挑漏洞",
    "反方",
    "失败记录",
    "旧稿",
    "判断",
    "签字",
    "退出成本",
    "依赖",
    "断裂感",
    "留存",
    "安全",
    "证明",
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
    return sum(1 for item in items if item in text)


def audit(text: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    heading = title(text)
    paras = paragraphs(text)
    opening = "\n".join(paras[:3])
    first_para = paras[0] if paras else ""
    first_four = "\n".join(paras[:4])

    if not heading:
        failures.append("missing title; cannot test reader-facing engine")
    else:
        title_tension = count_hits(heading, TITLE_READER_TENSION)
        if title_tension < 2:
            failures.append("title lacks reader-facing tension; it names a topic more than a problem")
        vague_title_hits = [item for item in VAGUE_GROUPS if item in heading]
        if "有些人" in heading:
            failures.append("title uses vague comparison subject `有些人`; name the contrast as action instead")
        elif vague_title_hits and not any(item in heading for item in ("你", "我", "普通人", "创作者")):
            failures.append("title relies on distant/vague groups without anchoring the reader: " + "、".join(vague_title_hits))
        if "AI" in heading and count_hits(heading, ORDINARY_READER_ANCHORS) < 1:
            failures.append("AI title does not name the reader's own action or pain")

    if not paras:
        failures.append("no body paragraphs found")
        return failures, warnings

    ordinary_count = count_hits(opening, ORDINARY_READER_ANCHORS)
    object_count = count_hits(first_four, CONCRETE_OBJECTS)
    action_count = count_hits(first_four, ACTION_VERBS)
    payoff_count = count_hits(first_four, PAYOFF_MARKERS)

    if ordinary_count < 3:
        failures.append("opening does not anchor enough ordinary-reader material before explaining")
    if object_count < 3:
        failures.append("first four paragraphs lack concrete objects/materials; add source/doc/workflow objects")
    if action_count < 4:
        failures.append("first four paragraphs lack enough verbs; prose is likely conceptual rather than moving")
    if payoff_count < 2:
        failures.append("opening does not make clear what the reader gains or avoids by reading on")

    pure_explainer_hits = [phrase for phrase in PURE_EXPLAINER_PHRASES if phrase in first_four]
    if len(pure_explainer_hits) >= 2:
        failures.append("opening leans on explainer scaffolding before the article engine earns it: " + "、".join(pure_explainer_hits))
    elif pure_explainer_hits:
        warnings.append("explainer phrases present; make sure they follow concrete material: " + "、".join(pure_explainer_hits))

    if len(first_para) > 80 and object_count < 2:
        failures.append("first paragraph is long before it gives enough concrete material")

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
