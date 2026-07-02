from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OBSIDIAN_VAULT_DIR = ROOT / "obsidian_vault"
OBSIDIAN_VAULT_DIR = DEFAULT_OBSIDIAN_VAULT_DIR
OBSIDIAN_APP_DIR = Path.home() / "Library" / "Application Support" / "obsidian"
OBSIDIAN_SHARED_SUBDIR = "Codex写作工作台"
STYLE_MEMORY_INDEX_NAME = "README.md"


def _is_formal_document_type(label: str) -> bool:
    return _normalize_space(label) in {"正式稿", "formal", "正式"}


def _is_test_topic_id(topic_id: str) -> bool:
    value = _normalize_space(topic_id).lower()
    return any(
        marker in value
        for marker in (
            "api_delete_probe",
            "delete_probe",
            "final-review",
            "final_review",
            "paste_diag",
            "smoke",
            "browser_temp",
            "browser-smoke",
            "temp",
            "tmp_",
            "quality_trial",
            "style_proof",
            "unit",
        )
    )


def _workspace_fallback_root() -> Path:
    return OBSIDIAN_VAULT_DIR


def _preferred_registered_obsidian_vault() -> Path | None:
    vaults = _registered_obsidian_vaults()
    if not vaults:
        return None
    preferred = next((item for item in vaults if item.get("path")), None)
    if not preferred:
        return None
    try:
        return Path(str(preferred["path"])).expanduser().resolve()
    except Exception:
        return Path(str(preferred["path"])).expanduser()


def _obsidian_storage_root() -> Path:
    configured = _workspace_fallback_root()
    try:
        configured_resolved = configured.expanduser().resolve()
        default_resolved = DEFAULT_OBSIDIAN_VAULT_DIR.expanduser().resolve()
    except Exception:
        configured_resolved = configured.expanduser()
        default_resolved = DEFAULT_OBSIDIAN_VAULT_DIR.expanduser()
    if configured_resolved != default_resolved:
        return configured
    preferred = _preferred_registered_obsidian_vault()
    if preferred is not None:
        return preferred / OBSIDIAN_SHARED_SUBDIR
    return configured


def _maybe_migrate_workspace_mirror(storage_root: Path) -> None:
    fallback_root = _workspace_fallback_root()
    try:
        storage_resolved = storage_root.expanduser().resolve()
        fallback_resolved = fallback_root.expanduser().resolve()
    except Exception:
        storage_resolved = storage_root.expanduser()
        fallback_resolved = fallback_root.expanduser()
    if storage_resolved == fallback_resolved:
        return
    if not fallback_root.exists():
        return
    storage_root.mkdir(parents=True, exist_ok=True)
    try:
        if any(storage_root.iterdir()):
            return
    except FileNotFoundError:
        pass
    for name in ("Workbench.md", "Topics", "StyleMemory"):
        src = fallback_root / name
        dst = storage_root / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _topics_dir() -> Path:
    return _obsidian_storage_root() / "Topics"


def _style_memory_dir() -> Path:
    return _obsidian_storage_root() / "StyleMemory"


def _safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", (value or "").strip(), flags=re.UNICODE)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or fallback


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def ensure_obsidian_dirs() -> None:
    storage_root = _obsidian_storage_root()
    _maybe_migrate_workspace_mirror(storage_root)
    _topics_dir().mkdir(parents=True, exist_ok=True)
    _style_memory_dir().mkdir(parents=True, exist_ok=True)
    _ensure_vault_index()
    _ensure_style_memory_index()


def _ensure_vault_index() -> None:
    index_path = _obsidian_storage_root() / "Workbench.md"
    if index_path.exists():
        return
    index_path.write_text(
        "\n".join(
            [
                "# 写作工作台镜像",
                "",
                "这是工作台同步到 Obsidian 的本地镜像层。",
                "",
                "- 主题稿：见 `Topics/`",
                "- 风格库：见 `StyleMemory/`",
                "",
                "日常还是在写作工作台里写；Obsidian 主要用来看主题历史、风格记忆和长期积累。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ensure_style_memory_index()


def _style_memory_index_path() -> Path:
    return _style_memory_dir() / STYLE_MEMORY_INDEX_NAME


def _ensure_style_memory_index() -> None:
    index_path = _style_memory_index_path()
    if index_path.exists():
        return
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        "\n".join(
            [
                "# 风格库归档",
                "",
                "这里不再同步每一条 `mem_xxx` 记忆文件。",
                "",
                "原因：单条喜欢/讨厌/改写记录会让 Obsidian 图谱变成噪音。日常写作仍然由写作工作台读取风格库，Obsidian 只保留这个只读说明页。",
                "",
                "主流程：",
                "",
                "1. 在写作工作台正文里选句。",
                "2. 点改句、喜欢或讨厌。",
                "3. 后台继续把偏好写入工作台风格库。",
                "4. Obsidian 不再展示每条记忆节点。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _registered_obsidian_vaults() -> list[dict[str, str]]:
    config_path = OBSIDIAN_APP_DIR / "obsidian.json"
    if not config_path.exists():
        return []
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    vaults = payload.get("vaults")
    if not isinstance(vaults, dict):
        return []
    rows: list[dict[str, str]] = []
    for vault_id, info in vaults.items():
        if not isinstance(info, dict):
            continue
        raw_path = str(info.get("path", "")).strip()
        if not raw_path:
            continue
        try:
            resolved = Path(raw_path).expanduser().resolve()
        except Exception:
            resolved = Path(raw_path).expanduser()
        rows.append(
            {
                "id": str(vault_id).strip(),
                "path": str(resolved),
                "name": resolved.name,
            }
        )
    return rows


def _registered_vault_for_path(path: Path) -> dict[str, str] | None:
    target = path.expanduser().resolve()
    matches: list[tuple[int, dict[str, str]]] = []
    for vault in _registered_obsidian_vaults():
        try:
            vault_path = Path(vault["path"]).expanduser().resolve()
            target.relative_to(vault_path)
        except Exception:
            continue
        matches.append((len(str(vault_path)), vault))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def obsidian_uri_for_path(path: Path) -> str:
    target = path.expanduser().resolve()
    vault = _registered_vault_for_path(target)
    if vault:
        vault_path = Path(vault["path"]).expanduser().resolve()
        try:
            relative = target.relative_to(vault_path).as_posix()
        except Exception:
            relative = target.name
        return f"obsidian://open?vault={quote(vault['id'], safe='')}&file={quote(relative, safe='')}"
    return f"obsidian://open?path={quote(str(target), safe='')}"


def _topic_dir(topic_id: str) -> Path:
    return _topics_dir() / _safe_name(topic_id, "untitled-topic")


def _topic_note_path(topic_id: str) -> Path:
    return _topic_dir(topic_id) / "index.md"


def _topic_versions_dir(topic_id: str) -> Path:
    return _topic_dir(topic_id) / "versions"


def topic_descriptor(topic_id: str) -> dict[str, str]:
    ensure_obsidian_dirs()
    topic_note = _topic_note_path(topic_id)
    versions_dir = _topic_versions_dir(topic_id)
    return {
        "vaultPath": str(_obsidian_storage_root()),
        "topicDir": str(topic_note.parent),
        "topicNotePath": str(topic_note),
        "versionsDir": str(versions_dir),
        "uri": obsidian_uri_for_path(topic_note),
    }


def _version_note_name(entry: dict[str, Any]) -> str:
    archive_id = _safe_name(str(entry.get("archiveId", "")), "version")
    return f"{archive_id}.md"


def _format_version_label(entry: dict[str, Any]) -> str:
    raw_time = str(entry.get("updatedAt", "")).strip()
    compact_time = raw_time.replace("T", " ").replace("+00:00", " UTC").replace("Z", " UTC")
    summary = _normalize_space(str(entry.get("changeSummary", ""))) or "版本"
    return f"{compact_time} · {summary}".strip(" ·")


def _render_topic_note(
    *,
    topic_id: str,
    title: str,
    document_type_label: str,
    updated_at: str,
    workspace_document_path: str,
    topic_archive_path: str,
    content_markdown: str,
    version_entries: list[dict[str, Any]],
) -> str:
    lines = [
        "---",
        f'title: "{title}"',
        f'topic_id: "{topic_id}"',
        f'type: "{document_type_label}"',
        f'updated_at: "{updated_at}"',
        "---",
        "",
        f"# {title}",
        "",
        f"- 类型：{document_type_label}",
        f"- 最近更新：{updated_at}",
        f"- 工作区稿件：`{workspace_document_path}`",
        f"- 主题存档：`{topic_archive_path}`",
        "",
        "## 当前正文",
        "",
        (content_markdown or "").strip(),
        "",
        "## 版本",
        "",
    ]
    if version_entries:
        lines.append(f"- 最近 {len(version_entries)} 次保存保留在写作工作台的“版本”面板里。")
        lines.append("- 这里不再同步每个版本文件，避免 Obsidian 图谱被 `archive_*` 和 `document_*` 节点污染。")
    else:
        lines.append("- 暂无历史版本")
    lines.append("")
    return "\n".join(lines)


def _render_version_note(entry: dict[str, Any]) -> str:
    title = _normalize_space(str(entry.get("title", ""))) or "未命名版本"
    updated_at = str(entry.get("updatedAt", "")).strip()
    summary = _normalize_space(str(entry.get("changeSummary", ""))) or "版本"
    body = str(entry.get("contentMarkdown", "") or "").strip()
    char_count = entry.get("charCount", 0)
    lines = [
        "---",
        f'title: "{title}"',
        f'updated_at: "{updated_at}"',
        f'summary: "{summary}"',
        f"char_count: {int(char_count) if str(char_count).isdigit() else 0}",
        "---",
        "",
        f"# {title}",
        "",
        f"- 更新时间：{updated_at}",
        f"- 变化：{summary}",
        f"- 字数：{char_count}",
        "",
        "## 正文",
        "",
        body,
        "",
    ]
    return "\n".join(lines)


def sync_topic_document(
    *,
    topic_id: str,
    title: str,
    document_type_label: str,
    updated_at: str,
    workspace_document_path: str,
    topic_archive_path: str,
    content_markdown: str,
    version_entries: list[dict[str, Any]],
) -> dict[str, str]:
    ensure_obsidian_dirs()
    descriptor = topic_descriptor(topic_id)
    if not _is_formal_document_type(document_type_label) or _is_test_topic_id(topic_id):
        return {
            **descriptor,
            "synced": "false",
            "reason": "obsidian-topic-sync-skipped",
        }
    topic_note = Path(descriptor["topicNotePath"])
    versions_dir = Path(descriptor["versionsDir"])
    topic_note.parent.mkdir(parents=True, exist_ok=True)
    if versions_dir.exists():
        for stale in versions_dir.glob("*.md"):
            stale.unlink()
        try:
            versions_dir.rmdir()
        except OSError:
            pass

    topic_note.write_text(
        _render_topic_note(
            topic_id=topic_id,
            title=title,
            document_type_label=document_type_label,
            updated_at=updated_at,
            workspace_document_path=workspace_document_path,
            topic_archive_path=topic_archive_path,
            content_markdown=content_markdown,
            version_entries=version_entries,
        ),
        encoding="utf-8",
    )
    return {
        **descriptor,
        "synced": "true",
        "versionsSynced": "false",
        "reason": "obsidian-formal-topic-index-only",
    }


def _memory_bucket(kind: str) -> str:
    return {
        "banned_line": "banned",
        "approved_line": "approved",
        "rewrite_pair": "rewrite-pairs",
        "rule": "rules",
    }.get(kind, "misc")


def _memory_note_path(entry: dict[str, Any]) -> Path:
    status = "deleted" if str(entry.get("status", "")).strip() == "deleted" else "active"
    kind = _memory_bucket(str(entry.get("kind", "")).strip())
    note_id = _safe_name(str(entry.get("id", "")), "memory")
    return _style_memory_dir() / status / kind / f"{note_id}.md"


def _render_memory_note(entry: dict[str, Any]) -> str:
    title = {
        "banned_line": "讨厌句",
        "approved_line": "喜欢句",
        "rewrite_pair": "改写对",
        "rule": "规则",
    }.get(str(entry.get("kind", "")).strip(), "风格记忆")
    source_text = str(entry.get("source_text", "")).strip() or str(entry.get("sourceText", "")).strip()
    replacement_text = str(entry.get("replacement_text", "")).strip() or str(entry.get("replacementText", "")).strip()
    reason = str(entry.get("reason", "")).strip()
    tags = entry.get("tags") or []
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    usage_count = int(entry.get("usage_count", 0) or 0)
    last_used_at = str(entry.get("last_used_at", "")).strip()
    if not isinstance(tags, list):
        tags = [str(tags)]
    lines = [
        "---",
        f'title: "{title}"',
        f'id: "{str(entry.get("id", "")).strip()}"',
        f'kind: "{str(entry.get("kind", "")).strip()}"',
        f'status: "{str(entry.get("status", "active")).strip() or "active"}"',
        f'strength: "{str(entry.get("strength", "")).strip()}"',
        f'scope: "{str(entry.get("scope", "")).strip()}"',
        f'origin: "{str(entry.get("origin", "")).strip()}"',
        "---",
        "",
        f"# {title}",
        "",
        "## 原句",
        "",
        source_text or "（空）",
        "",
    ]
    if replacement_text:
        lines.extend(["## 改法", "", replacement_text, ""])
    if reason:
        lines.extend(["## 原因", "", reason, ""])
    scene_bits: list[str] = []
    variant_label = _normalize_space(str(meta.get("variantLabel", "")))
    if variant_label:
        scene_bits.append(f"- 候选标签：{variant_label}")
    variant_move = _normalize_space(str(meta.get("variantMove", "")))
    if variant_move:
        scene_bits.append(f"- 改法动作：{variant_move}")
    audit_issue = meta.get("auditIssue") if isinstance(meta.get("auditIssue"), dict) else {}
    audit_category = _normalize_space(str(audit_issue.get("category", "")))
    if audit_category:
        scene_bits.append(f"- 触发问题：{audit_category}")
    if meta.get("paragraphAssist"):
        scene_bits.append("- 来源：补段候选")
    source_prompt = _normalize_space(str(meta.get("sourcePrompt", "")))
    if source_prompt:
        scene_bits.append(f"- 当时需求：{source_prompt}")
    if scene_bits:
        lines.extend(["## 场景", "", *scene_bits, ""])
    if tags:
        lines.extend(["## 标签", "", "- " + "\n- ".join(str(tag) for tag in tags if str(tag).strip()), ""])
    if usage_count or last_used_at:
        lines.extend(
            [
                "## 使用情况",
                "",
                f"- 记录次数：{usage_count}",
                f"- 最近进入上下文：{last_used_at or '暂无'}",
                "",
            ]
        )
    return "\n".join(lines)


def sync_style_memory_entry(entry: dict[str, Any]) -> dict[str, str]:
    ensure_obsidian_dirs()
    target = _style_memory_index_path()
    _ensure_style_memory_index()

    return {
        "notePath": str(target),
        "uri": obsidian_uri_for_path(target),
        "synced": "false",
        "reason": "style-memory-node-sync-disabled",
    }


def open_in_obsidian(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    vault = _registered_vault_for_path(target)
    if vault is None:
        storage_root = _obsidian_storage_root()
        return {
            "ok": False,
            "blocked": True,
            "reason": "vault-not-registered",
            "message": f"已同步到镜像，但 `{storage_root}` 还不是 Obsidian 已注册 vault，所以没有自动打开。",
            "path": str(target),
            "vaultPath": str(storage_root.resolve()),
            "registeredVaults": [item["path"] for item in _registered_obsidian_vaults()],
            "uri": "",
            "stdout": "",
            "stderr": "",
        }
    uri = obsidian_uri_for_path(target)
    result = subprocess.run(["open", uri], text=True, capture_output=True, check=False)
    return {
        "ok": result.returncode == 0,
        "blocked": False,
        "uri": uri,
        "path": str(target),
        "vaultPath": vault["path"],
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
