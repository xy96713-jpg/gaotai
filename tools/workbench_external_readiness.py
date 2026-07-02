#!/usr/bin/env python3
"""Check whether the workbench repo is ready for external technical users."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "QUICKSTART.md",
    "OPEN_SOURCE_GUIDE.md",
    "PROJECT_BOUNDARIES.md",
    "RELEASE_MANIFEST.md",
    "Makefile",
    ".env.local.example",
    "inline_editor_v2/app.js",
    "inline_editor_v2/styles.css",
    "tools/inline_editor_server.py",
    "tools/workbench_ops.py",
    "tools/workbench_release_gate.py",
    "tests/test_inline_editor_server.py",
]

REQUIRED_ENV_KEYS = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_REWRITE_THINKING",
    "DEEPSEEK_SUPPORT_THINKING",
    "FULL_DRAFT_JOB_TIMEOUT_SECONDS",
]

DIRTY_ALLOWLIST = {
    ".cache/writing/bad_lines_corpus.md",
    ".cache/writing/config/personal_ip_tone_profile.md",
    "tools/inline_editor_server.py",
}

SENSITIVE_FILE_PATTERNS = (
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"(^|/).*secret.*", re.I),
    re.compile(r"(^|/).*credential.*", re.I),
    re.compile(r"(^|/).*cookie.*", re.I),
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.I),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{24,}"),
)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def tracked_files() -> list[str]:
    result = run_git(["ls-files"])
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_status_short() -> list[str]:
    result = run_git(["status", "--short"])
    if result.returncode != 0:
        return [f"git status failed: {result.stderr.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def check_required_files() -> list[str]:
    return [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]


def check_env_template() -> list[str]:
    template = read_text(ROOT / ".env.local.example")
    missing = []
    for key in REQUIRED_ENV_KEYS:
        if not re.search(rf"^{re.escape(key)}=", template, flags=re.M):
            missing.append(key)
    return missing


def check_sensitive_tracking(files: list[str]) -> list[str]:
    findings = []
    for rel in files:
        if rel == ".env.local.example":
            continue
        if any(pattern.search(rel) for pattern in SENSITIVE_FILE_PATTERNS):
            findings.append(rel)
    return findings


def check_secret_values(files: list[str]) -> list[str]:
    findings = []
    skip_prefixes = (".cache/", "obsidian_vault/")
    skip_suffixes = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip")
    for rel in files:
        if rel == ".env.local.example":
            continue
        if rel.startswith(skip_prefixes) or rel.lower().endswith(skip_suffixes):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = read_text(path)
        if not text:
            continue
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(text):
                findings.append(rel)
                break
    return sorted(set(findings))


def check_dirty_status(status_lines: list[str]) -> list[str]:
    unexpected = []
    for line in status_lines:
        rel = line[3:].strip()
        if rel not in DIRTY_ALLOWLIST:
            unexpected.append(line)
    return unexpected


def main() -> int:
    files = tracked_files()
    status_lines = git_status_short()
    report = {
        "missingFiles": check_required_files(),
        "missingEnvKeys": check_env_template(),
        "trackedSensitiveFiles": check_sensitive_tracking(files),
        "secretValueHits": check_secret_values(files),
        "unexpectedDirtyFiles": check_dirty_status(status_lines),
        "allowedDirtyFiles": [line for line in status_lines if line[3:].strip() in DIRTY_ALLOWLIST],
    }
    blocking = {
        key: value
        for key, value in report.items()
        if key != "allowedDirtyFiles" and value
    }
    report["status"] = "BLOCKED" if blocking else "PASS"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
