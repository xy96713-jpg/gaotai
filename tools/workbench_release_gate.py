#!/usr/bin/env python3
"""Release gate for the local writing workbench small-scope beta.

This is intentionally stricter than a normal smoke test: it combines unit,
static, browser, topic-management, style-memory, and one small live quality
trial into a single READY/BLOCKED report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / ".cache" / "writing" / "release_checks"
FORMAL_DOCUMENT_ID = "first_video_concise_strengthened_20260617"
TRANSIENT_FAILURE_MARKERS = (
    "ERR_CONNECTION_REFUSED",
    "Connection refused",
    "Remote end closed connection without response",
    "Failed to fetch",
    "Execution context was destroyed",
    "Target page, context or browser has been closed",
)


@dataclass(frozen=True)
class ReleaseStep:
    name: str
    command: list[str]
    timeout_seconds: int = 180
    env: dict[str, str] | None = None


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def display_command(step: ReleaseStep) -> str:
    prefix = ""
    if step.env:
        prefix = " ".join(f"{key}={value}" for key, value in step.env.items()) + " "
    return prefix + " ".join(step.command)


def output_tail(value: str, limit: int = 5000) -> str:
    value = value or ""
    if len(value) <= limit:
        return value
    return value[-limit:]


def run_step(step: ReleaseStep) -> dict[str, Any]:
    started = time.monotonic()
    env = os.environ.copy()
    if step.env:
        env.update(step.env)
    try:
        completed = subprocess.run(
            step.command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=step.timeout_seconds,
            check=False,
        )
        return {
            "name": step.name,
            "command": display_command(step),
            "ok": completed.returncode == 0,
            "returnCode": completed.returncode,
            "ms": round((time.monotonic() - started) * 1000),
            "stdoutTail": output_tail(completed.stdout),
            "stderrTail": output_tail(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": step.name,
            "command": display_command(step),
            "ok": False,
            "returnCode": None,
            "ms": round((time.monotonic() - started) * 1000),
            "stdoutTail": output_tail(exc.stdout if isinstance(exc.stdout, str) else ""),
            "stderrTail": output_tail(exc.stderr if isinstance(exc.stderr, str) else f"timeout after {step.timeout_seconds}s"),
            "timedOut": True,
        }


def looks_transient_failure(step_result: dict[str, Any]) -> bool:
    if step_result.get("ok"):
        return False
    text = "\n".join(
        [
            str(step_result.get("stdoutTail") or ""),
            str(step_result.get("stderrTail") or ""),
        ]
    )
    return any(marker in text for marker in TRANSIENT_FAILURE_MARKERS)


def recover_service() -> dict[str, Any]:
    return run_step(ReleaseStep("recover service", ["python3", "tools/workbench_ops.py", "restart"], 120))


def release_steps(*, skip_live: bool = False) -> list[ReleaseStep]:
    formal_env = {"WORKBENCH_DOCUMENT_ID": FORMAL_DOCUMENT_ID}
    steps = [
        ReleaseStep("restart service", ["python3", "tools/workbench_ops.py", "restart"], 120),
        ReleaseStep("unit tests", ["python3", "-m", "unittest", "tests.test_inline_editor_server"], 240),
        ReleaseStep("frontend syntax", ["node", "--check", "inline_editor_v2/app.js"], 60),
        ReleaseStep("rewrite logic audit", ["python3", "tools/workbench_rewrite_logic_audit.py"], 180),
        ReleaseStep("rewrite matrix", ["python3", "tools/workbench_rewrite_matrix.py"], 240),
        ReleaseStep("paragraph assist fast matrix", ["python3", "tools/workbench_paragraph_assist_matrix.py", "--max-cases", "3"], 240),
        ReleaseStep("formal readonly browser smoke", ["node", "tools/workbench_formal_readonly_smoke.mjs"], 180, formal_env),
        ReleaseStep("presentation smoke", ["node", "tools/workbench_presentation_smoke.mjs"], 180, formal_env),
        ReleaseStep("new topic smoke", ["node", "tools/workbench_new_topic_smoke.mjs"], 240),
        ReleaseStep("topic management smoke", ["node", "tools/workbench_topic_management_smoke.mjs"], 240),
        ReleaseStep("style memory hygiene", ["python3", "tools/style_memory_hygiene.py"], 180),
    ]
    if not skip_live:
        steps.append(
            ReleaseStep(
                "release-small live quality trial",
                ["python3", "tools/workbench_quality_trial.py", "--mode", "live", "--preset", "release-small"],
                900,
            )
        )
    steps.append(ReleaseStep("product audit", ["python3", "tools/workbench_product_audit.py"], 180))
    return steps


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# 写作工作台小范围内测发布检查",
        "",
        f"- 结论：{result['status']}",
        f"- 生成时间：{result['generatedAt']}",
        f"- 输出目录：`{result['outputDir']}`",
        f"- 通过：{result['passed']} / {result['total']}",
        "",
        "## 步骤",
        "",
        "| 步骤 | 状态 | 耗时 | 命令 |",
        "| --- | --- | ---: | --- |",
    ]
    for step in result["steps"]:
        if step["ok"] and step.get("retried"):
            status = "PASS(重试后通过)"
        else:
            status = "PASS" if step["ok"] else "FAIL"
        lines.append(f"| {step['name']} | {status} | {step['ms']}ms | `{step['command']}` |")
    lines.extend(["", "## 失败详情", ""])
    failures = [step for step in result["steps"] if not step["ok"]]
    if not failures:
        lines.append("无。")
    for step in failures:
        lines.extend(
            [
                f"### {step['name']}",
                "",
                f"- 命令：`{step['command']}`",
                f"- 返回码：{step.get('returnCode')}",
                "",
                "```text",
                (step.get("stderrTail") or step.get("stdoutTail") or "").strip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the writing workbench release gate.")
    parser.add_argument("--skip-live", action="store_true", help="Skip the release-small live model quality trial.")
    args = parser.parse_args()

    out = REPORT_ROOT / now_slug()
    out.mkdir(parents=True, exist_ok=True)
    steps = []
    for step in release_steps(skip_live=args.skip_live):
        print(f"[release-check] {step.name}: {display_command(step)}", file=sys.stderr, flush=True)
        result = run_step(step)
        if looks_transient_failure(result):
            print(f"[release-check] retry transient step: {step.name}", file=sys.stderr, flush=True)
            recovery = recover_service()
            retried = run_step(step)
            retried["retried"] = True
            retried["recovery"] = recovery
            retried["firstFailure"] = {
                "returnCode": result.get("returnCode"),
                "stdoutTail": result.get("stdoutTail"),
                "stderrTail": result.get("stderrTail"),
            }
            result = retried
        steps.append(result)
    passed = sum(1 for step in steps if step["ok"])
    result = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "READY" if passed == len(steps) else "BLOCKED",
        "passed": passed,
        "total": len(steps),
        "outputDir": str(out.relative_to(ROOT)),
        "skipLive": bool(args.skip_live),
        "steps": steps,
    }
    result_path = out / "result.json"
    report_path = out / "report.md"
    result["resultPath"] = str(result_path.relative_to(ROOT))
    result["reportPath"] = str(report_path.relative_to(ROOT))
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    print(build_report(result))
    print(f"result: {result['resultPath']}")
    print(f"report: {result['reportPath']}")
    raise SystemExit(0 if result["status"] == "READY" else 1)


if __name__ == "__main__":
    main()
