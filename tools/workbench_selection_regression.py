#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".cache" / "writing" / "workbench_selection_regression_latest.json"


FIRST_SCREEN_SELECTED = "往往发生在第一屏"
FIRST_SCREEN_CONTEXT_BEFORE = "AI 写稿最麻烦的地方，"
FIRST_SCREEN_CONTEXT_AFTER = "。它三十秒交出一篇完整稿。"


def request_json(base: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 45) -> dict[str, Any]:
    data = None
    headers = {"content-type": "application/json"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body[:500]}") from exc
    return json.loads(body or "{}")


def delete_json(base: str, path: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(f"{base}{path}", method="DELETE")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def variant_texts(response: dict[str, Any]) -> list[str]:
    return [str(item.get("text", "")).strip() for item in response.get("variants", []) if str(item.get("text", "")).strip()]


def bad_variant_hits(texts: list[str], selected: str) -> list[str]:
    hits: list[str] = []
    for text in texts:
        if text == selected:
            hits.append(f"unchanged:{text}")
        if "往往" in text or "第一屏" in text:
            hits.append(f"bad-frame:{text}")
        if any(marker in text for marker in ["这句还缺", "把抽象判断", "避免像孤立金句", "先回答一个具体问题"]):
            hits.append(f"diagnostic:{text}")
    return hits


def run(base: str, document_id: str, report_path: Path) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    def step(name: str, fn):
        started = time.time()
        try:
            value = fn()
            item = {"name": name, "ok": True, "ms": round((time.time() - started) * 1000), "value": value}
        except Exception as exc:  # noqa: BLE001 - smoke report should keep going when useful
            item = {"name": name, "ok": False, "ms": round((time.time() - started) * 1000), "error": str(exc)}
        steps.append(item)
        print(json.dumps(item, ensure_ascii=False))
        return item

    step("health", lambda: request_json(base, "/api/health", timeout=10))

    def heuristic_preview() -> dict[str, Any]:
        response = request_json(
            base,
            "/api/rewrite-selection",
            {
                "documentId": document_id,
                "engine": "heuristic",
                "action": "rewrite",
                "selectedText": FIRST_SCREEN_SELECTED,
                "contextBefore": FIRST_SCREEN_CONTEXT_BEFORE,
                "contextAfter": FIRST_SCREEN_CONTEXT_AFTER,
                "documentText": f"{FIRST_SCREEN_CONTEXT_BEFORE}{FIRST_SCREEN_SELECTED}{FIRST_SCREEN_CONTEXT_AFTER}",
            },
            timeout=20,
        )
        texts = variant_texts(response)
        hits = bad_variant_hits(texts, FIRST_SCREEN_SELECTED)
        if len(texts) < 3:
            raise AssertionError(f"expected at least 3 preview variants, got {texts}")
        if hits:
            raise AssertionError(f"bad preview variants: {hits}")
        return {"engine": response.get("engine"), "texts": texts}

    step("heuristic preview candidates are real rewrites", heuristic_preview)

    request_id_holder: dict[str, str] = {}

    def enqueue_selection() -> dict[str, Any]:
        response = request_json(
            base,
            "/api/selection-request",
            {
                "documentId": document_id,
                "action": "rewrite",
                "selectedText": FIRST_SCREEN_SELECTED,
                "contextBefore": FIRST_SCREEN_CONTEXT_BEFORE,
                "contextAfter": FIRST_SCREEN_CONTEXT_AFTER,
                "documentText": f"{FIRST_SCREEN_CONTEXT_BEFORE}{FIRST_SCREEN_SELECTED}{FIRST_SCREEN_CONTEXT_AFTER}",
                "selection": {"start": len(FIRST_SCREEN_CONTEXT_BEFORE), "end": len(FIRST_SCREEN_CONTEXT_BEFORE) + len(FIRST_SCREEN_SELECTED)},
            },
            timeout=20,
        )
        request_id_holder["id"] = str(response.get("id", ""))
        if not response.get("responseUrl"):
            raise AssertionError(f"missing responseUrl: {response}")
        return response

    step("enqueue deepseek selection request", enqueue_selection)

    def poll_selection() -> dict[str, Any]:
        request_id = request_id_holder.get("id")
        if not request_id:
            raise AssertionError("selection request was not queued")
        path = f"/api/selection-response/{urllib.parse.quote(request_id)}"
        last: dict[str, Any] = {}
        deadline = time.time() + 80
        while time.time() < deadline:
            last = request_json(base, path, timeout=20)
            if last.get("status") == "done":
                break
            time.sleep(1)
        if last.get("status") != "done":
            raise AssertionError(f"selection job not done: {last}")
        texts = variant_texts(last)
        hits = bad_variant_hits(texts, FIRST_SCREEN_SELECTED)
        if len(texts) < 3:
            raise AssertionError(f"expected at least 3 final variants, got {texts}")
        if hits:
            raise AssertionError(f"bad final variants: {hits}")
        if last.get("document_id") != document_id:
            raise AssertionError(f"wrong document_id: {last.get('document_id')}")
        if last.get("selected_text") != FIRST_SCREEN_SELECTED:
            raise AssertionError(f"wrong selected_text: {last.get('selected_text')}")
        return {"engine": last.get("engine"), "texts": texts, "document_id": last.get("document_id")}

    step("poll selection response quality", poll_selection)

    def latest_selection() -> dict[str, Any]:
        latest = request_json(base, f"/api/latest-selection-response?documentId={urllib.parse.quote(document_id)}", timeout=20)
        texts = variant_texts(latest)
        hits = bad_variant_hits(texts, FIRST_SCREEN_SELECTED)
        if latest.get("selected_text") != FIRST_SCREEN_SELECTED:
            raise AssertionError(f"latest response not tied to selected text: {latest.get('selected_text')}")
        if hits:
            raise AssertionError(f"bad latest variants: {hits}")
        return {"request_id": latest.get("request_id"), "texts": texts[:3]}

    step("latest selection response is current and usable", latest_selection)

    memory_id_holder: dict[str, str] = {}

    def memory_roundtrip() -> dict[str, Any]:
        entry = request_json(
            base,
            "/api/memory",
            {
                "kind": "banned_line",
                "sourceText": "这是回归测试临时讨厌句",
                "replacementText": "",
                "reason": "workbench selection regression temporary record",
                "tags": "regression,temp",
                "strength": "hard",
                "origin": "workbench_selection_regression",
            },
            timeout=20,
        )
        memory_id = str(entry.get("id", ""))
        memory_id_holder["id"] = memory_id
        entries = request_json(base, "/api/memory", timeout=20)
        if not any(item.get("id") == memory_id for item in entries):
            raise AssertionError("memory entry not found after write")
        delete_json(base, f"/api/memory/{urllib.parse.quote(memory_id)}", timeout=20)
        entries_after = request_json(base, "/api/memory", timeout=20)
        if any(item.get("id") == memory_id for item in entries_after):
            raise AssertionError("memory entry still present after delete")
        return {"memory_id": memory_id, "deleted": True}

    step("style memory write and delete roundtrip", memory_roundtrip)

    failed = [item for item in steps if not item["ok"]]
    summary = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": not failed,
        "base": base,
        "documentId": document_id,
        "total": len(steps),
        "failed": len(failed),
        "steps": steps,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Workbench selection/editing regression smoke test.")
    parser.add_argument("--base", default="http://127.0.0.1:8766")
    parser.add_argument("--document-id", default="first_video_best_candidate_20260615")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = run(args.base.rstrip("/"), args.document_id, args.report)
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
