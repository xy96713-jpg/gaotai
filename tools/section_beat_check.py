#!/usr/bin/env python3
"""Check whether article sections move through different editorial jobs."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


ABSTRACT_WORDS = ("时代", "系统", "技术", "权力", "价值", "秩序", "文明", "风险", "伦理", "治理", "机制")
SOURCE_WORDS = ("通谕", "报告", "原文", "来源", "Vatican", "AP", "研究", "论文", "数据", "Forbes", "Nature", "《福布斯》", "《自然》", "调查", "采访", "美国国家经济研究局", "布鲁金斯", "政策简报", "公共讨论")
SCENE_WORDS = ("现场", "房间", "简历", "拒信", "医院", "学校", "平台", "按钮", "邮件", "一个人", "手机", "孩子", "角色", "消息", "同学", "家人", "老师")
MECHANISM_WORDS = ("流程", "部署", "训练", "筛选", "评分", "排序", "推荐", "画像", "风控", "模型", "留存", "依赖", "护栏", "增长", "审核", "退出成本")
OBJECTION_WORDS = ("误会", "反驳", "不是", "不能说", "不必", "质疑", "读者")
JUDGMENT_WORDS = ("我", "对我", "我的", "判断", "负责", "该", "需要", "不能")
IMAGE_WORDS = ("巴别塔", "耶路撒冷", "塔", "城", "墙", "废墟", "修城", "召回", "药品", "汽车", "医疗设备")
ENDING_WORDS = ("最后", "结尾", "工具照样用", "为什么")


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("#")]


def contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def beat_job(paragraph: str) -> str:
    if contains_any(paragraph, ("Forbes", "Nature", "《福布斯》", "《自然》", "Stanford", "Anthropic", "NBER", "Wiley", "Wharton", "美国国家经济研究局")):
        return "source"
    if contains_any(paragraph, SCENE_WORDS):
        return "scene"
    if contains_any(paragraph, IMAGE_WORDS):
        return "image"
    if contains_any(paragraph, SOURCE_WORDS):
        return "source"
    if contains_any(paragraph, MECHANISM_WORDS):
        return "mechanism"
    if contains_any(paragraph, OBJECTION_WORDS):
        return "objection"
    if contains_any(paragraph, JUDGMENT_WORDS):
        return "judgment"
    if contains_any(paragraph, ENDING_WORDS) and chinese_len(paragraph) < 100:
        return "landing"
    if sum(paragraph.count(word) for word in ABSTRACT_WORDS) >= 3:
        return "abstract"
    return "bridge"


def audit(text: str) -> tuple[list[str], list[str], list[tuple[int, str, str]]]:
    paras = paragraphs(text)
    failures: list[str] = []
    warnings: list[str] = []
    board: list[tuple[int, str, str]] = []

    if len(paras) < 6:
        failures.append(f"too few paragraphs for serious beat check: {len(paras)}")

    jobs: list[str] = []
    for index, para in enumerate(paras, 1):
        job = beat_job(para)
        jobs.append(job)
        preview = re.sub(r"\s+", " ", para)[:80]
        board.append((index, job, preview))

    for index in range(len(jobs) - 2):
        window = jobs[index : index + 3]
        if len(set(window)) == 1 and window[0] in {"abstract", "mechanism", "source", "bridge"}:
            failures.append(f"three consecutive paragraphs have same low-movement job `{window[0]}` at {index + 1}-{index + 3}")

    counts = Counter(jobs)
    if counts.get("scene", 0) == 0:
        failures.append("no scene/example beat found")
    if counts.get("mechanism", 0) == 0:
        failures.append("no mechanism beat found")
    if counts.get("objection", 0) == 0:
        warnings.append("no explicit objection/correction beat found")
    if counts.get("judgment", 0) == 0:
        failures.append("no personal/editorial judgment beat found")
    if counts.get("landing", 0) == 0:
        warnings.append("no compact landing beat detected")

    source_or_image = counts.get("source", 0) + counts.get("image", 0)
    if source_or_image == 0:
        failures.append("no source/image pressure beat found")

    if counts:
        dominant, amount = counts.most_common(1)[0]
        if amount / max(len(jobs), 1) > 0.45:
            warnings.append(f"dominant beat `{dominant}` takes {amount}/{len(jobs)} paragraphs")

    return failures, warnings, board


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--board-output", type=Path, help="Optional Markdown beat board output path.")
    args = parser.parse_args()

    text = args.draft.read_text(encoding="utf-8", errors="replace")
    failures, warnings, board = audit(text)

    if args.board_output:
        lines = ["# Section Beat Board", "", "| # | Job | Preview |", "|---:|---|---|"]
        for index, job, preview in board:
            safe_preview = preview.replace("|", "\\|")
            lines.append(f"| {index} | {job} | {safe_preview} |")
        args.board_output.parent.mkdir(parents=True, exist_ok=True)
        args.board_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("PASS" if not failures else "FAIL")
    for failure in failures:
        print(f"- FAIL: {failure}")
    for warning in warnings:
        print(f"- WARN: {warning}")
    if board:
        print("## Beat Board")
        for index, job, preview in board[:40]:
            print(f"- {index:02d} {job}: {preview}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
