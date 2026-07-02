#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import (
    DELETED_DOCUMENT_DIR,
    DELETED_TOPIC_ARCHIVE_DIR,
    DOCUMENT_DIR,
    ROOT,
    TOPIC_ARCHIVE_DIR,
    infer_document_type,
    soft_delete_document,
)

NOISE_PATTERNS = [
    r"(^|_)browser_smoke_temp",
    r"(^|_)browser_smoke_debug",
    r"(^|_)focused_smoke_temp",
    r"(^|_)focused_temp",
    r"(^|_)memory_ui_temp",
    r"(^|_)api_delete_probe",
    r"(^|_)obsidian_link_probe",
    r"(^|_)plain_language_temp",
    r"(^|_)hard_issue_temp",
    r"(^|_)smoke_exact_debug",
    r"(^|_)smoke_state_debug",
    r"(^|_)style_memory_real_proof_",
    r"(^|_)selection_sync_regression_",
    r"(^|_)topic_management_smoke_",
    r"(^|_)ui_document_type_probe_",
    r"(^|_)verify_live_smoke_",
    r"(^|_)verify_fixture_",
    r"(^|_)timeout_fix_fixture_",
    r"(^|_)paragraph_assist_(smoke|state|accept|natural)",
    r"(^|_)paragraph_inline_removed_",
    r"(^|_)kimi_fast_paragraph_",
    r"(^|_)smoke-doc$",
    r"(^|_)fast_route_fixture_",
    r"(^|_)formal_default_fixture_",
    r"(^|_)gate_fix_fixture_",
    r"(^|_)gate_repair_fixture_",
    r"(^|_)live_fast_route_probe_",
    r"(^|_)live_full_timeout_probe",
    r"(^|_)live_gate_repair_proof_",
    r"(^|_)quality_trial_",
    r"(^|[-_])e2e([-_]|$)",
]

NOISE_RX = re.compile("|".join(f"(?:{pattern})" for pattern in NOISE_PATTERNS))

DELETED_TEST_TITLE_MARKERS = (
    "新主题烟测",
    "主题管理烟测",
    "版本风格证明验证稿",
)

DELETED_TEST_ID_RX = re.compile(
    r"^(?:topic_\d{8}_\d{6}_[a-z0-9]{4}|topic_management_smoke_|topic_archive_styleproof_verify_)"
)


def iter_noise_documents() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(DOCUMENT_DIR.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        document_id = str(record.get("document_id", path.stem)).strip() or path.stem
        title = str(record.get("title", "")).strip()
        if not NOISE_RX.search(document_id):
            continue
        document_type = infer_document_type(document_id, title, str(record.get("document_type", "")))
        rows.append(
            {
                "document_id": document_id,
                "title": title,
                "document_type": document_type,
                "path": str(path),
            }
        )
    return rows


def iter_noise_topic_archives() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not TOPIC_ARCHIVE_DIR.exists():
        return rows
    for path in sorted(TOPIC_ARCHIVE_DIR.glob("*.json")):
        archive_id = path.stem
        if not NOISE_RX.search(archive_id):
            continue
        rows.append(
            {
                "document_id": archive_id,
                "path": str(path),
            }
        )
    return rows


def soft_delete_topic_archive(path_text: str) -> str:
    source = Path(path_text)
    DELETED_TOPIC_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = DELETED_TOPIC_ARCHIVE_DIR / f"{source.stem}.{timestamp}.json"
    source.replace(target)
    return str(target)


def deleted_test_artifacts() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for base_dir, kind in [
        (DELETED_DOCUMENT_DIR, "deleted_document"),
        (DELETED_TOPIC_ARCHIVE_DIR, "deleted_topic_archive"),
    ]:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.glob("*.json")):
            stem_id = path.name.split(".", 1)[0]
            title = ""
            content = ""
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                title = normalize_deleted_text(str(record.get("title", "")))
                content = normalize_deleted_text(str(record.get("content_text", "")))
            except Exception:
                pass
            if DELETED_TEST_ID_RX.search(stem_id) or any(marker in f"{title} {content}" for marker in DELETED_TEST_TITLE_MARKERS):
                rows.append(
                    {
                        "kind": kind,
                        "document_id": stem_id,
                        "title": title,
                        "path": str(path),
                    }
                )
    return rows


def normalize_deleted_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def quarantine_deleted_test_artifacts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    quarantine_root = ROOT / ".cache" / "writing" / "quarantine" / "deleted_test_artifacts" / timestamp
    moved: list[dict[str, str]] = []
    for row in rows:
        source = Path(row["path"])
        if not source.exists():
            continue
        target_dir = quarantine_root / row["kind"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        source.replace(target)
        moved.append({**row, "quarantine_path": str(target)})
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(description="Soft-delete obvious workbench smoke/temp/fixture documents.")
    parser.add_argument("--apply", action="store_true", help="Move matched documents into deleted_documents.")
    args = parser.parse_args()

    rows = iter_noise_documents()
    archive_rows = iter_noise_topic_archives()
    deleted_rows = deleted_test_artifacts()
    if not args.apply:
        print(
            json.dumps(
                {
                    "apply": False,
                    "count": len(rows),
                    "documents": rows,
                    "topicArchiveCount": len(archive_rows),
                    "topicArchives": archive_rows,
                    "deletedTestArtifactCount": len(deleted_rows),
                    "deletedTestArtifacts": deleted_rows,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    deleted: list[dict[str, str]] = []
    for row in rows:
        result = soft_delete_document(row["document_id"], confirm_formal=True)
        deleted.append(
            {
                "document_id": row["document_id"],
                "title": row["title"],
                "document_type": result.get("documentType", row["document_type"]),
                "deleted_path": result.get("deletedPath", ""),
            }
        )
    deleted_archives = [
        {
            "document_id": row["document_id"],
            "deleted_path": soft_delete_topic_archive(row["path"]),
        }
        for row in archive_rows
        if Path(row["path"]).exists()
    ]
    quarantined_deleted = quarantine_deleted_test_artifacts(deleted_rows)
    print(
        json.dumps(
            {
                "apply": True,
                "count": len(deleted),
                "documents": deleted,
                "topicArchiveCount": len(deleted_archives),
                "topicArchives": deleted_archives,
                "deletedTestArtifactCount": len(quarantined_deleted),
                "deletedTestArtifacts": quarantined_deleted,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
