#!/usr/bin/env python3
"""Audit the selected-line rewrite routing for the writing workbench.

This catches the failure class where local rewrite heuristics hijack a normal
selected sentence and turn it into workbench/product copy.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import (  # noqa: E402
    build_variants,
    deepseek_rewrite,
    rewrite_selection_response,
)
from tools.style_memory import StyleMemoryStore  # noqa: E402


REPORT_PATH = ROOT / ".cache" / "writing" / "workbench_rewrite_logic_audit_latest.json"
EDITOR_META_RE = re.compile(
    r"候选\s*\d*|编辑点评|短句节奏|适合口播|自然引出|补出读者|动作或结果|source-ground|oralize|concretize|rewrite",
    re.I,
)
WORKBENCH_TERMS = (
    "工作台",
    "Codex",
    "Kimi",
    "DeepSeek",
    "风格库",
    "点“改句”",
    "点“讨厌”",
    "点“喜欢”",
    "选中",
    "右侧",
    "按钮",
)


def compact(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value or ""))


def similarity(left: str, right: str) -> float:
    a = compact(left)
    b = compact(right)
    if not a or not b:
        return 0.0
    counts: dict[str, int] = {}
    for char in a:
        counts[char] = counts.get(char, 0) + 1
    overlap = 0
    for char in b:
        count = counts.get(char, 0)
        if count:
            overlap += 1
            counts[char] = count - 1
    return overlap / max(len(a), len(b))


def assert_article_ready(name: str, selected: str, variants: list[dict[str, Any]], *, min_count: int = 1) -> None:
    texts = [str(item.get("text", "")).strip() for item in variants if str(item.get("text", "")).strip()]
    if len(texts) < min_count:
        raise AssertionError(f"{name}: expected >= {min_count} candidates, got {len(texts)}")
    if len(set(texts)) != len(texts):
        raise AssertionError(f"{name}: duplicate candidate text: {texts}")
    for text in texts:
        if text == selected:
            raise AssertionError(f"{name}: unchanged candidate: {text}")
        if selected and selected in text and len(text) <= len(selected) + 18:
            raise AssertionError(f"{name}: candidate only wraps selected text: {text}")
        if similarity(text, selected) >= 0.95:
            raise AssertionError(f"{name}: candidate too close to selected text: {text}")
        if EDITOR_META_RE.search(text):
            raise AssertionError(f"{name}: editor/meta wording leaked: {text}")


def assert_no_context_hijack(name: str, selected: str, variants: list[dict[str, Any]]) -> None:
    if any(term in selected for term in WORKBENCH_TERMS):
        return
    texts = [str(item.get("text", "")) for item in variants]
    hijacks = [text for text in texts if any(term in text for term in WORKBENCH_TERMS)]
    if hijacks:
        raise AssertionError(f"{name}: workbench context hijacked normal selected text: {hijacks}")


def heuristic_case(name: str, selected: str, *, before: str = "", after: str = "", must_any: tuple[str, ...] = ()) -> dict[str, Any]:
    variants = build_variants(selected, "rewrite", before, after, "")
    assert_article_ready(name, selected, variants, min_count=1)
    assert_no_context_hijack(name, selected, variants)
    texts = [str(item.get("text", "")) for item in variants]
    if must_any and not any(any(marker in text for marker in must_any) for text in texts):
        raise AssertionError(f"{name}: expected one of {must_any}, got {texts}")
    return {"name": name, "ok": True, "engine": "heuristic", "texts": texts[:3]}


def response_case_deepseek_default() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        store = StyleMemoryStore(Path(temp_dir) / "style_memory.jsonl", Path(temp_dir) / "style_memory_deleted.jsonl")
        with mock.patch.dict(os.environ, {"WORKBENCH_REWRITE_LOCAL_FIRST": "0"}, clear=False), mock.patch(
            "tools.inline_editor_server.deepseek_rewrite",
            return_value=[
                {
                    "move": "model-specific",
                    "label": "DeepSeek",
                    "text": "先找材料，把读者可能的质疑摆出来，再让草稿退回去改。",
                    "reason": "model",
                },
                {
                    "move": "model-oral",
                    "label": "DeepSeek",
                    "text": "材料先到，草稿能退，人再决定哪一句能留下。",
                    "reason": "model",
                },
                {
                    "move": "model-frame",
                    "label": "DeepSeek",
                    "text": "这些研究最后落回一条顺序：先备料，再审稿，最后才让模型继续写。",
                    "reason": "model",
                },
            ],
        ) as remote:
            response = rewrite_selection_response(
                {
                    "selectedText": (
                        "到今天，比较成熟的解法已经很清楚。Stanford STORM 先检索材料、多视角提问、生成大纲，"
                        "再进入正文。PaperDebugger 走的是研究、批判、修订的编辑器内流程。"
                    ),
                    "action": "rewrite",
                    "engine": "deepseek",
                },
                store,
                "deepseek",
            )
    if response.get("engine") != "deepseek":
        raise AssertionError(f"default deepseek route should use model first, got {response.get('engine')}")
    remote.assert_called_once()
    texts = [str(item.get("text", "")) for item in response.get("variants", [])]
    if "先找材料，把读者可能的质疑摆出来" not in texts[0]:
        raise AssertionError(f"model candidate was not kept first: {texts}")
    return {"name": "deepseek-default-primary", "ok": True, "engine": response.get("engine"), "texts": texts[:3]}


def response_case_explicit_local_fast() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        store = StyleMemoryStore(Path(temp_dir) / "style_memory.jsonl", Path(temp_dir) / "style_memory_deleted.jsonl")
        with mock.patch.dict(os.environ, {"WORKBENCH_REWRITE_LOCAL_FIRST": "1"}, clear=False):
            response = rewrite_selection_response(
                {
                    "selectedText": (
                        "到今天，比较成熟的解法已经很清楚。Stanford STORM 先检索材料、多视角提问、生成大纲，"
                        "再进入正文。PaperDebugger 走的是研究、批判、修订的编辑器内流程。"
                    ),
                    "action": "rewrite",
                    "engine": "deepseek",
                },
                store,
                "deepseek",
            )
    if response.get("engine") != "local-fast":
        raise AssertionError(f"explicit local-fast opt-in did not work, got {response.get('engine')}")
    return {"name": "explicit-local-fast-opt-in", "ok": True, "engine": response.get("engine")}


def model_order_case() -> dict[str, Any]:
    selected = "这套工作台改变的是坏句的去向。以前坏句混在全文里，最后靠人硬洗；现在坏句会被划出来、记录下来，变成下一次生成前的门槛。"

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "variants": [
                                            {
                                                "move": "model-action",
                                                "label": "DeepSeek",
                                                "text": "以前碰到空话，我只能整篇硬改；现在先选中那一句，点“讨厌”，把原因记下来。",
                                                "reason": "从动作进入。",
                                            },
                                            {
                                                "move": "model-memory",
                                                "label": "DeepSeek",
                                                "text": "风格库存下来的，是我为什么删掉这句话。",
                                                "reason": "说清记录内容。",
                                            },
                                            {
                                                "move": "model-next",
                                                "label": "DeepSeek",
                                                "text": "下一次 Kimi 写到同类句式，Codex 会先拿这条记录提醒它避开。",
                                                "reason": "接到下一次生成。",
                                            },
                                        ]
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                },
                ensure_ascii=False,
            ).encode("utf-8")

    with mock.patch.dict("tools.inline_editor_server.os.environ", {"DEEPSEEK_API_KEY": "test-key"}, clear=False), mock.patch(
        "tools.inline_editor_server.urllib_request.urlopen", return_value=FakeResponse()
    ):
        variants = deepseek_rewrite({"selectedText": selected, "action": "rewrite"}, "", timeout=1)
    moves = [str(item.get("move")) for item in variants[:3]]
    if moves != ["model-action", "model-memory", "model-next"]:
        raise AssertionError(f"good model candidates were reordered or replaced: {moves}")
    return {"name": "deepseek-model-order", "ok": True, "moves": moves, "texts": [item["text"] for item in variants[:3]]}


def run() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    cases.append(
        heuristic_case(
            "closing-line-no-workbench-hijack",
            "写作工具该留下的，可能就是这点稳定感",
            before="总得来说这个工作台的逻辑就是正式生成、审稿、细修、记录偏好。",
            after="",
            must_any=("不用从头推翻", "继续写", "判断"),
        )
    )
    cases.append(
        heuristic_case(
            "enough-line-no-workbench-hijack",
            "对我来说，这就够了。",
            before="它不保证每篇都写的惊艳。",
            after="它让我少一点从头推翻。",
        )
    )
    cases.append(
        heuristic_case(
            "smooth-but-useless-stays-on-sentence-problem",
            "这句话听起来很顺，但放不进正文。",
            before="不要被工作台说明带偏。",
            after="下一段讲具体例子。",
            must_any=("读者", "抓住", "改稿", "留"),
        )
    )
    cases.append(
        heuristic_case(
            "report-tone-does-not-become-product-copy",
            "值得注意的是，AI 写作工具的快速发展正在带来新的机会和挑战。",
            before="前文刚解释工作台怎么用。",
            after="后面才进入例子。",
            must_any=("机会和挑战", "具体", "变化"),
        )
    )
    cases.append(
        heuristic_case(
            "ai-trend-cliche-not-synonym-polished",
            "随着人工智能技术飞速发展，内容创作迎来前所未有的变革。",
            before="这里需要直接进入问题。",
            after="下一段说 AI 味。",
            must_any=("不要先写", "AI 时代", "开写前"),
        )
    )
    cases.append(
        heuristic_case(
            "real-workbench-selection-can-use-workbench-actions",
            "这套工作台改变的是坏句的去向。以前坏句混在全文里，最后靠人硬洗；现在坏句会被划出来、记录下来，变成下一次生成前的门槛。",
            before="这条记录还会影响下一次生成。",
            after="这个差别会慢慢累积。",
            must_any=("讨厌", "风格库", "Kimi", "Codex", "下次"),
        )
    )
    cases.append(response_case_deepseek_default())
    cases.append(response_case_explicit_local_fast())
    cases.append(model_order_case())
    return {"status": "PASS", "cases": cases}


def main() -> None:
    try:
        result = run()
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc)}
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
