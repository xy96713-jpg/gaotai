#!/usr/bin/env python3
"""Product acceptance matrix for the local /video-analysis workspace.

This is a lightweight, repeatable gate. It does not claim universal platform
download success. It checks whether the product contract is currently proven:
clean entry, real progress, local video success for supported routes, local
upload, and honest auth/download failure.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".cache" / "video-analysis-acceptance-matrix"
JOB_DIR = ROOT / ".cache" / "video-analysis" / "jobs"
REPORTS = {
    "clean_entry": ROOT / ".cache" / "video-analysis-clean-entry" / "latest.json",
    "progress": ROOT / ".cache" / "video-analysis-progress-smoke" / "latest.json",
    "auth_failure": ROOT / ".cache" / "video-analysis-auth-failure-smoke" / "latest.json",
    "local_upload": ROOT / ".cache" / "video-analysis-local-upload-smoke" / "latest.json",
    "browser_matrix": ROOT / ".cache" / "video-analysis-browser-matrix" / "latest.json",
    "professional_matrix": ROOT / ".cache" / "video-analysis-professional-matrix" / "latest.json",
}


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def nested_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def get_video_embed(job: dict[str, Any]) -> dict[str, Any]:
    summary = nested_dict(job.get("summary"))
    for candidate in (
        summary.get("videoEmbed"),
        job.get("videoEmbed"),
        nested_dict(job.get("result")).get("videoEmbed"),
    ):
        if isinstance(candidate, dict):
            return candidate
    return {}


def local_path_exists(embed: dict[str, Any]) -> bool:
    if embed.get("type") != "local":
        return False
    local_path = str(embed.get("localPath") or "")
    return bool(local_path and Path(local_path).exists())


def iter_jobs(job_dir: Path = JOB_DIR) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    if not job_dir.exists():
        return jobs
    for path in job_dir.glob("*.json"):
        data = read_json(path)
        if not data:
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        data["_path"] = str(path)
        data["_mtime"] = mtime
        jobs.append(data)
    return sorted(jobs, key=lambda item: float(item.get("_mtime") or 0), reverse=True)


def find_latest_local_job(platform: str, jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for job in jobs:
        if job.get("status") != "done":
            continue
        summary = nested_dict(job.get("summary"))
        actual_platform = str(summary.get("platform") or job.get("platform") or "")
        if actual_platform != platform:
            continue
        embed = get_video_embed(job)
        if local_path_exists(embed):
            return job
    return None


def find_latest_login_failure(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for job in jobs:
        if job.get("status") != "error":
            continue
        failure = nested_dict(job.get("failure"))
        raw = " ".join(
            str(value or "")
            for value in (
                failure.get("title"),
                failure.get("reason"),
                job.get("message"),
                job.get("error"),
            )
        )
        if any(token in raw for token in ("登录", "验证", "not a bot", "Sign in", "timeout", "超时")):
            return job
    return None


def report_row(name: str, label: str, ok: bool, evidence: str, next_step: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "ok": bool(ok),
        "evidence": evidence,
        "nextStep": next_step,
    }


def build_matrix(
    *,
    reports: dict[str, Path] = REPORTS,
    job_dir: Path = JOB_DIR,
    out_dir: Path = OUT_DIR,
) -> dict[str, Any]:
    payloads = {name: read_json(path) for name, path in reports.items()}
    jobs = iter_jobs(job_dir)
    rows: list[dict[str, Any]] = []

    clean = payloads.get("clean_entry") or {}
    rows.append(
        report_row(
            "clean_entry",
            "打开页面是干净入口",
            bool(clean.get("ok")),
            str(clean.get("results", [{}])[0].get("value", {}).get("title") if isinstance(clean.get("results"), list) and clean.get("results") else clean.get("error") or ""),
            "重新跑 node tools/video_analysis_clean_entry_smoke.mjs",
        )
    )

    progress = payloads.get("progress") or {}
    progress_text = str(progress.get("progressText") or "")
    unknown_text = str(progress.get("unknownTotalProgressText") or "")
    progress_ok = bool(progress.get("ok")) and "保存 取图 字幕 整理" not in progress_text and "保存 取图 字幕 整理" not in unknown_text
    rows.append(
        report_row(
            "real_progress",
            "下载进度不伪装",
            progress_ok,
            f"{progress.get('width') or 'no width'}；未知总量条隐藏={progress.get('unknownTotalTrackHidden')}",
            "重新跑 node tools/video_analysis_progress_smoke.mjs",
        )
    )

    browser = payloads.get("browser_matrix") or {}
    scenarios = browser.get("scenarios") if isinstance(browser.get("scenarios"), list) else []
    by_name = {str(item.get("name") or ""): item for item in scenarios if isinstance(item, dict)}
    strict_remote = by_name.get("required_local_remote_cache_fails") or {}
    rows.append(
        report_row(
            "strict_remote_block",
            "只有内嵌缓存会被拦住",
            bool(strict_remote.get("ok")),
            str(strict_remote.get("url") or strict_remote.get("error") or ""),
            "重新跑 node tools/video_analysis_browser_matrix_smoke.mjs",
        )
    )
    caption_recovery = by_name.get("stale_caption_cache_recovers") or {}
    rows.append(
        report_row(
            "caption_cache_recovery",
            "旧任务能恢复缓存字幕",
            bool(caption_recovery.get("ok")),
            str(caption_recovery.get("url") or caption_recovery.get("error") or ""),
            "重新跑 node tools/video_analysis_browser_matrix_smoke.mjs",
        )
    )

    for platform, label in (("youtube", "YouTube 有本地视频样本"), ("bilibili", "B站有本地视频样本")):
        job = find_latest_local_job(platform, jobs)
        embed = get_video_embed(job or {})
        rows.append(
            report_row(
                f"{platform}_local",
                label,
                bool(job),
                f"{job.get('id')} · {embed.get('localPath')}" if job else "没有找到可用本地视频任务",
                "跑一个短公开视频样本并确认 videoEmbed.type=local",
            )
        )

    local_upload = payloads.get("local_upload") or {}
    final_state = nested_dict(local_upload.get("finalState"))
    rows.append(
        report_row(
            "local_upload",
            "本地视频可直接分析",
            bool(local_upload.get("ok")) and "已保存本地" in str(final_state.get("playback") or ""),
            str(final_state.get("href") or local_upload.get("error") or ""),
            "重新跑本地上传烟测",
        )
    )

    auth = payloads.get("auth_failure") or {}
    login_failure = find_latest_login_failure(jobs)
    rows.append(
        report_row(
            "auth_failure",
            "登录/验证失败能说明白",
            bool(auth.get("ok")) and ("打开 YouTube 登录" in str(auth.get("failureText") or "") or login_failure is not None),
            str(auth.get("failureText") or (login_failure or {}).get("id") or ""),
            "重新跑 node tools/video_analysis_auth_failure_smoke.mjs",
        )
    )

    professional = payloads.get("professional_matrix") or {}
    platforms = professional.get("platforms") if isinstance(professional.get("platforms"), list) else []
    platform_rows = {
        str(item.get("platform") or ""): item
        for item in platforms
        if isinstance(item, dict)
    }
    for platform, label in (("youtube", "YouTube 能生成专业 PPT"), ("bilibili", "B站能生成专业 PPT")):
        item = platform_rows.get(platform) or {}
        candidate = nested_dict(item.get("candidate"))
        smoke = nested_dict(item.get("smoke"))
        parsed = nested_dict(smoke.get("parsed"))
        ppt_step = ""
        for step in parsed.get("steps") or []:
            if isinstance(step, dict) and step.get("name") == "download PPTX and inspect content":
                value = nested_dict(step.get("value"))
                ppt_step = f"{value.get('slides')} 页 / {value.get('media')} 图"
                break
        rows.append(
            report_row(
                f"{platform}_professional_ppt",
                label,
                bool(item.get("ok")),
                f"{candidate.get('id') or ''} · {candidate.get('uniqueScreenshots') or 0} 张不同截图 · {ppt_step}",
                "重新跑 node tools/video_analysis_professional_matrix.mjs",
            )
        )

    core_names = {
        "clean_entry",
        "real_progress",
        "strict_remote_block",
        "caption_cache_recovery",
        "youtube_local",
        "bilibili_local",
        "local_upload",
        "auth_failure",
        "youtube_professional_ppt",
        "bilibili_professional_ppt",
    }
    blockers = [row for row in rows if row["name"] in core_names and not row["ok"]]
    warnings: list[str] = []
    if len(jobs) > 250:
        warnings.append(f"任务缓存较多：{len(jobs)} 个，后续需要清理策略。")

    matrix = {
        "ok": not blockers,
        "verdict": "SELF_USE_READY" if not blockers else "BLOCKED",
        "generatedAt": utc_now(),
        "rows": rows,
        "blockers": blockers,
        "warnings": warnings,
        "jobCount": len(jobs),
        "contract": [
            "成功必须有本地视频文件。",
            "下载中只显示真实下载数据，未知总量不显示假进度条。",
            "被登录、验证、格式或网络拦住时停止分析，不生成伪总结。",
            "支持范围先固定为 YouTube、B站和本地视频上传。",
        ],
    }
    write_report(matrix, out_dir)
    return matrix


def write_report(matrix: dict[str, Any], out_dir: Path = OUT_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"
    json_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# 视频材料验收矩阵：{matrix['verdict']}",
        "",
        f"- 生成时间：{matrix['generatedAt']}",
        f"- 任务缓存：{matrix['jobCount']} 个",
        "",
        "## 产品契约",
        "",
    ]
    lines.extend(f"- {item}" for item in matrix["contract"])
    lines.extend(["", "## 场景", "", "| 场景 | 状态 | 证据 |", "| --- | --- | --- |"])
    for row in matrix["rows"]:
        evidence = str(row.get("evidence") or "").replace("|", "/").replace("\n", " ")
        if len(evidence) > 150:
            evidence = evidence[:147] + "..."
        lines.append(f"| {row['label']} | {'PASS' if row['ok'] else 'BLOCK'} | {evidence} |")
    if matrix["blockers"]:
        lines.extend(["", "## 阻断", ""])
        lines.extend(f"- {row['label']}：{row['nextStep']}" for row in matrix["blockers"])
    if matrix["warnings"]:
        lines.extend(["", "## 预警", ""])
        lines.extend(f"- {item}" for item in matrix["warnings"])
    md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    matrix = build_matrix()
    print(
        json.dumps(
            {
                "ok": matrix["ok"],
                "verdict": matrix["verdict"],
                "json": str(OUT_DIR / "latest.json"),
                "markdown": str(OUT_DIR / "latest.md"),
                "blockers": [row["name"] for row in matrix["blockers"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if matrix["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
