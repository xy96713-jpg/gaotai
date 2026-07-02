#!/usr/bin/env python3
"""Smoke-test the workbench from a fresh clone.

This script simulates a technical external user cloning the repository,
copying the env template, and running the local readiness checks. It avoids
real API calls and does not print local secrets.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "QUICKSTART.md",
    ".env.local.example",
    "Makefile",
    "inline_editor_v2/app.js",
    "inline_editor_v2/styles.css",
    "tools/inline_editor_server.py",
    "tools/workbench_external_readiness.py",
    "tools/obsidian_bridge.py",
    "tests/test_inline_editor_server.py",
]

PY_COMPILE_FILES = [
    "tools/workbench_external_readiness.py",
    "tools/inline_editor_server.py",
    "tools/obsidian_bridge.py",
]


def run(cmd: list[str], cwd: Path, *, timeout: int = 120) -> dict[str, object]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "cmd": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def ensure_ok(step: dict[str, object]) -> None:
    if step["returncode"] != 0:
        raise RuntimeError(
            f"command failed: {step['cmd']}\nSTDOUT:\n{step['stdout']}\nSTDERR:\n{step['stderr']}"
        )


def clone_repo(source: Path, dest: Path) -> dict[str, object]:
    # Local clone is intentional: it proves the committed repository state
    # without depending on GitHub/network availability.
    return run(["git", "clone", "--quiet", "--no-hardlinks", str(source), str(dest)], ROOT, timeout=120)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(ROOT), help="repo path to clone")
    parser.add_argument("--keep", action="store_true", help="keep the temporary clone")
    parser.add_argument("--skip-tests", action="store_true", help="skip Python unittest in the clone")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    base_dir = Path(tempfile.mkdtemp(prefix="workbench-fresh-clone-"))
    clone_dir = base_dir / "repo"
    report: dict[str, object] = {"source": str(source), "cloneDir": str(clone_dir), "steps": []}

    try:
        step = clone_repo(source, clone_dir)
        report["steps"].append(step)
        ensure_ok(step)

        missing = [rel for rel in REQUIRED_FILES if not (clone_dir / rel).exists()]
        report["missingFiles"] = missing
        if missing:
            raise RuntimeError(f"fresh clone missing required files: {missing}")

        shutil.copy2(clone_dir / ".env.local.example", clone_dir / ".env.local")
        ignored = run(["git", "check-ignore", ".env.local"], clone_dir)
        report["steps"].append(ignored)
        ensure_ok(ignored)

        status = run(["git", "status", "--short"], clone_dir)
        report["steps"].append(status)
        ensure_ok(status)
        if status["stdout"].strip():
            raise RuntimeError(f"fresh clone is dirty after env copy:\n{status['stdout']}")

        readiness = run(["make", "workbench-external-readiness"], clone_dir)
        report["steps"].append(readiness)
        ensure_ok(readiness)

        py_compile = run([sys.executable, "-m", "py_compile", *PY_COMPILE_FILES], clone_dir)
        report["steps"].append(py_compile)
        ensure_ok(py_compile)

        node_check = run(["node", "--check", "inline_editor_v2/app.js"], clone_dir)
        report["steps"].append(node_check)
        ensure_ok(node_check)

        if not args.skip_tests:
            tests = run([sys.executable, "-m", "unittest", "tests.test_inline_editor_server"], clone_dir, timeout=180)
            report["steps"].append(tests)
            ensure_ok(tests)

        report["status"] = "PASS"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    finally:
        if args.keep:
            print(f"kept clone at: {clone_dir}")
        else:
            shutil.rmtree(base_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
