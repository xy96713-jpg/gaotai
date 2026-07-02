#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import deepseek_rewrite, rewrite_selection_response
from tools.style_memory import StyleMemoryStore
from tools.workbench_rewrite_matrix import assert_candidate_quality, request_json, variant_texts


DEFAULT_REPORT = ROOT / ".cache" / "writing" / "workbench_chaos_latest.json"
DEFAULT_BASE = "http://127.0.0.1:8766"

RESEARCH_SELECTED = (
    "到今天，比较成熟的解法已经很清楚。Stanford STORM 先检索材料、多视角提问、生成大纲，再进入正文。"
    "PaperDebugger 走的是研究、批判、修订的编辑器内流程。CoAuthor 这类研究把人和模型的写作互动拆开看。"
    "2025 年关于学术写作的综述也反复强调，AI 可以辅助，但责任和解释权还在人这里。"
)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"choices": [{"message": {"content": self.content}}]}, ensure_ascii=False).encode("utf-8")


def openai_json_content(variants: list[dict[str, str]]) -> str:
    return json.dumps({"variants": variants}, ensure_ascii=False)


def assert_clean_candidates(case_name: str, selected: str, variants: list[dict[str, Any]], min_count: int = 3) -> list[str]:
    texts = [str(item.get("text", "")).strip() for item in variants if str(item.get("text", "")).strip()]
    assert_candidate_quality(case_name=case_name, selected=selected, texts=texts, min_count=min_count)
    for text in texts:
        if any(fragment in text for fragment in ["variants", '"text"', "{", "}", "\\"]):
            raise AssertionError(f"{case_name}: JSON fragment leaked: {text}")
    return texts


def run_step(results: list[dict[str, Any]], name: str, fn) -> None:  # noqa: ANN001
    started = time.time()
    try:
        value = fn()
        item = {"name": name, "ok": True, "ms": round((time.time() - started) * 1000), "value": value}
    except Exception as exc:  # noqa: BLE001
        item = {"name": name, "ok": False, "ms": round((time.time() - started) * 1000), "error": str(exc)}
    results.append(item)
    print(json.dumps(item, ensure_ascii=False))


def direct_deepseek_bad_json_recovery() -> dict[str, Any]:
    content = "\n".join(
        [
            "{",
            '"variants": [',
            "1. 这些研究其实在解决同一件事：先把材料、角度和反对意见准备好，再让模型写。",
            '"text": "',
            "2. 换成日常写稿的话，就是先做功课，再让 AI 动笔。",
            "}",
            "3. 它们给我的提醒很直接：别把写作当成一次生成。",
        ]
    )
    with mock.patch.dict("tools.inline_editor_server.os.environ", {"DEEPSEEK_API_KEY": "chaos-test"}, clear=False), mock.patch(
        "tools.inline_editor_server.urllib_request.urlopen", return_value=FakeResponse(content)
    ):
        variants = deepseek_rewrite({"selectedText": RESEARCH_SELECTED, "action": "rewrite"}, "", timeout=1)
    texts = assert_clean_candidates("bad json recovery", RESEARCH_SELECTED, variants)
    return {"count": len(texts), "texts": texts[:3]}


def direct_deepseek_near_duplicate_mixdown() -> dict[str, Any]:
    content = openai_json_content(
        [
            {
                "move": "rewrite",
                "label": "候选",
                "text": "到现在，比较成熟的解法已经很清楚。Stanford STORM 的做法是：先检索材料，再从多个角度提问，生成大纲，最后写正文。PaperDebugger 则是在编辑器里走研究、批判、修订的流程。",
                "reason": "微调。",
            },
            {
                "move": "rewrite",
                "label": "候选",
                "text": "到现在，比较成熟的解法已经很清楚。Stanford STORM 先检索材料，从多个角度提问，生成大纲，再动笔写正文。PaperDebugger 走的是研究、批判、修订的编辑器内流程。",
                "reason": "微调。",
            },
            {
                "move": "rewrite",
                "label": "候选",
                "text": "这些研究其实在解决同一件事：先把材料、角度和反对意见准备好，再让模型写。",
                "reason": "换成动作。",
            },
        ]
    )
    with mock.patch.dict("tools.inline_editor_server.os.environ", {"DEEPSEEK_API_KEY": "chaos-test"}, clear=False), mock.patch(
        "tools.inline_editor_server.urllib_request.urlopen", return_value=FakeResponse(content)
    ):
        variants = deepseek_rewrite({"selectedText": RESEARCH_SELECTED, "action": "rewrite"}, "", timeout=1)
    texts = assert_clean_candidates("near duplicate mixdown", RESEARCH_SELECTED, variants)
    if not any("日常写稿" in text for text in texts):
        raise AssertionError(f"near duplicate mixdown: local oral route was not mixed in: {texts}")
    return {"count": len(texts), "texts": texts[:3]}


def rewrite_response_falls_back_when_model_unusable() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        store = StyleMemoryStore(Path(temp_dir) / "style_memory.jsonl", Path(temp_dir) / "style_memory_deleted.jsonl")
        payload = {
            "engine": "deepseek",
            "action": "rewrite",
            "selectedText": RESEARCH_SELECTED,
            "contextBefore": "",
            "contextAfter": "",
        }
        with mock.patch.dict("tools.inline_editor_server.os.environ", {"WORKBENCH_REWRITE_LOCAL_FIRST": "0"}, clear=False), mock.patch(
            "tools.inline_editor_server.deepseek_rewrite", side_effect=RuntimeError("chaos unusable model")
        ):
            result = rewrite_selection_response(payload, store, "deepseek")
    if result.get("engine") != "heuristic-fallback":
        raise AssertionError(f"expected heuristic fallback, got {result.get('engine')}")
    texts = assert_clean_candidates("fallback response", RESEARCH_SELECTED, result.get("variants", []))
    return {"engine": result.get("engine"), "count": len(texts), "texts": texts[:3]}


def api_case(base: str, name: str, selected: str, action: str = "rewrite", required_any: tuple[str, ...] = ()) -> dict[str, Any]:
    payload = {
        "documentId": "chaos_api_temp",
        "engine": "heuristic",
        "action": action,
        "selectedText": selected,
        "contextBefore": "",
        "contextAfter": "",
        "documentText": selected,
    }
    response = request_json(base, "/api/rewrite-selection", payload, timeout=20)
    texts = variant_texts(response)
    assert_candidate_quality(case_name=name, selected=selected, texts=texts, required_any=required_any)
    return {"engine": response.get("engine"), "count": len(texts), "texts": texts[:3]}


def run(base: str = DEFAULT_BASE, report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    run_step(results, "direct bad-json recovery", direct_deepseek_bad_json_recovery)
    run_step(results, "direct near-duplicate mixdown", direct_deepseek_near_duplicate_mixdown)
    run_step(results, "rewrite response fallback", rewrite_response_falls_back_when_model_unusable)
    run_step(
        results,
        "api macro slop rewrite",
        lambda: api_case(
            base,
            "api macro slop rewrite",
            "随着人工智能技术飞速发展，内容创作迎来前所未有的变革。",
            required_any=("写 AI 时代来了", "开写前", "文章要往哪走"),
        ),
    )
    run_step(
        results,
        "api jargon plain-language",
        lambda: api_case(
            base,
            "api jargon plain-language",
            "AI writing workflow 需要通过 style memory 和审稿 gate 才能稳定降低 AI 味。",
            action="plain-language",
            required_any=("记住你的喜好", "同一套标准", "下一次开写前"),
        ),
    )

    failed = [item for item in results if not item.get("ok")]
    summary = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": not failed,
        "base": base,
        "total": len(results),
        "failed": len(failed),
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Chaos tests for writing workbench model-output and candidate-quality failures.")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = run(args.base.rstrip("/"), args.report)
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
