#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8766
BASE_URL = f"http://{HOST}:{PORT}"
SESSION_NAME = "inline_editor_8766"
LOG_PATH = ROOT / ".cache" / "logs" / "inline_editor_8766.log"


def resolve_server_python() -> Path:
    override = os.environ.get("WORKBENCH_PYTHON", "").strip()
    candidates = [
        Path(override).expanduser() if override else None,
        ROOT / ".venv-local-vlm" / "bin" / "python",
        ROOT / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return Path(sys.executable)


PYTHON = resolve_server_python()
PYTHON_CMD = str(PYTHON)
SERVER_CMD = (
    f"cd {shlex.quote(str(ROOT))} && "
    f"{shlex.quote(PYTHON_CMD)} tools/inline_editor_server.py "
    f"--host {HOST} --port {PORT} --engine deepseek "
    f"> {shlex.quote(str(LOG_PATH))} 2>&1"
)


def run_cmd(args: list[str], check: bool = False, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout)


def shell_cmd(command: str, check: bool = False, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["zsh", "-lc", command], cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout)


def screen_sessions() -> str:
    result = run_cmd(["screen", "-ls"], check=False)
    return f"{result.stdout}{result.stderr}"


def screen_running() -> bool:
    return f".{SESSION_NAME}" in screen_sessions()


def port_pids() -> list[int]:
    result = run_cmd(["lsof", "-t", f"-iTCP:{PORT}", "-sTCP:LISTEN"], check=False)
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def pid_command(pid: int) -> str:
    result = run_cmd(["ps", "-p", str(pid), "-o", "command="], check=False)
    return result.stdout.strip()


def health(timeout: int = 4) -> dict[str, Any]:
    request = urllib.request.Request(f"{BASE_URL}/api/health")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def health_ok() -> bool:
    try:
        data = health()
        return bool(data.get("ok"))
    except Exception:
        return False


def service_status() -> dict[str, Any]:
    pids = port_pids()
    return {
        "baseUrl": BASE_URL,
        "python": PYTHON_CMD,
        "screenSession": SESSION_NAME,
        "screenRunning": screen_running(),
        "listenPids": [{"pid": pid, "command": pid_command(pid)} for pid in pids],
        "health": health() if pids else None,
        "logPath": str(LOG_PATH),
    }


def stop_service() -> dict[str, Any]:
    stopped: list[dict[str, Any]] = []
    if screen_running():
        run_cmd(["screen", "-S", SESSION_NAME, "-X", "quit"], check=False)
        stopped.append({"kind": "screen", "name": SESSION_NAME})
        time.sleep(0.8)

    for pid in port_pids():
        command = pid_command(pid)
        if "inline_editor_server.py" not in command:
            raise RuntimeError(f"port {PORT} is occupied by non-workbench process {pid}: {command}")
        run_cmd(["kill", str(pid)], check=False)
        stopped.append({"kind": "pid", "pid": pid, "command": command})

    deadline = time.time() + 6
    while time.time() < deadline and port_pids():
        time.sleep(0.2)
    remaining = port_pids()
    if remaining:
        for pid in remaining:
            command = pid_command(pid)
            if "inline_editor_server.py" in command:
                run_cmd(["kill", "-9", str(pid)], check=False)
                stopped.append({"kind": "pid-force", "pid": pid, "command": command})
        time.sleep(0.5)
    return {"stopped": stopped, "remainingPids": port_pids()}


def start_service(force: bool = False) -> dict[str, Any]:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if force:
        stop_service()
    elif health_ok():
        return {"started": False, "reason": "already healthy", "status": service_status()}

    if port_pids():
        stop_service()
    run_cmd(["screen", "-dmS", SESSION_NAME, "zsh", "-lc", SERVER_CMD], check=True)

    deadline = time.time() + 12
    last_error = ""
    while time.time() < deadline:
        try:
            data = health(timeout=2)
            if data.get("ok"):
                return {"started": True, "status": service_status()}
        except Exception as exc:  # noqa: BLE001 - surfaced in status
            last_error = str(exc)
        time.sleep(0.4)
    log_tail = LOG_PATH.read_text(encoding="utf-8", errors="replace")[-2000:] if LOG_PATH.exists() else ""
    raise RuntimeError(f"workbench did not become healthy: {last_error}\n{log_tail}")


def run_step(name: str, command: list[str], timeout: int = 180) -> dict[str, Any]:
    started = time.time()
    result = run_cmd(command, check=False, timeout=timeout)
    return {
        "name": name,
        "ok": result.returncode == 0,
        "ms": round((time.time() - started) * 1000),
        "command": command,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "returncode": result.returncode,
    }


def smoke(selection_only: bool = False) -> dict[str, Any]:
    steps = [
        run_step("health", [PYTHON_CMD, "-c", "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8766/api/health')), ensure_ascii=False))"], timeout=15),
        run_step("rewrite matrix", [PYTHON_CMD, "tools/workbench_rewrite_matrix.py"], timeout=60),
        run_step("chaos test", [PYTHON_CMD, "tools/workbench_chaos_test.py"], timeout=60),
        run_step("selection regression", [PYTHON_CMD, "tools/workbench_selection_regression.py", "--document-id", "first_video_best_candidate_20260615"], timeout=120),
    ]
    if not selection_only:
        steps.append(run_step("desktop residue smoke", ["node", "tools/workbench_desktop_residue_smoke.mjs"], timeout=60))
        steps.append(run_step("browser smoke", ["node", "tools/workbench_browser_smoke.mjs"], timeout=180))
    return {"ok": all(step["ok"] for step in steps), "steps": steps}


def verify() -> dict[str, Any]:
    start_service(force=True)
    steps = [
        run_step("js syntax", ["node", "--check", "inline_editor_v2/app.js"], timeout=20),
        run_step("unit tests", [PYTHON_CMD, "-m", "unittest", "discover", "-s", "tests"], timeout=120),
        *smoke(selection_only=False)["steps"],
    ]
    return {"ok": all(step["ok"] for step in steps), "status": service_status(), "steps": steps}


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate the local writing workbench service.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("start")
    subparsers.add_parser("stop")
    subparsers.add_parser("restart")
    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--selection-only", action="store_true")
    subparsers.add_parser("verify")
    args = parser.parse_args()

    try:
        if args.command == "status":
            print_json(service_status())
        elif args.command == "start":
            print_json(start_service(force=False))
        elif args.command == "stop":
            print_json(stop_service())
        elif args.command == "restart":
            print_json(start_service(force=True))
        elif args.command == "smoke":
            print_json(smoke(selection_only=args.selection_only))
        elif args.command == "verify":
            print_json(verify())
        return 0
    except Exception as exc:  # noqa: BLE001 - command line operator output
        print_json({"ok": False, "error": str(exc), "status": service_status() if args.command != "stop" else None})
        return 1


if __name__ == "__main__":
    sys.exit(main())
