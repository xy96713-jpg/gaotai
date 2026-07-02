#!/usr/bin/env python3
"""Check whether a title or opening has communication anchors.

The gate is intentionally simple. It prevents abstract "deep" titles from
replacing a concrete hook. A strong source-based title/opening should carry:
who, action, conflict, and image/object.
"""

from __future__ import annotations

import re
import sys


WHO_PATTERNS = [
    r"教皇",
    r"Leo\s*XIV",
    r"梵蒂冈",
    r"公司",
    r"OpenAI",
    r"Anthropic",
    r"学者",
    r"投资人",
    r"创业者",
    r"平台",
    r"医生|老师|员工|老板|创作者|博主|用户|你|我|普通人",
]

ACTION_PATTERNS = [
    r"警告",
    r"写给",
    r"发布",
    r"下架",
    r"起诉",
    r"宣布",
    r"拒绝",
    r"押注",
    r"转向",
    r"禁止",
    r"决定",
    r"提醒",
    r"质疑",
    r"回应",
    r"写",
    r"问",
    r"丢给",
    r"交给",
    r"查错",
    r"复核",
    r"判断",
    r"整理",
    r"对照",
    r"看",
    r"签字",
    r"验",
    r"发给",
    r"点开",
    r"回消息",
    r"开口",
]

CONFLICT_PATTERNS = [
    r"AI\s*时代",
    r"最后警告",
    r"为什么",
    r"会不会",
    r"不是.*而是",
    r"却",
    r"反而",
    r"正在",
    r"权力|责任|尊严|战争|劳动|真相|焦虑|风险|信任|套话|漏洞|证据|顺不等于能用|难的是|麻烦|看错|答错",
]

IMAGE_PATTERNS = [
    r"巴别塔",
    r"耶路撒冷",
    r"塔",
    r"城",
    r"房间",
    r"通谕",
    r"模型",
    r"聊天框",
    r"AI\s*伴侣",
    r"分数",
    r"评分",
    r"推荐",
    r"战场",
    r"简历",
    r"门票",
    r"判决",
    r"prompt",
    r"提示词",
    r"报告",
    r"稿子",
    r"合同",
    r"会议纪要",
    r"邮件",
    r"论文",
    r"代码",
]


def hit(patterns: list[str], text: str) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.I)]


def check(text: str) -> tuple[bool, dict[str, list[str]]]:
    results = {
        "who": hit(WHO_PATTERNS, text),
        "action": hit(ACTION_PATTERNS, text),
        "conflict": hit(CONFLICT_PATTERNS, text),
        "image": hit(IMAGE_PATTERNS, text),
    }
    score = sum(1 for values in results.values() if values)
    return score >= 3, results


def main() -> int:
    lines = sys.argv[1:] or [line.strip() for line in sys.stdin if line.strip()]
    if not lines:
        print("usage: communication_anchor_gate.py <title-or-opening> [...]", file=sys.stderr)
        return 2
    failed = False
    for line in lines:
        ok, results = check(line)
        status = "PASS" if ok else "FAIL"
        present = [key for key, values in results.items() if values]
        missing = [key for key, values in results.items() if not values]
        print(f"{status}\t{line}")
        print(f"  - present: {', '.join(present) or 'none'}")
        if missing:
            print(f"  - missing: {', '.join(missing)}")
        failed = failed or not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
