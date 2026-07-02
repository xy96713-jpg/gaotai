#!/usr/bin/env python3
"""Build writing packets for local projects without forcing a pain-point frame."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / ".cache" / "writing" / "project_story_packs"

IGNORED_DIRS = {
    ".cache",
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
}


@dataclass(frozen=True)
class MotivationRoute:
    key: str
    label: str
    description: str
    keywords: tuple[str, ...]


ROUTES: tuple[MotivationRoute, ...] = (
    MotivationRoute(
        key="curiosity",
        label="好奇 / 好玩",
        description="先承认它是因为有趣、想试、觉得酷才开始，不急着包装成痛点。",
        keywords=("酷", "好玩", "有趣", "想试", "灵感", "突然", "脑洞", "玩一下", "curious", "fun", "cool"),
    ),
    MotivationRoute(
        key="aesthetic",
        label="审美 / 手感",
        description="从视觉、交互、质感、产品手感进入，重点写为什么这个感觉值得做。",
        keywords=("视觉", "design", "ui", "重设", "手感", "好看", "不土", "不廉价", "质感", "风格", "product design"),
    ),
    MotivationRoute(
        key="experiment",
        label="实验 / 验证",
        description="把项目写成一次实验：假设是什么、怎么试、试出了什么边界。",
        keywords=("研究", "对比", "方案", "验证", "测试", "实验", "prototype", "poc", "remotion", "hyperframes", "ar"),
    ),
    MotivationRoute(
        key="problem",
        label="问题 / 改进",
        description="确实有痛点、卡点、效率问题时，再走问题到方案的叙事。",
        keywords=("必要性", "技巧", "整理", "自动化", "bug", "卡住", "问题", "痛点", "不好用", "解决", "修复"),
    ),
    MotivationRoute(
        key="showcase",
        label="作品 / 展示",
        description="把它写成作品展示：最抓人的画面、关键能力、完成后的样子。",
        keywords=("作品", "展示", "demo", "动画", "粒子", "面具", "特效", "showcase"),
    ),
    MotivationRoute(
        key="business_validation",
        label="商业 / 需求验证",
        description="当项目关乎用户、转化、市场或业务判断时，写验证逻辑和取舍。",
        keywords=("商业", "转化", "用户", "产品", "增长", "需求", "市场", "留存"),
    ),
)


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "project"


def _count_keyword_hits(haystack: str, keywords: tuple[str, ...]) -> int:
    lowered = haystack.lower()
    score = 0
    for keyword in keywords:
        score += lowered.count(keyword.lower())
    return score


def classify_project_motivation(name: str, notes: str = "", path_summary: str = "") -> dict[str, Any]:
    haystack = "\n".join(part for part in (name, notes, path_summary) if part)
    scored: list[dict[str, Any]] = []
    for route in ROUTES:
        score = _count_keyword_hits(haystack, route.keywords)
        scored.append(
            {
                "key": route.key,
                "label": route.label,
                "description": route.description,
                "score": score,
            }
        )

    scored.sort(key=lambda item: (-int(item["score"]), item["label"]))
    primary = scored[0]
    if int(primary["score"]) <= 0:
        primary = next(item for item in scored if item["key"] == "curiosity")

    # If a project says "cool/fun/interesting" and also mentions a solution word,
    # preserve the playful route instead of forcing problem-solution copy.
    curiosity = next(item for item in scored if item["key"] == "curiosity")
    problem = next(item for item in scored if item["key"] == "problem")
    if int(curiosity["score"]) > 0 and int(problem["score"]) <= int(curiosity["score"]) + 1:
        primary = curiosity

    return {
        "primary": primary,
        "candidates": scored,
        "antiForcedPainPoint": primary["key"] != "problem",
    }


def inspect_project_path(path_value: str | Path | None) -> dict[str, Any]:
    if not path_value:
        return {"exists": False, "path": "", "files": [], "signals": [], "gitLog": []}
    path = Path(path_value).expanduser()
    if not path.exists():
        return {"exists": False, "path": str(path), "files": [], "signals": ["路径不存在"], "gitLog": []}

    base = path if path.is_dir() else path.parent
    files: list[str] = []
    signals: list[str] = []
    for file_path in base.rglob("*"):
        if len(files) >= 80:
            break
        rel = file_path.relative_to(base)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if file_path.is_file():
            rel_text = str(rel)
            files.append(rel_text)
            lowered = rel_text.lower()
            if lowered in {"readme.md", "agents.md", "package.json", "product.md", "design.md", "handoff.md"}:
                signals.append(f"有项目说明：{rel_text}")
            if lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov")):
                signals.append(f"有可展示素材：{rel_text}")

    git_log: list[str] = []
    try:
        completed = subprocess.run(
            ["git", "-C", str(base), "log", "--oneline", "-5"],
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
        if completed.returncode == 0:
            git_log = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    except Exception:
        git_log = []

    return {
        "exists": True,
        "path": str(base),
        "files": files,
        "signals": sorted(set(signals))[:20],
        "gitLog": git_log,
    }


def _project_card_questions(route: dict[str, Any]) -> list[str]:
    common = [
        "项目最开始为什么想做？",
        "第一眼想做出什么感觉？",
        "现在已经做到了哪一步？",
        "最有展示价值的一幕是什么？",
        "最意外或最失败的一版是什么？",
    ]
    route_key = route.get("key")
    if route_key == "problem":
        return common + ["它原来卡住了谁的什么动作？", "用项目后这个动作具体变轻了哪里？"]
    if route_key == "aesthetic":
        return common + ["它和普通版本的视觉/手感差在哪里？", "哪个细节最能说明审美判断？"]
    if route_key == "experiment":
        return common + ["这次实验想验证什么？", "结果推翻或保留了哪个假设？"]
    if route_key == "showcase":
        return common + ["观众第一眼应该看见什么？", "它最适合用截图、录屏还是对比图展示？"]
    if route_key == "business_validation":
        return common + ["它验证的是用户、转化、需求还是价格？", "现在最不能夸大的指标是什么？"]
    return common + ["它酷在哪里？", "它只是好玩也成立吗？为什么？"]


def _writing_angles(route: dict[str, Any]) -> list[str]:
    route_key = route.get("key")
    if route_key == "problem":
        return ["真实卡点复盘", "解决路径拆解", "改前改后对比"]
    if route_key == "aesthetic":
        return ["审美重设故事", "一个细节如何改变手感", "失败版到可用版的视觉复盘"]
    if route_key == "experiment":
        return ["一次实验的假设和结果", "工具/方案对比", "边界和踩坑记录"]
    if route_key == "showcase":
        return ["作品展示稿", "幕后制作过程", "一个效果为什么成立"]
    if route_key == "business_validation":
        return ["需求验证记录", "用户判断与误判", "商业假设复盘"]
    return ["为什么我就是想做这个", "从觉得酷到做出第一版", "好玩项目也能留下什么方法"]


def _format_list(items: list[str], empty: str = "暂无。") -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def build_project_story_pack(
    name: str,
    path: str | Path | None = "",
    notes: str = "",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    clean_name = name.strip() or "未命名项目"
    inspection = inspect_project_path(path)
    path_summary = "\n".join([*(inspection.get("signals") or []), *(inspection.get("files") or [])[:20]])
    classification = classify_project_motivation(clean_name, notes, path_summary)
    primary = classification["primary"]
    slug = slugify(clean_name)
    angles = _writing_angles(primary)
    questions = _project_card_questions(primary)

    markdown = f"""# 项目写作包：{clean_name}

## 动机路由
- 主路由：{primary["label"]}
- 判断：{primary["description"]}
- 不强行写成痛点叙事：{"是" if classification["antiForcedPainPoint"] else "否，这个项目确实有明确问题/改进对象。"}

## 项目卡
- 项目名：{clean_name}
- 项目路径：{inspection.get("path") or "未提供"}
- 原始备注：{notes.strip() or "未提供。"}
- 当前材料信号：
{_format_list(inspection.get("signals") or [])}

## 需要补齐的问题
{_format_list(questions)}

## 可写方向
{_format_list([f"{index}. {angle}" for index, angle in enumerate(angles, 1)])}

## Kimi 主笔 Brief
请把这个项目写成一篇中文个人 IP 内容。不要默认套“痛点-方案-结果”。

主路由是：{primary["label"]}。

写作重点：
- 先承认真实动机：它可能是因为酷、好玩、想试、审美、实验，也可能是问题驱动。
- 先写项目为什么值得看，再写它解决了什么。
- 如果没有用户数据、商业结果、真实反馈，不要编。
- 至少保留一个具体画面、一个失败/意外、一个现在能展示的结果。

## Codex 审稿门槛
- 如果没有明确痛点，不准硬写成“我发现一个问题，所以做了一个工具”。
- 每段必须有项目对象、动作或画面，不能只讲方法论。
- 必须区分：好奇、审美、实验、问题、作品、商业验证。
- 没有材料时，标记缺口，不要补成看起来完整的故事。

## 可用材料
### 文件线索
{_format_list(inspection.get("files") or [])}

### 最近 Git 记录
{_format_list(inspection.get("gitLog") or [])}
"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    md_path = output_path / f"{slug}_project_story_pack.md"
    json_path = output_path / f"{slug}_project_story_pack.json"
    result = {
        "ok": True,
        "slug": slug,
        "name": clean_name,
        "classification": classification,
        "primaryRoute": primary,
        "angles": angles,
        "questions": questions,
        "inspection": inspection,
        "markdown": markdown,
        "markdownPath": str(md_path),
        "jsonPath": str(json_path),
    }
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a project writing packet.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--path", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = build_project_story_pack(args.name, path=args.path, notes=args.notes, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["markdown"])
        print(f"\nSaved: {result['markdownPath']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
