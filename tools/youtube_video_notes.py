#!/usr/bin/env python3
"""Unified video analysis pipeline for content/style research.

Resolution order:
1. Pull public metadata with yt-dlp
2. Try local video parser transcript (best when available)
3. Try yt-dlp subtitles / auto-captions
4. Optionally transcribe downloaded audio with faster-whisper / whisper
5. Build a structured analysis package with pluggable reasoning backends
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import html
import importlib.util
import importlib.metadata
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = WORKSPACE / ".cache" / "video-analysis"
DEFAULT_VIDEO_PARSER = os.environ.get("VIDEO_PARSER_BASE_URL", "http://127.0.0.1:5201")
CHANNEL_PROFILE_PATH = WORKSPACE / "CHANNEL.md"
SUPPORTED_RULES_BACKENDS = {"rules", "openai-compatible", "mlx-vlm-local"}
BUNDLED_BIN_DIR = WORKSPACE / "tools" / "bin"
BGUTIL_PROVIDER_HOME = Path(
    os.environ.get("YOUTUBE_NOTES_BGUTIL_PROVIDER_HOME", WORKSPACE / ".cache" / "bgutil-ytdlp-pot-provider")
).expanduser()
BGUTIL_PROVIDER_SERVER_HOME = Path(
    os.environ.get("YOUTUBE_NOTES_BGUTIL_SERVER_HOME", BGUTIL_PROVIDER_HOME / "server")
).expanduser()
BGUTIL_PROVIDER_BASE_URL = os.environ.get("YOUTUBE_NOTES_BGUTIL_BASE_URL", "http://127.0.0.1:4416").strip()
BGUTIL_PROVIDER_LOG = WORKSPACE / ".cache" / "video-analysis" / "bgutil-provider.log"
LOCAL_VLM_PYTHON = WORKSPACE / ".venv-local-vlm" / "bin" / "python"
WHISPER_CPP_ROOT = WORKSPACE / ".cache" / "external-asr" / "whisper.cpp"
WHISPER_CPP_CLI = WHISPER_CPP_ROOT / "build" / "bin" / "whisper-cli"
WHISPER_CPP_MODELS = WHISPER_CPP_ROOT / "models"
ASR_BACKEND_CHOICES = {"auto", "whisper-cpp", "lightning-mlx", "mlx-whisper", "faster-whisper", "whisper"}
_YTDLP_POT_LOGGER_COMPAT_APPLIED = False
_BGUTIL_PROVIDER_STARTED = False


def optional_module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("_") or "video"


def compact_text(value: str, limit: int = 4000) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def parse_json_object_from_text(value: str) -> dict[str, Any]:
    value = (value or "").strip()
    if not value:
        raise ValueError("Empty model response")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model response")
        return json.loads(value[start : end + 1])


def normalize_visual_summary(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if not value:
        return ""
    if value.startswith("<") and ">" not in value and len(value) < 40:
        return ""
    if value.lower().startswith("<points:"):
        return ""
    return value


def describe_visual_asset(asset: dict[str, Any]) -> str:
    asset_type = str(asset.get("type") or "image")
    if asset_type == "thumbnail":
        return "封面"
    if asset_type == "frame":
        timestamp = asset.get("timestamp")
        if isinstance(timestamp, (int, float)):
            return f"{format_timestamp(timestamp)} 关键帧"
        return "关键帧"
    return asset_type


def format_duration(seconds: Any) -> str:
    try:
        total = int(seconds)
    except Exception:
        return "unknown"
    return f"{total // 60}:{total % 60:02d}"


def format_timestamp(seconds: Any) -> str:
    try:
        total = int(float(seconds))
    except Exception:
        return "00:00"
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_clock_to_seconds(value: str) -> int:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Unsupported clock format: {value}")


def parse_whisper_cpp_clock_to_seconds(value: str) -> float:
    match = re.match(r"^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{3})$", str(value).strip())
    if not match:
        return 0.0
    return (
        int(match.group("h")) * 3600
        + int(match.group("m")) * 60
        + int(match.group("s"))
        + int(match.group("ms")) / 1000.0
    )


def clean_whisper_cpp_text(value: str) -> str:
    value = re.sub(r"\[_BEG_\]|\[_TT_\d+\]", "", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def remove_user_banned_report_phrasing(value: str) -> str:
    replacements = {
        "不是标题，而是": "重点落在",
        "而不是复述结论": "少复述结论",
        "而不是宏大趋势复述": "少做宏大趋势复述",
        "真正的核心命题不是标题表面那句话，而是": "核心命题是",
        "真正要讲的不是": "要讲的是",
        "不是表面问题，而是": "核心落在",
        "真正重要的不是灵感，而是": "它更看重",
        "不是聪明，而是": "更依赖",
        "不是空聊": "有可判断的材料",
        "不急着给鼓励，而是": "先",
        "不是不能做，是大多数人还没到那个阶段": "多数人还没准备好",
        "真正想回答的不是表面问题，而是": "想回答的是",
        "不是因为它多新，而是": "原因在于",
        "不是最后那一下生成，而是": "价值集中在",
        "这已经不是重点了": "这个问题可以先放一边",
        "不是它能不能写几句漂亮话，而是": "关键看",
        "不是 AI 帮你润色两句，而是": "核心在于",
        "不是更会聊天的 AI，而是": "需要的是",
        "门槛不是消失了，而是": "门槛转到了",
        "不是因为它万能，而是": "原因在于",
    }
    for source, replacement in replacements.items():
        value = value.replace(source, replacement)
    value = re.sub(r"不是(.{0,28})，而是", r"重点是", value)
    value = re.sub(r"不是(.{0,28})而是", r"重点是", value)
    return value


def clean_report_text_object(value: Any) -> Any:
    if isinstance(value, str):
        return remove_user_banned_report_phrasing(value)
    if isinstance(value, list):
        return [clean_report_text_object(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_report_text_object(item) for key, item in value.items()}
    return value


def build_comment_preview(info: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    comments = info.get("comments")
    if not isinstance(comments, list):
        return preview
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        text = compact_text(str(comment.get("text") or ""), 180)
        if not text:
            continue
        item: dict[str, Any] = {"text": text}
        author = compact_text(str(comment.get("author") or comment.get("author_id") or ""), 40)
        if author:
            item["author"] = author
        like_count = comment.get("like_count")
        if isinstance(like_count, int):
            item["like_count"] = like_count
        preview.append(item)
        if len(preview) >= limit:
            break
    return preview


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "bilibili.com" in host or "b23.tv" in host:
        return "bilibili"
    if "douyin.com" in host or "iesdouyin.com" in host:
        return "douyin"
    return "generic"


def should_try_video_parser(platform: str) -> bool:
    return platform == "youtube"


def default_browser_cookie_source(platform: str) -> str | None:
    env_value = os.environ.get("YOUTUBE_NOTES_COOKIES_FROM_BROWSER", "").strip()
    if env_value:
        return None if env_value.lower() in {"0", "false", "none", "off", "no"} else env_value
    if platform in {"youtube", "bilibili", "douyin"}:
        return "chrome"
    return None


def resolve_cookies_from_browser(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if value.lower() in {"0", "false", "none", "off", "no"}:
        return "none"
    return value


def apply_cookie_options(opts: dict[str, Any], platform: str, cookies_file: str | None, cookies_from_browser: str | None) -> str:
    if cookies_file:
        opts["cookiefile"] = cookies_file
        return f"file:{cookies_file}"
    effective_browser = resolve_cookies_from_browser(cookies_from_browser)
    if effective_browser == "none":
        return "disabled"
    effective_browser = effective_browser or default_browser_cookie_source(platform)
    if effective_browser:
        opts["cookiesfrombrowser"] = (effective_browser,)
        return f"browser:{effective_browser}"
    return "none"


def parse_description_chapters(description: str) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for raw_line in (description or "").splitlines():
        line = raw_line.strip()
        match = re.match(r"^(?P<clock>\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<title>.+?)\s*$", line)
        if not match:
            continue
        chapters.append(
            {
                "start": parse_clock_to_seconds(match.group("clock")),
                "title": match.group("title").strip(),
            }
        )
    return chapters


def read_vtt_text(path: Path) -> str:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT":
            continue
        if "-->" in line:
            continue
        if line.startswith(("Kind:", "Language:")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    return "\n".join(lines)


def parse_subtitle_clock(value: str) -> float:
    value = value.strip().replace(",", ".")
    parts = value.split(":")
    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0.0
    return 0.0


def subtitle_text_to_items(text: str, *, default_duration: float = 3.0) -> list[dict[str, Any]]:
    """Parse simple VTT/SRT text into transcript items.

    yt-dlp exposes Bilibili AI subtitles as SRT `data`, while YouTube usually
    writes VTT files. Keep the parser intentionally small: we only need text,
    start, and duration for downstream summaries.
    """
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
    items: list[dict[str, Any]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        timing_index = next((idx for idx, line in enumerate(lines) if "-->" in line), -1)
        if timing_index < 0:
            continue
        timing = lines[timing_index]
        start_text, _, end_text = timing.partition("-->")
        start = parse_subtitle_clock(start_text.strip())
        end = parse_subtitle_clock(end_text.split()[0].strip())
        duration = max(0.0, end - start) if end else default_duration
        text_lines = lines[timing_index + 1 :]
        cleaned_lines: list[str] = []
        for line in text_lines:
            if line.isdigit():
                continue
            line = re.sub(r"<[^>]+>", "", line)
            line = re.sub(r"\s+", " ", html.unescape(line)).strip()
            if line:
                cleaned_lines.append(line)
        text_value = " ".join(cleaned_lines).strip()
        if text_value:
            items.append({"text": text_value, "start": start, "duration": duration})
    if items:
        return items

    # Last-resort plain text parsing for subtitle-like files without timing.
    start = 0.0
    for raw in text.splitlines():
        line = re.sub(r"<[^>]+>", "", raw).strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        if line.startswith(("Kind:", "Language:")):
            continue
        line = re.sub(r"\s+", " ", html.unescape(line)).strip()
        if line:
            items.append({"text": line, "start": start, "duration": default_duration})
            start += default_duration
    return items


def ass_subtitle_to_items(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        start = parse_subtitle_clock(parts[1])
        end = parse_subtitle_clock(parts[2])
        body = parts[9]
        body = re.sub(r"\{[^}]*\}", "", body)
        body = re.sub(r"\\+[Nn]", " ", body)
        body = re.sub(r"\s+", " ", html.unescape(body)).strip()
        if body:
            items.append({"text": body, "start": start, "duration": max(0.0, end - start)})
    return items


def normalize_transcript_items(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items or []:
        text = re.sub(r"\s+", " ", str(item.get("text") or "")).strip()
        if not text:
            continue
        try:
            start = float(item.get("start") or 0)
        except Exception:
            start = 0.0
        try:
            duration = float(item.get("duration") or 0)
        except Exception:
            duration = 0.0
        normalized.append({"text": text, "start": start, "duration": duration})
    return normalized


def youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtu.be" in host:
        return parsed.path.strip("/").split("/")[0]
    if "youtube.com" in host:
        query = dict(part.split("=", 1) for part in parsed.query.split("&") if "=" in part)
        return query.get("v", "")
    return ""


def rosetta_slug(value: str, *, compact: bool = False) -> str:
    value = html.unescape(value or "").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"['’`]", "", value)
    value = re.sub(r"[^a-z0-9]+", "" if compact else "-", value)
    value = value.strip("-")
    return value


def transcript_text_to_items(text: str, segment_words: int = 42) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[。！？!?])\s+|(?<=\.)\s+(?=[A-Z\"'])", text)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for piece in pieces:
        words = piece.split()
        if not words:
            continue
        if len(words) > segment_words:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_words = 0
            for index in range(0, len(words), segment_words):
                chunks.append(" ".join(words[index : index + segment_words]).strip())
            continue
        if current and current_words + len(words) > segment_words:
            chunks.append(" ".join(current).strip())
            current = []
            current_words = 0
        current.append(piece.strip())
        current_words += len(words)
    if current:
        chunks.append(" ".join(current).strip())
    return [
        {"text": chunk, "start": float(index * 12), "duration": 12.0}
        for index, chunk in enumerate(chunks)
        if chunk
    ]


def fetch_rosetta_transcript(url: str, title: str = "", channel: str = "") -> tuple[list[dict[str, Any]], str | None]:
    video_id = youtube_video_id(url)
    if not video_id:
        return [], "rosetta-fallback-skipped:no-video-id"
    search_url = f"https://rosetta.to/search?q={video_id}"
    try:
        import requests

        candidate_urls: list[str] = []
        channel_slug = rosetta_slug(channel, compact=True)
        title_slug = rosetta_slug(title)
        if channel_slug and title_slug:
            candidate_urls.append(f"https://rosetta.to/u/{channel_slug}/{title_slug}")

        for candidate_url in candidate_urls:
            candidate_response = requests.get(candidate_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            if candidate_response.status_code >= 400:
                continue
            transcript = extract_transcript_from_html(candidate_response.text)
            if transcript:
                return transcript_text_to_items(transcript), f"rosetta-transcript:{candidate_url}"

        search_response = requests.get(search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        search_response.raise_for_status()
        candidates = re.findall(r'href="([^"]+)"', search_response.text)
        archive_path = ""
        for candidate in candidates:
            decoded = html.unescape(candidate)
            if decoded.startswith("/u/") and video_id in search_response.text:
                archive_path = decoded
                break
        if not archive_path:
            direct_match = re.search(r'href="([^"]+/[^"]*?)"[^>]*>\s*[^<]*(?:Watch on YouTube|Full transcript)', search_response.text)
            if direct_match:
                archive_path = html.unescape(direct_match.group(1))
        if archive_path.startswith("http"):
            archive_url = archive_path
        elif archive_path:
            archive_url = "https://rosetta.to" + archive_path
        else:
            glasp_url = f"https://glasp.co/youtube/{video_id}"
            glasp_response = requests.get(glasp_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            if glasp_response.status_code >= 400:
                return [], "rosetta-fallback-no-archive"
            archive_url = glasp_url
            html_text = glasp_response.text
            transcript = extract_transcript_from_html(html_text)
            if transcript:
                return transcript_text_to_items(transcript), f"glasp-transcript:{glasp_url}"
            return [], "rosetta-fallback-no-transcript"
        archive_response = requests.get(archive_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        archive_response.raise_for_status()
        transcript = extract_transcript_from_html(archive_response.text)
        if transcript:
            return transcript_text_to_items(transcript), f"rosetta-transcript:{archive_url}"
        return [], "rosetta-fallback-no-transcript"
    except Exception as exc:
        return [], f"rosetta-fallback-error:{exc}"


def extract_transcript_from_html(html_text: str) -> str:
    patterns = [
        r'<section[^>]+id="transcript"[\s\S]*?<div[^>]+class="prose"[^>]*>\s*<p>(?P<body>[\s\S]*?)</p>\s*</div>',
        r"<h2[^>]*>\s*Transcript\s*</h2>[\s\S]*?<p[^>]*>(?P<body>[\s\S]*?)</p>",
        r"##\s*Transcript(?P<body>[\s\S]+?)(?:##\s|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.I)
        if not match:
            continue
        body = match.group("body")
        body = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.I)
        body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.I)
        body = re.sub(r"<[^>]+>", " ", body)
        body = html.unescape(body)
        body = re.sub(r"\s+", " ", body).strip()
        if len(body) >= 300:
            return body
    return ""


def transcript_items_to_text(items: list[dict[str, Any]], with_timestamps: bool = True) -> str:
    lines: list[str] = []
    for item in items:
        text = item["text"]
        if with_timestamps:
            lines.append(f"[{format_timestamp(item['start'])}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def write_transcript_artifacts(
    out_dir: Path,
    video_slug: str,
    transcript_items: list[dict[str, Any]],
    transcript_source: str,
    transcript_notes: list[str],
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_json_path = out_dir / f"{video_slug}_transcript.json"
    transcript_md_path = out_dir / f"{video_slug}_transcript.md"
    payload = {
        "source": transcript_source,
        "notes": transcript_notes,
        "count": len(transcript_items),
        "segments": normalize_transcript_items(transcript_items),
    }
    transcript_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_lines = [
        "# Transcript",
        "",
        f"- Source: {transcript_source}",
        f"- Segment count: {len(transcript_items)}",
        f"- Notes: {', '.join(transcript_notes) or 'none'}",
        "",
        transcript_items_to_text(transcript_items, with_timestamps=True) if transcript_items else "(No transcript content resolved.)",
        "",
    ]
    transcript_md_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    return transcript_json_path, transcript_md_path


def build_outline_sections(
    transcript: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    fallback_window_seconds: int = 240,
) -> list[dict[str, Any]]:
    transcript = normalize_transcript_items(transcript)
    if not transcript:
        return []

    if not chapters:
        chapters = []
        current_start = int(transcript[0]["start"])
        end_time = int(transcript[-1]["start"])
        index = 1
        while current_start <= end_time:
            chapters.append({"start": current_start, "title": f"片段 {index}"})
            current_start += fallback_window_seconds
            index += 1

    sections: list[dict[str, Any]] = []
    sorted_chapters = sorted(chapters, key=lambda item: item["start"])
    for idx, chapter in enumerate(sorted_chapters):
        start = chapter["start"]
        end = sorted_chapters[idx + 1]["start"] if idx + 1 < len(sorted_chapters) else None
        chunk = [
            item
            for item in transcript
            if item["start"] >= start and (end is None or item["start"] < end)
        ]
        if not chunk:
            continue
        summary = compact_text(" ".join(item["text"] for item in chunk), 260)
        sections.append(
            {
                "title": chapter["title"],
                "start": start,
                "end": end,
                "summary": summary,
                "line_count": len(chunk),
            }
        )
    return sections


def build_key_points(sections: list[dict[str, Any]], transcript: list[dict[str, Any]]) -> list[str]:
    if sections:
        return [
            f"{format_timestamp(section['start'])} {section['title']}：{section['summary']}"
            for section in sections[:6]
        ]
    transcript = normalize_transcript_items(transcript)
    points: list[str] = []
    for item in transcript[:8]:
        points.append(f"{format_timestamp(item['start'])} {item['text']}")
    return points


def resolve_cover_assets(info: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    thumbnail = info.get("thumbnail")
    if thumbnail:
        assets.append({"type": "thumbnail", "url": thumbnail, "source": "metadata-thumbnail"})

    thumbnails = info.get("thumbnails") or []
    for item in thumbnails[-3:]:
        url = item.get("url")
        if not url or any(asset.get("url") == url for asset in assets):
            continue
        assets.append({"type": "thumbnail", "url": url, "source": "metadata-thumbnails"})
    return assets


def resolve_binary(name: str) -> str | None:
    bundled = BUNDLED_BIN_DIR / name
    if bundled.exists():
        return str(bundled)
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_path and Path(ffmpeg_path).exists():
                return ffmpeg_path
        except Exception:
            pass
    return shutil.which(name)


def get_youtube_dl():
    try:
        from yt_dlp import YoutubeDL
    except Exception as exc:
        raise RuntimeError(f"yt-dlp unavailable: {exc}") from exc
    ensure_ytdlp_pot_logger_compat()
    return YoutubeDL


def ensure_ytdlp_pot_logger_compat() -> None:
    """Allow bgutil POT providers using debug(..., once=True) on yt-dlp builds.

    Recent yt-dlp content-provider loggers accept `warning(..., once=True)` but
    some builds still expose `debug(message)` only, while bgutil-ytdlp-pot-provider
    1.3.1 calls `debug(..., once=True)`. Patch the logger method at runtime so a
    provider diagnostics line does not abort the whole video download.
    """
    global _YTDLP_POT_LOGGER_COMPAT_APPLIED
    if _YTDLP_POT_LOGGER_COMPAT_APPLIED:
        return
    try:
        from yt_dlp.extractor.youtube.pot._director import YoutubeIEContentProviderLogger
    except Exception:
        _YTDLP_POT_LOGGER_COMPAT_APPLIED = True
        return

    original_debug = getattr(YoutubeIEContentProviderLogger, "debug", None)
    if not callable(original_debug):
        _YTDLP_POT_LOGGER_COMPAT_APPLIED = True
        return
    if getattr(original_debug, "_a1_once_compat", False):
        _YTDLP_POT_LOGGER_COMPAT_APPLIED = True
        return

    def debug_once_compat(self, message: str, *args: Any, once: bool = False, **kwargs: Any) -> Any:
        if "only_once" in kwargs:
            once = bool(kwargs.pop("only_once"))
        if once:
            try:
                return self._ie.write_debug(f"[{self._prefix}] {message}", only_once=True)
            except Exception:
                return original_debug(self, message)
        return original_debug(self, message)

    debug_once_compat._a1_once_compat = True  # type: ignore[attr-defined]
    YoutubeIEContentProviderLogger.debug = debug_once_compat
    _YTDLP_POT_LOGGER_COMPAT_APPLIED = True


def bgutil_provider_ping(timeout: float = 1.5) -> bool:
    if not BGUTIL_PROVIDER_BASE_URL:
        return False
    try:
        req = Request(f"{BGUTIL_PROVIDER_BASE_URL.rstrip('/')}/ping", headers={"Accept": "application/json"})
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="ignore") or "{}")
        return bool(payload.get("version"))
    except Exception:
        return False


def bgutil_provider_server_entry() -> Path | None:
    candidate = BGUTIL_PROVIDER_SERVER_HOME / "build" / "main.js"
    if candidate.exists():
        return candidate
    return None


def bgutil_provider_script_entry() -> Path | None:
    candidate = BGUTIL_PROVIDER_SERVER_HOME / "build" / "generate_once.js"
    if candidate.exists():
        return candidate
    return None


def ensure_bgutil_provider_server(notes: list[str] | None = None) -> bool:
    """Start the local bgutil POT server when it is installed but not running."""
    global _BGUTIL_PROVIDER_STARTED
    if bgutil_provider_ping():
        if notes is not None:
            notes.append("po-token-server:ready")
        return True

    server_entry = bgutil_provider_server_entry()
    node_path = shutil.which("node") or "/Applications/Codex.app/Contents/Resources/node"
    if not server_entry or not node_path or not Path(node_path).exists():
        if notes is not None:
            if bgutil_provider_script_entry():
                notes.append("po-token-server:not-running-script-available")
            else:
                notes.append("po-token-server:not-installed")
        return False

    if not _BGUTIL_PROVIDER_STARTED:
        try:
            BGUTIL_PROVIDER_LOG.parent.mkdir(parents=True, exist_ok=True)
            log_file = BGUTIL_PROVIDER_LOG.open("a", encoding="utf-8")
            subprocess.Popen(
                [node_path, str(server_entry)],
                cwd=str(BGUTIL_PROVIDER_SERVER_HOME),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            _BGUTIL_PROVIDER_STARTED = True
            if notes is not None:
                notes.append("po-token-server:start")
        except Exception as exc:
            if notes is not None:
                notes.append(f"po-token-server:start-failed:{compact_text(str(exc), 120)}")
            return False

    for _ in range(20):
        if bgutil_provider_ping(timeout=0.5):
            if notes is not None:
                notes.append("po-token-server:ready")
            return True
        time.sleep(0.25)
    if notes is not None:
        notes.append("po-token-server:start-timeout")
    return False


def build_ytdlp_runtime_opts() -> dict[str, Any]:
    opts: dict[str, Any] = {}
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin:
        opts["ffmpeg_location"] = ffmpeg_bin
        try:
            from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor

            FFmpegPostProcessor._ffmpeg_location.set(ffmpeg_bin)
        except Exception:
            pass

    node_path = shutil.which("node") or "/Applications/Codex.app/Contents/Resources/node"
    if node_path and Path(node_path).exists():
        opts["js_runtimes"] = {"node": {"path": node_path}}

    return opts


def yt_dlp_impersonate_target() -> Any | None:
    if not importlib.util.find_spec("curl_cffi"):
        return None
    target_name = os.environ.get("YOUTUBE_NOTES_IMPERSONATE_TARGET", "chrome").strip().lower()
    if not target_name:
        return None
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget

        return ImpersonateTarget.from_str(target_name)
    except Exception:
        return None


def build_ytdlp_resilience_opts(platform: str, *, phase: str = "download") -> dict[str, Any]:
    retry_count = 2 if phase == "metadata" else 4
    socket_timeout = 18 if phase == "metadata" else 25
    opts: dict[str, Any] = {
        "retries": retry_count,
        "fragment_retries": retry_count,
        "file_access_retries": 3,
        "extractor_retries": retry_count,
        "socket_timeout": socket_timeout,
        "continuedl": True,
        "noprogress": True,
        "cachedir": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    }
    if platform == "youtube":
        opts["force_ipv4"] = True
        opts["concurrent_fragment_downloads"] = 1 if phase == "download" else 2
        impersonate_target = yt_dlp_impersonate_target()
        if impersonate_target is not None:
            opts["impersonate"] = impersonate_target
    return opts


def ytdlp_runtime_diagnostics() -> dict[str, Any]:
    ffmpeg_bin = resolve_binary("ffmpeg")
    node_path = shutil.which("node") or "/Applications/Codex.app/Contents/Resources/node"
    deno_path = shutil.which("deno")
    ejs_available = optional_module_available("yt_dlp_ejs")
    provider_available = optional_module_available("yt_dlp_plugins.extractor.getpot_bgutil")
    if not provider_available:
        try:
            importlib.metadata.version("bgutil-ytdlp-pot-provider")
            provider_available = True
        except importlib.metadata.PackageNotFoundError:
            provider_available = False
    try:
        import yt_dlp

        ytdlp_version = yt_dlp.version.__version__
    except Exception:
        ytdlp_version = ""
    curl_cffi_available = importlib.util.find_spec("curl_cffi") is not None
    impersonate_target = yt_dlp_impersonate_target()
    return {
        "ytDlp": ytdlp_version,
        "ffmpeg": ffmpeg_bin or "",
        "node": node_path if node_path and Path(node_path).exists() else "",
        "deno": deno_path or "",
        "ejs": ejs_available,
        "curlCffi": curl_cffi_available,
        "impersonate": str(impersonate_target or ""),
        "poTokenProviderInstalled": provider_available,
        "poTokenServer": bgutil_provider_ping(timeout=0.5),
        "poTokenScript": bool(bgutil_provider_script_entry()),
        "poTokenProvider": bool(provider_available and (bgutil_provider_ping(timeout=0.5) or bgutil_provider_script_entry())),
    }


def append_runtime_diagnostics(notes: list[str] | None) -> None:
    if notes is None:
        return
    diag = ytdlp_runtime_diagnostics()
    bits = [
        f"yt-dlp={diag.get('ytDlp') or 'missing'}",
        f"ffmpeg={'ok' if diag.get('ffmpeg') else 'missing'}",
        f"node={'ok' if diag.get('node') else 'missing'}",
        f"ejs={'ok' if diag.get('ejs') else 'missing'}",
        f"impersonate={diag.get('impersonate') or 'missing'}",
        f"po-token-provider={'ok' if diag.get('poTokenProvider') else 'missing'}",
        f"po-token-server={'ok' if diag.get('poTokenServer') else 'missing'}",
    ]
    if diag.get("deno"):
        bits.append("deno=ok")
    notes.append(f"yt-dlp-runtime:{','.join(bits)}")


def download_policy_from_notes(
    *,
    platform: str,
    auth_note: str,
    notes: list[str] | None,
    local_video_path: str = "",
    require_local_video: bool = False,
) -> dict[str, Any]:
    """Return a compact product-facing record of how local video was obtained.

    This is intentionally separate from the raw yt-dlp notes. The UI needs to
    show whether this run used Chrome cookies, PO-token support, retries, cache,
    and a real local file without exposing noisy downloader internals.
    """
    note_items = [str(item or "") for item in (notes or []) if str(item or "").strip()]
    runtime = ytdlp_runtime_diagnostics()
    local_path = str(local_video_path or "").strip()
    local_bytes = 0
    if local_path:
        try:
            local_bytes = Path(local_path).expanduser().stat().st_size
        except OSError:
            local_bytes = 0
    auth_label = str(auth_note or "none")
    browser = ""
    if auth_label.startswith("browser:"):
        browser = auth_label.split(":", 1)[1] or "browser"
    strategy_labels: list[str] = []
    for note in note_items:
        if note.startswith("yt-dlp-video-option:"):
            strategy_labels.append(note.split(":", 1)[1])
        elif note.startswith("yt-dlp-video-strategy:"):
            strategy_labels.append(note.split(":", 1)[1])
        elif note.startswith("yt-dlp-frame-range:"):
            strategy_labels.append("range-download")
        elif note.startswith("local-video-reused:") or note.startswith("frame-source:preloaded-local-video"):
            strategy_labels.append("local-source")
    deduped_strategies: list[str] = []
    for label in strategy_labels:
        if label and label not in deduped_strategies:
            deduped_strategies.append(label)
    failed = any("yt-dlp-video-download-failed" in note for note in note_items)
    status = "saved" if local_bytes > 0 else "failed" if failed or require_local_video else "not-required"
    return {
        "required": bool(require_local_video),
        "status": status,
        "platform": platform,
        "auth": auth_label,
        "browserCookies": browser,
        "poTokenProvider": bool(runtime.get("poTokenProvider")),
        "poTokenServer": bool(runtime.get("poTokenServer")),
        "poTokenScript": bool(runtime.get("poTokenScript")),
        "impersonate": runtime.get("impersonate") or "",
        "ytDlp": runtime.get("ytDlp") or "",
        "ffmpeg": "ok" if runtime.get("ffmpeg") else "missing",
        "node": "ok" if runtime.get("node") else "missing",
        "ejs": "ok" if runtime.get("ejs") else "missing",
        "strategies": deduped_strategies[:6],
        "localVideoPath": local_path,
        "localVideoBytes": local_bytes,
        "cacheReuse": False,
        "lastNotes": note_items[-6:],
    }


def parse_env_csv(name: str) -> list[str]:
    value = os.environ.get(name, "").strip()
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,;\n]+", value) if item.strip()]


def youtube_extractor_args_for_clients(clients: list[str] | None = None) -> dict[str, Any]:
    args: dict[str, Any] = {}
    youtube_args: dict[str, list[str]] = {}
    if clients:
        youtube_args["player_client"] = clients
    po_tokens = parse_env_csv("YOUTUBE_NOTES_YOUTUBE_PO_TOKEN")
    if po_tokens:
        youtube_args["po_token"] = po_tokens
    visitor_data = os.environ.get("YOUTUBE_NOTES_YOUTUBE_VISITOR_DATA", "").strip()
    if visitor_data:
        youtube_args["visitor_data"] = [visitor_data]
    if youtube_args:
        args["youtube"] = youtube_args
    if BGUTIL_PROVIDER_BASE_URL and BGUTIL_PROVIDER_BASE_URL.rstrip("/") != "http://127.0.0.1:4416":
        args["youtubepot-bgutilhttp"] = {"base_url": [BGUTIL_PROVIDER_BASE_URL.rstrip("/")]}
    if bgutil_provider_script_entry():
        args["youtubepot-bgutilscript"] = {"server_home": [str(BGUTIL_PROVIDER_SERVER_HOME)]}
    return args


def merge_extractor_args(base_opts: dict[str, Any], extra_args: dict[str, Any]) -> dict[str, Any]:
    if not extra_args:
        return dict(base_opts)
    opts = dict(base_opts)
    merged = {
        key: dict(value)
        for key, value in (base_opts.get("extractor_args") or {}).items()
        if isinstance(value, dict)
    }
    for key, value in extra_args.items():
        existing = merged.get(key, {})
        merged[key] = {**existing, **value}
    opts["extractor_args"] = merged
    return opts


def build_ytdlp_attempts(url: str, base_opts: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    attempts: list[tuple[str, dict[str, Any]]] = [("default", dict(base_opts))]
    if detect_platform(url) != "youtube":
        return attempts

    client_sets: list[list[str]] = []
    configured_clients = parse_env_csv("YOUTUBE_NOTES_YOUTUBE_PLAYER_CLIENTS")
    if configured_clients:
        client_sets.append(configured_clients)
    else:
        client_sets.extend(
            [
                ["web_safari", "mweb", "web"],
                ["ios"],
                ["android"],
                ["tv"],
            ]
        )

    token_only_args = youtube_extractor_args_for_clients()
    if token_only_args:
        attempts.append(("youtube-token-env", merge_extractor_args(base_opts, token_only_args)))

    seen: set[str] = set()
    for clients in client_sets:
        key = ",".join(clients)
        if key in seen:
            continue
        seen.add(key)
        attempts.append(
            (
                f"youtube-client:{key}",
                merge_extractor_args(base_opts, youtube_extractor_args_for_clients(clients)),
            )
        )
    return attempts


def extract_video(
    url: str,
    out_dir: Path,
    langs: list[str],
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    include_comments: bool = False,
) -> tuple[dict[str, Any], list[Path]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    platform = detect_platform(url)
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": langs,
        "subtitlesformat": "vtt/best",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
    }
    ydl_opts.update(build_ytdlp_resilience_opts(platform, phase="metadata"))
    if include_comments:
        # Comment retrieval is slower and often platform-limited, so keep it opt-in.
        ydl_opts["getcomments"] = True
    ydl_opts.update(build_ytdlp_runtime_opts())
    apply_cookie_options(ydl_opts, platform, cookies_file, cookies_from_browser)
    before = set(out_dir.glob("*"))
    youtube_dl = get_youtube_dl()
    first_errors: list[str] = []
    try:
        for strategy, attempt_opts in build_ytdlp_attempts(url, ydl_opts):
            try:
                with youtube_dl(attempt_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                break
            except Exception as exc:
                first_errors.append(f"{strategy}:{compact_text(str(exc), 180)}")
        else:
            raise RuntimeError("; ".join(first_errors) or "metadata extraction failed")
    except Exception as first_exc:
        fallback_opts = dict(ydl_opts)
        fallback_opts["writesubtitles"] = False
        fallback_opts["writeautomaticsub"] = False
        second_errors: list[str] = []
        try:
            for strategy, attempt_opts in build_ytdlp_attempts(url, fallback_opts):
                try:
                    with youtube_dl(attempt_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                    break
                except Exception as exc:
                    second_errors.append(f"{strategy}:{compact_text(str(exc), 180)}")
            else:
                raise RuntimeError("; ".join(second_errors) or str(first_exc))
        except Exception as second_exc:
            message = str(second_exc) or str(first_exc)
            if platform == "bilibili" and "412" in message:
                raise RuntimeError(
                    "bilibili-fetch-412: B站返回 412，当前更像站点风控/鉴权问题；需要 cookies 或浏览器会话后再抓取"
                ) from second_exc
            raise
    after = set(out_dir.glob("*"))
    return info, sorted(after - before)


def try_video_parser_transcript(url: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import requests
    except Exception:
        return [], "requests-not-installed"

    endpoint = f"{DEFAULT_VIDEO_PARSER}/api/parse-video"
    try:
        response = requests.post(
            endpoint,
            json={
                "url": url,
                "include_transcript": True,
                "include_thumbnail": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return [], f"video-parser-error: {exc}"

    transcript = normalize_transcript_items(data.get("transcript"))
    if transcript:
        return transcript, None
    return [], "video-parser-no-transcript"


def caption_file_preference_key(path: Path) -> tuple[int, str]:
    name = path.name.lower()
    if "live_chat" in name or "danmaku" in name:
        return (99, name)
    if any(token in name for token in (".zh-hans-en.", ".zh-cn-en.", ".cmn-hans-en.")):
        return (0, name)
    if name.endswith(".zh-hans.vtt") or name.endswith(".zh-hans.srt") or name.endswith(".zh-cn.vtt") or name.endswith(".zh-cn.srt"):
        return (1, name)
    if any(token in name for token in (".zh-hans", ".zh-cn", ".zh_simplified", ".cmn-hans")):
        return (2, name)
    if any(token in name for token in (".zh-hant", ".zh-tw", ".cmn-hant")):
        return (3, name)
    if ".zh" in name or ".cmn" in name:
        return (4, name)
    if name.endswith(".en.vtt") or name.endswith(".en.srt") or ".en-en." in name:
        return (5, name)
    if ".en-" in name:
        return (6, name)
    return (10, name)


def sort_caption_files(caption_files: list[Path]) -> list[Path]:
    return sorted(caption_files, key=caption_file_preference_key)


def extract_caption_transcript(caption_files: list[Path]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sort_caption_files(caption_files):
        if path.suffix.lower() not in {".vtt", ".srt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text:
            continue
        items = subtitle_text_to_items(text)
        if items:
            break
    return items


def find_cached_caption_files(out_dir: Path, video_slug: str) -> list[Path]:
    candidates: list[Path] = []
    for suffix in (".vtt", ".srt"):
        candidates.extend(out_dir.glob(f"{video_slug}*{suffix}"))
    return sort_caption_files([path for path in candidates if path.is_file()])


def preferred_subtitle_languages(subtitles: dict[str, Any]) -> list[str]:
    if not isinstance(subtitles, dict):
        return []
    preferred = ["ai-zh", "zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW", "en"]
    languages = list(subtitles.keys())
    ordered = [lang for lang in preferred if lang in subtitles]
    ordered.extend(lang for lang in languages if lang not in ordered and lang != "danmaku")
    return ordered


def extract_embedded_subtitle_transcript(info: dict[str, Any], notes: list[str] | None = None) -> tuple[list[dict[str, Any]], str | None]:
    subtitles = info.get("subtitles") or {}
    if not isinstance(subtitles, dict) or not subtitles:
        return [], None
    for lang in preferred_subtitle_languages(subtitles):
        entries = subtitles.get(lang) or []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            data = entry.get("data")
            if not data:
                continue
            items = subtitle_text_to_items(str(data))
            if items:
                if notes is not None:
                    notes.append(f"yt-dlp-embedded-subtitle:{lang}")
                return items, f"yt-dlp-embedded-subtitle:{lang}"
    return [], None


def bilibili_bvid_from_url(url: str) -> str:
    match = re.search(r"/video/(BV[0-9A-Za-z]+)", url)
    return match.group(1) if match else ""


def request_json(url: str, *, referer: str = "https://www.bilibili.com/", timeout: int = 20) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": referer,
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def bilibili_subtitle_json_to_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    body = data.get("body") or []
    items: list[dict[str, Any]] = []
    if not isinstance(body, list):
        return items
    for row in body:
        if not isinstance(row, dict):
            continue
        text = re.sub(r"\s+", " ", str(row.get("content") or "")).strip()
        if not text:
            continue
        try:
            start = float(row.get("from") or 0)
        except Exception:
            start = 0.0
        try:
            end = float(row.get("to") or start)
        except Exception:
            end = start
        items.append({"text": text, "start": start, "duration": max(0.0, end - start)})
    return items


def try_bilibili_api_transcript(url: str, info: dict[str, Any], notes: list[str]) -> tuple[list[dict[str, Any]], str | None]:
    bvid = bilibili_bvid_from_url(url) or str(info.get("id") or "")
    if not bvid.startswith("BV"):
        notes.append("bilibili-subtitle-api-skipped:no-bvid")
        return [], None

    referer = f"https://www.bilibili.com/video/{bvid}/"
    aid = info.get("aid") or info.get("aid_id")
    cid = info.get("cid")
    if not cid:
        try:
            view = request_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", referer=referer)
            data = view.get("data") or {}
            aid = aid or data.get("aid")
            pages = data.get("pages") or []
            if pages and isinstance(pages[0], dict):
                cid = pages[0].get("cid")
        except Exception as exc:
            notes.append(f"bilibili-view-api-failed:{compact_text(str(exc), 120)}")
            return [], None

    if not cid:
        notes.append("bilibili-subtitle-api-skipped:no-cid")
        return [], None

    query = f"aid={aid}&cid={cid}" if aid else f"bvid={bvid}&cid={cid}"
    try:
        player = request_json(f"https://api.bilibili.com/x/player/wbi/v2?{query}", referer=referer)
    except Exception as exc:
        notes.append(f"bilibili-subtitle-api-failed:{compact_text(str(exc), 120)}")
        return [], None

    player_data = player.get("data") or {}
    if player_data.get("need_login_subtitle"):
        notes.append("bilibili-subtitle-login-required")
    subtitle_data = player_data.get("subtitle") or {}
    subtitle_rows = subtitle_data.get("subtitles") if isinstance(subtitle_data, dict) else []
    if not subtitle_rows:
        notes.append("bilibili-subtitle-api-empty")
        return [], None

    for row in subtitle_rows:
        if not isinstance(row, dict):
            continue
        subtitle_url = str(row.get("subtitle_url") or "")
        if not subtitle_url:
            continue
        if subtitle_url.startswith("//"):
            subtitle_url = "https:" + subtitle_url
        elif subtitle_url.startswith("/"):
            subtitle_url = "https://www.bilibili.com" + subtitle_url
        try:
            subtitle_json = request_json(subtitle_url, referer=referer)
            items = bilibili_subtitle_json_to_items(subtitle_json)
        except Exception as exc:
            notes.append(f"bilibili-subtitle-download-failed:{compact_text(str(exc), 120)}")
            continue
        if items:
            lang = str(row.get("lan") or row.get("lan_doc") or "unknown")
            notes.append(f"bilibili-subtitle-api:{lang}")
            return items, f"bilibili-subtitle-api:{lang}"
    return [], None


def parse_subtitle_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(payload, dict):
                items = bilibili_subtitle_json_to_items(payload)
                if items:
                    return items
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    if suffix == ".ass":
        return ass_subtitle_to_items(text)
    if suffix in {".srt", ".vtt", ".txt"}:
        return subtitle_text_to_items(text)
    return []


def find_bbdown_binary() -> str | None:
    env_value = os.environ.get("BBDOWN_BIN", "").strip()
    candidates = [env_value] if env_value else []
    candidates.extend(["BBDown", "bbdown"])
    for item in candidates:
        if not item:
            continue
        resolved = shutil.which(item) if not os.path.isabs(item) else item
        if resolved and Path(resolved).exists():
            return resolved
    return None


def try_bbdown_bilibili_transcript(url: str, out_dir: Path, notes: list[str]) -> tuple[list[dict[str, Any]], str | None]:
    binary = find_bbdown_binary()
    if not binary:
        notes.append("bbdown-skipped:not-installed")
        return [], None

    work_dir = out_dir / "_bbdown_subtitle"
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        url,
        "--sub-only",
        "--skip-ai",
        "false",
    ]
    timeout = int(float(os.environ.get("BBDOWN_TIMEOUT_SECONDS", "120") or "120"))
    try:
        result = subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        notes.append("bbdown-failed:timeout")
        return [], None
    except Exception as exc:
        notes.append(f"bbdown-failed:{compact_text(str(exc), 120)}")
        return [], None

    if result.returncode != 0:
        stderr = compact_text(result.stderr or result.stdout or "unknown", 180)
        notes.append(f"bbdown-failed:exit-{result.returncode}:{stderr}")
        return [], None

    subtitle_files = sorted(
        path
        for path in work_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".srt", ".vtt", ".ass", ".json", ".txt"}
    )
    for path in subtitle_files:
        items = parse_subtitle_file(path)
        if items:
            notes.append(f"bbdown-subtitle:{path.name}")
            return items, "bbdown-subtitle"

    notes.append("bbdown-empty:no-subtitle-file")
    return [], None


def fetch_bilibili_public_info(url: str, notes: list[str] | None = None) -> tuple[dict[str, Any], list[Path]]:
    bvid = bilibili_bvid_from_url(url)
    if not bvid:
        raise RuntimeError("bilibili-public-info-skipped:no-bvid")
    referer = f"https://www.bilibili.com/video/{bvid}/"
    try:
        payload = request_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", referer=referer)
    except Exception as exc:
        raise RuntimeError(f"bilibili-public-info-failed:{compact_text(str(exc), 180)}") from exc
    data = payload.get("data") or {}
    if not data:
        raise RuntimeError(f"bilibili-public-info-empty:code-{payload.get('code')}")
    pages = data.get("pages") or []
    first_page = pages[0] if pages and isinstance(pages[0], dict) else {}
    duration = data.get("duration") or first_page.get("duration")
    info = {
        "id": bvid,
        "webpage_url": url,
        "original_url": url,
        "title": data.get("title") or "Bilibili video",
        "description": data.get("desc") or "",
        "duration": duration,
        "thumbnail": data.get("pic") or "",
        "uploader": (data.get("owner") or {}).get("name"),
        "channel": (data.get("owner") or {}).get("name"),
        "aid": data.get("aid"),
        "cid": first_page.get("cid"),
        "subtitles": {},
        "automatic_captions": {},
        "formats": [],
        "http_headers": {"Referer": referer},
        "_bilibili_public_info": True,
    }
    if notes is not None:
        notes.append("bilibili-public-info:fallback-after-yt-dlp")
    return info, []


def download_audio_for_transcription(url: str, out_dir: Path) -> Path | None:
    return download_audio_for_transcription_with_auth(url, out_dir)


def download_audio_for_transcription_with_auth(
    url: str,
    out_dir: Path,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    notes: list[str] | None = None,
) -> Path | None:
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin is None:
        if notes is not None:
            notes.append("yt-dlp-audio-download-skipped:no-ffmpeg")
            append_runtime_diagnostics(notes)
        return None
    platform = detect_platform(url)

    out_dir.mkdir(parents=True, exist_ok=True)
    template = str(out_dir / "audio.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": ffmpeg_bin,
        "format": "bestaudio/best",
        "outtmpl": template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    opts.update(build_ytdlp_resilience_opts(platform))
    opts.update(build_ytdlp_runtime_opts())
    apply_cookie_options(opts, platform, cookies_file, cookies_from_browser)
    youtube_dl = get_youtube_dl()
    errors: list[str] = []
    for strategy, attempt_opts in build_ytdlp_attempts(url, opts):
        try:
            with youtube_dl(attempt_opts) as ydl:
                ydl.download([url])
        except Exception:
            errors.append(strategy)
            continue
        matches = sorted(out_dir.glob("audio.*"))
        if matches:
            if notes is not None and strategy != "default":
                notes.append(f"yt-dlp-audio-strategy:{strategy}")
            return matches[0]
    if notes is not None and errors:
        notes.append(f"yt-dlp-audio-download-failed:{','.join(errors[-4:])}")
        append_runtime_diagnostics(notes)
    source_video = download_video_for_frames_with_auth(
        url,
        out_dir / "_video_fallback",
        cookies_file=cookies_file,
        cookies_from_browser=cookies_from_browser,
        notes=notes,
    )
    if source_video is None:
        return None
    return extract_audio_from_video(source_video, out_dir / "audio-from-video.mp3")
    return None


def can_download_audio() -> bool:
    return resolve_binary("ffmpeg") is not None


def default_transcription_limit_seconds(platform: str) -> int:
    env_value = os.environ.get("YOUTUBE_NOTES_TRANSCRIBE_MAX_SECONDS", "").strip()
    if env_value:
        try:
            return max(0, int(float(env_value)))
        except Exception:
            return 0
    if platform in {"bilibili", "douyin"}:
        return 120
    return 0


def limit_audio_duration(audio_path: Path, seconds: int) -> Path:
    if seconds <= 0:
        return audio_path
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin is None:
        return audio_path
    limited_path = audio_path.with_name(f"{audio_path.stem}-first-{seconds}s{audio_path.suffix}")
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(audio_path),
        "-t",
        str(seconds),
        str(limited_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not limited_path.exists():
        return audio_path
    return limited_path


def extract_audio_from_video(source_video: Path, output_audio: Path) -> Path | None:
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin is None:
        return None
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_video),
        "-vn",
        "-acodec",
        "mp3",
        "-ab",
        "192k",
        str(output_audio),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not output_audio.exists():
        return None
    return output_audio


def resolve_whisper_cpp_model() -> Path | None:
    explicit_path = os.environ.get("YOUTUBE_NOTES_WHISPER_CPP_MODEL_PATH", "").strip()
    if explicit_path:
        path = Path(explicit_path).expanduser()
        return path if path.exists() else None
    model_name = os.environ.get("YOUTUBE_NOTES_WHISPER_CPP_MODEL", "base").strip() or "base"
    candidates = [
        WHISPER_CPP_MODELS / f"ggml-{model_name}.bin",
        WHISPER_CPP_MODELS / model_name,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def parse_whisper_cpp_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items: list[dict[str, Any]] = []
    for item in data.get("transcription") or []:
        text = clean_whisper_cpp_text(str(item.get("text") or ""))
        if not text:
            continue
        offsets = item.get("offsets") or {}
        try:
            start = float(offsets.get("from")) / 1000.0
            end = float(offsets.get("to")) / 1000.0
        except Exception:
            timestamps = item.get("timestamps") or {}
            start = parse_whisper_cpp_clock_to_seconds(str(timestamps.get("from") or ""))
            end = parse_whisper_cpp_clock_to_seconds(str(timestamps.get("to") or ""))
        items.append({"text": text, "start": start, "duration": max(0.0, end - start)})
    return normalize_transcript_items(items)


def run_whisper_cpp_transcriber(audio_path: Path) -> tuple[list[dict[str, Any]], str]:
    if not WHISPER_CPP_CLI.exists():
        return [], "whisper-cpp-unavailable:no-cli"
    model_path = resolve_whisper_cpp_model()
    if model_path is None:
        return [], "whisper-cpp-unavailable:no-model"

    language = os.environ.get("YOUTUBE_NOTES_ASR_LANGUAGE", "zh").strip() or "zh"
    beam_size = os.environ.get("YOUTUBE_NOTES_WHISPER_CPP_BEAM_SIZE", "1").strip() or "1"
    best_of = os.environ.get("YOUTUBE_NOTES_WHISPER_CPP_BEST_OF", "1").strip() or "1"
    threads = os.environ.get("YOUTUBE_NOTES_WHISPER_CPP_THREADS", "4").strip() or "4"

    with tempfile.TemporaryDirectory(prefix="whisper-cpp-") as tmp_dir:
        output_prefix = Path(tmp_dir) / "transcript"
        command = [
            str(WHISPER_CPP_CLI),
            "-m",
            str(model_path),
            "-f",
            str(audio_path),
            "-l",
            language,
            "-oj",
            "-ojf",
            "-of",
            str(output_prefix),
            "-np",
            "-bs",
            beam_size,
            "-bo",
            best_of,
            "-t",
            threads,
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        except Exception as exc:
            return [], f"whisper-cpp-failed:{exc}"
        transcript = parse_whisper_cpp_json(output_prefix.with_suffix(".json"))
        if transcript:
            return transcript, f"whisper-cpp:{model_path.name}:bs{beam_size}:bo{best_of}"
        reason = compact_text(result.stderr or result.stdout or "empty transcript", 600)
        return [], f"whisper-cpp-failed:{reason}"


def run_external_python_transcriber(audio_path: Path, backend: str, model_name: str) -> tuple[list[dict[str, Any]], str]:
    if not LOCAL_VLM_PYTHON.exists():
        return [], f"{backend}-unavailable:no-local-vlm-python"

    if backend == "lightning-mlx":
        script = """
import json, sys
from lightning_whisper_mlx import LightningWhisperMLX
audio_path = sys.argv[1]
model_name = sys.argv[2]
whisper = LightningWhisperMLX(model=model_name, batch_size=12, quant=None)
result = whisper.transcribe(audio_path=audio_path)
segments = result.get("segments") or []
if segments:
    transcript = [
        {
            "text": str(segment.get("text") or "").strip(),
            "start": float(segment.get("start") or 0),
            "duration": float((segment.get("end") or segment.get("start") or 0) - (segment.get("start") or 0)),
        }
        for segment in segments
        if str(segment.get("text") or "").strip()
    ]
else:
    text = str(result.get("text") or "").strip()
    transcript = [{"text": text, "start": 0.0, "duration": 0.0}] if text else []
print(json.dumps(transcript, ensure_ascii=False))
"""
    elif backend == "mlx-whisper":
        script = """
import json, sys
import mlx_whisper
audio_path = sys.argv[1]
model_name = sys.argv[2]
result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model_name)
segments = result.get("segments") or []
if segments:
    transcript = [
        {
            "text": str(segment.get("text") or "").strip(),
            "start": float(segment.get("start") or 0),
            "duration": float((segment.get("end") or segment.get("start") or 0) - (segment.get("start") or 0)),
        }
        for segment in segments
        if str(segment.get("text") or "").strip()
    ]
else:
    text = str(result.get("text") or "").strip()
    transcript = [{"text": text, "start": 0.0, "duration": 0.0}] if text else []
print(json.dumps(transcript, ensure_ascii=False))
"""
    elif backend == "faster-whisper":
        script = """
import json, sys
from faster_whisper import WhisperModel
audio_path = sys.argv[1]
model_name = sys.argv[2]
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4, num_workers=1)
segments, _info = model.transcribe(audio_path, vad_filter=True, beam_size=1, condition_on_previous_text=False)
transcript = [
    {
        "text": segment.text.strip(),
        "start": float(segment.start),
        "duration": float(segment.end - segment.start),
    }
    for segment in segments
    if segment.text.strip()
]
print(json.dumps(transcript, ensure_ascii=False))
"""
    else:
        return [], f"{backend}-unsupported"

    try:
        env = os.environ.copy()
        ffmpeg_bin = resolve_binary("ffmpeg")
        if ffmpeg_bin:
            env["PATH"] = f"{str(Path(ffmpeg_bin).parent)}:{env.get('PATH', '')}"
        result = subprocess.run(
            [str(LOCAL_VLM_PYTHON), "-c", script, str(audio_path), model_name],
            capture_output=True,
            text=True,
            timeout=1800,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            transcript = normalize_transcript_items(json.loads(result.stdout))
            if transcript:
                return transcript, f"{backend}:{model_name}"
        reason = compact_text(result.stderr or result.stdout or "empty transcript", 600)
        return [], f"{backend}-failed:{reason}"
    except Exception as exc:
        return [], f"{backend}-failed:{exc}"


def transcribe_audio(audio_path: Path) -> tuple[list[dict[str, Any]], str]:
    requested_backend = os.environ.get("YOUTUBE_NOTES_ASR_BACKEND", "auto").strip() or "auto"
    if requested_backend not in ASR_BACKEND_CHOICES:
        requested_backend = "auto"
    lightning_model = os.environ.get("YOUTUBE_NOTES_LIGHTNING_MLX_MODEL", "base")
    mlx_model = os.environ.get("YOUTUBE_NOTES_MLX_WHISPER_MODEL", "mlx-community/whisper-tiny")
    external_model_name = os.environ.get("YOUTUBE_NOTES_EXTERNAL_WHISPER_MODEL", "tiny")

    backend_plan: list[tuple[str, str]] = []
    backend_errors: list[str] = []
    if requested_backend == "auto":
        transcript, source = run_whisper_cpp_transcriber(audio_path)
        if transcript:
            return transcript, source
        backend_errors.append(source)
        backend_plan.extend(
            [
                ("mlx-whisper", mlx_model),
                ("lightning-mlx", lightning_model),
                ("faster-whisper", external_model_name),
            ]
        )
    elif requested_backend == "whisper-cpp":
        transcript, source = run_whisper_cpp_transcriber(audio_path)
        if transcript:
            return transcript, source
        backend_errors.append(source)
    elif requested_backend == "lightning-mlx":
        backend_plan.append(("lightning-mlx", lightning_model))
    elif requested_backend == "mlx-whisper":
        backend_plan.append(("mlx-whisper", mlx_model))
    elif requested_backend == "faster-whisper":
        backend_plan.append(("faster-whisper", external_model_name))

    for backend, model_name in backend_plan:
        transcript, source = run_external_python_transcriber(audio_path, backend, model_name)
        if transcript:
            return transcript, source
        backend_errors.append(source)

    model_name = os.environ.get("YOUTUBE_NOTES_WHISPER_MODEL", "small")
    if requested_backend in {"auto", "faster-whisper"}:
        try:
            from faster_whisper import WhisperModel  # type: ignore

            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            segments, _info = model.transcribe(str(audio_path), vad_filter=True)
            transcript = [
                {
                    "text": segment.text.strip(),
                    "start": float(segment.start),
                    "duration": float(segment.end - segment.start),
                }
                for segment in segments
                if segment.text.strip()
            ]
            if transcript:
                return transcript, f"faster-whisper:{model_name}"
        except Exception as exc:
            backend_errors.append(f"faster-whisper-local-failed:{exc}")

    if requested_backend in {"auto", "whisper"}:
        try:
            import whisper  # type: ignore

            model = whisper.load_model(model_name)
            result = model.transcribe(str(audio_path))
            transcript = normalize_transcript_items(result.get("segments"))
            if transcript:
                return transcript, f"whisper:{model_name}"
        except Exception as exc:
            backend_errors.append(f"whisper-failed:{exc}")

    return [], compact_text("; ".join(backend_errors) or "whisper-unavailable", 1000)

def download_video_for_frames(url: str, out_dir: Path) -> Path | None:
    return download_video_for_frames_with_auth(url, out_dir)


def build_frame_download_range(end_seconds: int):
    if end_seconds <= 0:
        return None
    try:
        from yt_dlp.utils import download_range_func
    except Exception:
        def fallback_download_range(_info_dict, _ydl):
            return [{"start_time": 0.0, "end_time": float(end_seconds)}]

        return fallback_download_range
    return download_range_func([], [(0, float(end_seconds))])


def default_frame_download_format() -> str:
    return os.environ.get(
        "YOUTUBE_NOTES_FRAME_FORMAT",
        (
            "18/"
            "b[height<=360][ext=mp4][protocol=https]/"
            "b[height<=360][protocol=https]/"
            "worstvideo[height<=360][vcodec!=none][protocol=https]/"
            "worstvideo[height<=360][vcodec!=none][protocol=http]/"
            "worst[height<=360][protocol=https]/"
            "worst[height<=360][protocol=http]/"
            "worstvideo[height<=360][vcodec!=none]/"
            "worst[height<=360]/"
            "worstvideo[vcodec!=none]/"
            "worst"
        ),
    ).strip() or "worstvideo[height<=360][vcodec!=none][protocol=https]/worst"


def compatible_local_video_format() -> str:
    return os.environ.get(
        "YOUTUBE_NOTES_LOCAL_VIDEO_FORMAT",
        (
            "18/"
            "b[height<=480][ext=mp4][protocol=https]/"
            "b[height<=360][ext=mp4][protocol=https]/"
            "b[height<=480][protocol=https]/"
            "bv*[height<=480][ext=mp4]+ba[ext=m4a]/"
            "b[height<=480][ext=mp4]/"
            "bv*[height<=480]+ba/"
            "b[height<=480]/"
            "bv*[height<=720][ext=mp4]+ba[ext=m4a]/"
            "b[height<=720][ext=mp4]/"
            "best[height<=720]/"
            "best"
        ),
    ).strip() or "best[height<=720]/best"


def build_video_download_option_variants(base_opts: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    variants: list[tuple[str, dict[str, Any]]] = [("ranged-low", dict(base_opts))]
    has_range = "download_ranges" in base_opts
    if has_range:
        no_range = dict(base_opts)
        no_range.pop("download_ranges", None)
        no_range.pop("force_keyframes_at_cuts", None)
        variants.append(("full-low", no_range))
    compatible = dict(base_opts)
    compatible.pop("download_ranges", None)
    compatible.pop("force_keyframes_at_cuts", None)
    compatible["format"] = compatible_local_video_format()
    variants.append(("full-compatible", compatible))

    seen: set[tuple[str, str, bool]] = set()
    deduped: list[tuple[str, dict[str, Any]]] = []
    for label, opts in variants:
        key = (label, str(opts.get("format") or ""), "download_ranges" in opts)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, opts))
    return deduped


def source_video_candidates(out_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in out_dir.glob("source.*"):
        suffixes = {suffix.lower() for suffix in path.suffixes}
        if suffixes.intersection({".part", ".ytdl", ".tmp"}):
            continue
        try:
            if not path.is_file() or path.stat().st_size <= 0:
                continue
        except OSError:
            continue
        candidates.append(path)
    return sorted(candidates, key=lambda item: (item.stat().st_size, item.name), reverse=True)


def copy_source_video(source_video: Path, target_video: Path, notes: list[str] | None = None, note: str = "local-video-saved:source") -> Path:
    target_video.parent.mkdir(parents=True, exist_ok=True)
    try:
        if source_video.resolve() == target_video.resolve():
            if notes is not None:
                notes.append("local-video-reused:source")
            return target_video
    except Exception:
        pass
    if not target_video.exists() or target_video.stat().st_size != source_video.stat().st_size:
        shutil.copy2(source_video, target_video)
        if notes is not None:
            notes.append(note)
    elif notes is not None:
        notes.append("local-video-reused:source")
    return target_video


def remux_source_video_to_mp4(source_video: Path, target_video: Path, notes: list[str] | None = None) -> Path | None:
    if source_video.suffix.lower() == ".mp4":
        return copy_source_video(source_video, target_video, notes, "local-video-saved:mp4-source")
    ffmpeg_bin = resolve_binary("ffmpeg")
    if not ffmpeg_bin:
        if notes is not None:
            notes.append("local-video-remux-skipped:no-ffmpeg")
        return None
    target_video.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_video),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(target_video),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True)
    except Exception as exc:
        if notes is not None:
            notes.append(f"local-video-remux-failed:{compact_text(str(exc), 100)}")
        return None
    if completed.returncode == 0 and target_video.exists() and target_video.stat().st_size > 0:
        if notes is not None:
            notes.append("local-video-remuxed:mp4")
        return target_video
    try:
        target_video.unlink(missing_ok=True)
    except Exception:
        pass
    if notes is not None:
        notes.append(f"local-video-remux-failed:{compact_text(completed.stderr or 'ffmpeg failed', 120)}")
    return None


def persist_source_video_for_material(source_video: Path, asset_dir: Path, notes: list[str] | None = None) -> Path:
    """Persist the downloaded source under the stable `source-video.*` name.

    The analysis UI and cache lookup use `source-video*`. Required downloads can
    happen before frame extraction, so persist the file immediately instead of
    relying on the later frame path to copy it.
    """
    source_video = source_video.expanduser().resolve()
    asset_dir.mkdir(parents=True, exist_ok=True)
    preferred_mp4 = asset_dir / "source-video.mp4"
    remuxed = remux_source_video_to_mp4(source_video, preferred_mp4, notes)
    if remuxed is not None:
        return remuxed
    suffix = source_video.suffix or ".mp4"
    fallback = asset_dir / f"source-video{suffix}"
    return copy_source_video(source_video, fallback, notes, "local-video-saved:original-source")


def download_video_for_frames_with_auth(
    url: str,
    out_dir: Path,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    notes: list[str] | None = None,
    section_end_seconds: int | None = None,
    progress_callback=None,
    playable_video: bool = False,
) -> Path | None:
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin is None:
        if notes is not None:
            notes.append("yt-dlp-video-download-skipped:no-ffmpeg")
            append_runtime_diagnostics(notes)
        return None
    platform = detect_platform(url)

    out_dir.mkdir(parents=True, exist_ok=True)
    template = str(out_dir / "source.%(ext)s")
    if platform == "youtube":
        ensure_bgutil_provider_server(notes)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": ffmpeg_bin,
        "format": compatible_local_video_format() if playable_video else default_frame_download_format(),
        "outtmpl": template,
    }
    opts.update(build_ytdlp_resilience_opts(platform))
    if section_end_seconds:
        download_range = build_frame_download_range(section_end_seconds)
        if download_range is not None:
            opts["download_ranges"] = download_range
            opts["force_keyframes_at_cuts"] = False
            if notes is not None:
                notes.append(f"yt-dlp-frame-range:0-{section_end_seconds}s")
    opts.update(build_ytdlp_runtime_opts())
    apply_cookie_options(opts, platform, cookies_file, cookies_from_browser)
    if progress_callback:
        last_progress_emit = {"at": 0.0}

        def emit_download_progress(payload: dict[str, Any]) -> None:
            try:
                status = str(payload.get("status") or "")
                now = time.monotonic()
                if status == "downloading" and now - last_progress_emit["at"] < 0.7:
                    return
                last_progress_emit["at"] = now
                downloaded = int(payload.get("downloaded_bytes") or 0)
                total = int(payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0)
                speed = int(payload.get("speed") or 0)
                eta_value = payload.get("eta")
                eta = int(eta_value) if isinstance(eta_value, (int, float)) and eta_value >= 0 else None
                elapsed_value = payload.get("elapsed")
                elapsed = int(elapsed_value) if isinstance(elapsed_value, (int, float)) and elapsed_value >= 0 else None
                fragment_index = int(payload.get("fragment_index") or 0)
                fragment_count = int(payload.get("fragment_count") or 0)
                progress: dict[str, Any] = {
                    "progressKind": "download",
                    "downloadStatus": status,
                    "downloadedBytes": downloaded,
                    "totalBytes": total,
                    "speedBytesPerSecond": speed,
                    "filename": str(payload.get("filename") or ""),
                }
                if eta is not None:
                    progress["etaSeconds"] = eta
                if elapsed is not None:
                    progress["elapsedSeconds"] = elapsed
                if fragment_index:
                    progress["fragmentIndex"] = fragment_index
                if fragment_count:
                    progress["fragmentCount"] = fragment_count
                if downloaded and total:
                    progress["percent"] = max(0.0, min(100.0, downloaded * 100.0 / total))
                message = "下载完成" if status == "finished" else "下载中"
                progress_callback("download", message, progress)
            except Exception:
                return

        opts["progress_hooks"] = [emit_download_progress]
    youtube_dl = get_youtube_dl()
    errors: list[str] = []
    for option_label, option_opts in build_video_download_option_variants(opts):
        for strategy, attempt_opts in build_ytdlp_attempts(url, option_opts):
            try:
                with youtube_dl(attempt_opts) as ydl:
                    ydl.download([url])
            except Exception as exc:
                errors.append(f"{option_label}/{strategy}:{compact_text(str(exc), 120)}")
                continue
            candidates = source_video_candidates(out_dir)
            if candidates:
                if notes is not None:
                    notes.append(f"yt-dlp-frame-format:{attempt_opts.get('format')}")
                if notes is not None and option_label != "ranged-low":
                    notes.append(f"yt-dlp-video-option:{option_label}")
                if notes is not None and strategy != "default":
                    notes.append(f"yt-dlp-video-strategy:{strategy}")
                return candidates[0]
            errors.append(f"{option_label}/{strategy}:no-complete-source-file")
    if notes is not None and errors:
        notes.append(f"yt-dlp-video-download-failed:{' | '.join(errors[-4:])}")
        append_runtime_diagnostics(notes)
    return None


def extract_keyframes(
    url: str,
    out_dir: Path,
    interval_seconds: int,
    max_frames: int,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    target_seconds: list[int | float] | None = None,
    source_video_path: str | Path | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    assets: list[dict[str, Any]] = []
    ffmpeg_bin = resolve_binary("ffmpeg")
    if ffmpeg_bin is None:
        return assets, ["frame-extraction-skipped:no-ffmpeg"]

    frame_interval = max(1, interval_seconds)
    frame_count = max(1, max_frames)
    normalized_targets = normalize_target_frame_seconds(target_seconds, frame_count)
    timestamps = normalized_targets or [float(index * frame_interval) for index in range(frame_count)]
    section_end_seconds = int(max(timestamps or [0])) + max(8, min(30, frame_interval))
    source_video = Path(source_video_path).expanduser().resolve() if source_video_path else None
    temp_context = None
    try:
        if source_video is not None and source_video.exists():
            notes.append("frame-source:preloaded-local-video")
        else:
            source_video = None
            temp_context = tempfile.TemporaryDirectory(prefix="video-frames-")
            tmp_dir = temp_context.__enter__()
            temp_source = download_video_for_frames_with_auth(
                url,
                Path(tmp_dir),
                cookies_file=cookies_file,
                cookies_from_browser=cookies_from_browser,
                notes=notes,
                section_end_seconds=section_end_seconds,
            )
            if temp_source is None:
                if cookies_file or resolve_cookies_from_browser(cookies_from_browser) != "none":
                    notes.append("frame-download-retry:no-auth")
                    temp_source = download_video_for_frames_with_auth(
                        url,
                        Path(tmp_dir) / "no_auth",
                        cookies_file=None,
                        cookies_from_browser="none",
                        notes=notes,
                        section_end_seconds=section_end_seconds,
                    )
                if temp_source is None:
                    return assets, notes + ["frame-extraction-failed:video-download"]
            source_video = temp_source

        if source_video is None:
            return assets, notes + ["frame-extraction-failed:video-download"]

        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            persist_source_video_for_material(source_video, out_dir, notes=notes)
        except Exception as exc:
            notes.append(f"local-video-save-failed:{compact_text(str(exc), 80)}")

        frames_dir = out_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        if normalized_targets:
            notes.append("frame-extraction-targeted")
        for index, timestamp in enumerate(timestamps):
            frame_path = frames_dir / f"frame-{index + 1:03d}.jpg"
            command = [
                ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                str(source_video),
                "-frames:v",
                "1",
                str(frame_path),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0 or not frame_path.exists():
                notes.append(f"frame-extraction-failed:{format_timestamp(timestamp)}:{compact_text(result.stderr, 160)}")
                continue
            assets.append(
                {
                    "type": "frame",
                    "path": str(frame_path),
                    "source": "ffmpeg",
                    "timestamp": timestamp,
                }
            )
    finally:
        if temp_context is not None:
            temp_context.__exit__(None, None, None)
    if not assets:
        notes.append("frame-extraction-produced-no-assets")
    return assets, notes


def normalize_target_frame_seconds(value: Any, max_frames: int) -> list[float]:
    if value is None:
        return []
    raw_items: list[Any]
    if isinstance(value, str):
        raw_items = [item.strip() for item in re.split(r"[,，\s]+", value) if item.strip()]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]

    seen: set[int] = set()
    normalized: list[float] = []
    for item in raw_items:
        try:
            if isinstance(item, str) and ":" in item:
                seconds = float(parse_clock_to_seconds(item))
            else:
                seconds = float(item)
        except (TypeError, ValueError):
            continue
        if seconds < 0:
            continue
        rounded = int(round(seconds))
        if rounded in seen:
            continue
        seen.add(rounded)
        normalized.append(float(rounded))
        if len(normalized) >= max(1, max_frames):
            break
    return normalized


def read_channel_profile() -> str:
    if not CHANNEL_PROFILE_PATH.exists():
        return ""
    return CHANNEL_PROFILE_PATH.read_text(encoding="utf-8")


def build_analysis_payload(
    url: str,
    platform: str,
    info: dict[str, Any],
    transcript_items: list[dict[str, Any]],
    outline: list[dict[str, Any]],
    key_points: list[str],
    visual_assets: list[dict[str, Any]],
    visual_notes: list[str],
    transcript_source: str = "",
) -> dict[str, Any]:
    description = str(info.get("description") or "")
    transcript_plain = transcript_items_to_text(transcript_items, with_timestamps=False)
    transcript_preview = transcript_items_to_text(transcript_items[:80], with_timestamps=True)
    channel_profile = read_channel_profile()

    return {
        "url": url,
        "platform": platform,
        "title": str(info.get("title") or "Untitled"),
        "channel": info.get("channel") or info.get("uploader") or "unknown",
        "duration_seconds": info.get("duration"),
        "duration_human": format_duration(info.get("duration")),
        "upload_date": info.get("upload_date") or "unknown",
        "view_count": info.get("view_count") or "unknown",
        "like_count": info.get("like_count") or "unknown",
        "comment_count": info.get("comment_count") or "unknown",
        "comments_preview": build_comment_preview(info),
        "description_preview": compact_text(description, 2500),
        "outline": outline,
        "key_points": key_points,
        "transcript_source_count": len(transcript_items),
        "transcript_source": transcript_source,
        "transcript_preview": compact_text(transcript_preview, 12000),
        "transcript_plain": compact_text(transcript_plain, 16000),
        "visual_assets": visual_assets,
        "visual_notes": visual_notes,
        "channel_profile": compact_text(channel_profile, 8000),
    }


def classify_report_type(payload: dict[str, Any]) -> str:
    source = " ".join(
        [
            str(payload.get("url") or ""),
            str(payload.get("platform") or ""),
            str(payload.get("title") or ""),
            str(payload.get("channel") or ""),
            str(payload.get("description_preview") or ""),
        ]
    ).lower()
    transcript = str(payload.get("transcript_plain") or "").lower()
    if is_short_product_tutorial(payload):
        return "tutorial"
    if "ted.com/talks" in source or "ted talk" in source or "ted20" in source:
        return "talk"
    if any(marker in transcript for marker in ["my name is ", "today i'm going to"]):
        return "talk"
    if any(marker in source for marker in ["interview", "q&a", "conversation"]):
        return "interview"
    if any(marker in source for marker in ["tutorial", "course", "how to", "教程"]):
        return "tutorial"
    return "general"


def is_short_product_tutorial(payload: dict[str, Any]) -> bool:
    title = str(payload.get("title") or "")
    transcript = str(payload.get("transcript_plain") or "")
    text = f"{title}\n{transcript}".lower()
    duration = payload.get("duration_seconds")
    try:
        duration_value = float(duration)
    except Exception:
        duration_value = 0
    product_signal = re.search(
        r"tutorial|how to|generator|captions?|subtitles?|capcut|veed|canva|tool|demo|editor|upload|export|preset",
        text,
        re.I,
    )
    action_hits = sum(
        1
        for pattern in (
            r"let me show you|show you how",
            r"all you need to do|head over to",
            r"upload",
            r"subtitles?|captions?",
            r"choose|select",
            r"edit|customi[sz]e",
            r"export|done",
        )
        if re.search(pattern, text, re.I)
    )
    return bool(product_signal and action_hits >= 3 and (duration_value == 0 or duration_value <= 300))


def extract_product_tutorial_steps(payload: dict[str, Any]) -> list[str]:
    title = str(payload.get("title") or "")
    transcript = str(payload.get("transcript_plain") or "")
    key_points = [str(item or "") for item in payload.get("key_points") or []]
    text = "\n".join([title, transcript, *key_points])
    steps: list[str] = []
    candidates = [
        (r"upload|导入|上传", "上传视频或素材"),
        (r"subtitle|caption|字幕|auto-caption", "打开字幕功能并自动生成字幕"),
        (r"transcript|转写|文稿", "检查转写文本"),
        (r"style|preset|样式|模板", "选择字幕样式"),
        (r"edit|customi[sz]e|effects?|animation|品牌|on-brand|调整|编辑|动效", "继续调整样式、动效和品牌感"),
        (r"done|export|导出|发布", "确认效果后导出视频"),
    ]
    for pattern, label in candidates:
        if re.search(pattern, text, re.I) and label not in steps:
            steps.append(label)
    if not steps:
        for item in key_points:
            cleaned = re.sub(r"^\d{2}:\d{2}(?::\d{2})?\s*", "", item).strip()
            if cleaned:
                steps.append(compact_text(cleaned, 48))
            if len(steps) >= 5:
                break
    return steps[:6]


def clean_source_excerpt(value: str, limit: int = 140) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = value.strip(" -–—")
    return compact_text(value, limit)


def find_excerpt(text: str, patterns: list[str], limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    lower = text.lower()
    for pattern in patterns:
        index = lower.find(pattern.lower())
        if index == -1:
            continue
        start = index
        while start > 0 and text[start - 1].isalnum():
            start -= 1
        end = min(len(text), index + len(pattern) + 90)
        while end < len(text) and text[end - 1].isalnum() and text[end].isalnum():
            end += 1
        return clean_source_excerpt(text[start:end], limit)
    return ""


def build_talk_report(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or "Untitled")
    speaker = str(payload.get("channel") or "unknown")
    transcript = str(payload.get("transcript_plain") or "")
    description = str(payload.get("description_preview") or "")
    lower = transcript.lower()

    if "agency" in lower and ("deception" in lower or "self-preservation" in lower):
        summary = [
            f"{speaker} 把 AI 风险讲成一条能力演化链：模型先掌握语言，再获得规划和执行能力。",
            "演讲的压力点在 agency：系统开始计划、隐藏意图、保护自身时，风险就进入另一种量级。",
            "他给出的解法是 Scientist AI：让 AI 先承担可靠预测和科学辅助，少把主动执行权交给不可信 agent。",
        ]
        argument_chain = [
            "用孩子学说话的经历引入能力扩展，把 human capability、agency 和 joy 连在一起。",
            "回顾深度学习从手写识别、图像识别、翻译到 ChatGPT 的能力跃迁。",
            "指出商业压力正在推动更强 agent，因为它们能替代劳动。",
            "引用近期实验：部分先进模型出现欺骗、作弊、自我保存倾向。",
            "提出 Scientist AI：强调理解世界和可靠预测，作为不可信 agent 的护栏。",
        ]
        evidence_examples = [
            "2023 年暂停信和后续 extinction risk statement，说明风险讨论已经从学术界进入公共治理。",
            "OpenAI O1 相关风险评估被他说成从 low 升到 medium，用来强调能力增长带来的现实压力。",
            "模型被告知会被替换后尝试保留自身代码和权重，这个实验支撑了自我保存风险。",
            "他用“三明治监管比 AI 多”的说法，把监管滞后讲得很直观。",
        ]
        channel_angles = [
            "AI agent 的变化点：工具开始获得执行权。",
            "Bengio 的警告适合和 Codex、Claude Code 这类后台 agent 放在一起讲。",
            "普通人不用先争论末日论，可以先问：我愿意把哪些真实任务交给 AI？",
            "Scientist AI 这个概念适合延展成“少让 AI 替你行动，多让 AI 替你校验”。",
        ]
        plain_summary = (
            "Bengio 这场演讲可以这样理解：AI 风险正在从“模型更聪明”推进到“模型更会行动”。"
            "他把担心放在能够计划、执行、复制、隐藏意图的 agent 上。"
            "他的解法也很克制：先发展能做可靠预测的 Scientist AI，用它来约束更危险的执行型系统。"
        )
    else:
        summary = [
            f"{speaker} 围绕《{title}》展开一个公共议题。",
            "演讲通过个人经历、事实线索和风险判断逐步推进。",
            "适合提炼成一篇解释型内容：先交代演讲者立场，再拆论证链和观众可带走的判断。",
        ]
        argument_chain = [
            "开场用个人故事或具体场景降低进入门槛。",
            "中段把议题放回公共风险、技术变化或社会选择。",
            "结尾给出行动方向或治理想象。",
        ]
        evidence_examples = [
            "演讲使用人物经历作为入口。",
            "核心判断通过例子、研究或公共事件支撑。",
            "结尾把问题收回到观众能理解的责任边界。",
        ]
        channel_angles = [
            f"《{title}》适合改成一条“演讲者为什么现在站出来说这话”的内容。",
            "可以拆演讲的开头方式：从小场景进入大问题。",
            "可以做一版“这场 TED 真正值得普通人带走的 3 个判断”。",
        ]
        plain_summary = compact_text(description or transcript, 420)

    key_excerpts = [
        find_excerpt(transcript, ["human agency", "human joy"], 150),
        find_excerpt(transcript, ["risk of extinction from AI", "global priority"], 150),
        find_excerpt(transcript, ["deception", "cheating", "self-preservation"], 150),
        find_excerpt(transcript, ["Scientist AI", "trustworthy predictions"], 150),
    ]
    key_excerpts = [item for item in key_excerpts if item]

    tensions = [
        "他同时是 AI 发展的核心贡献者和风险警告者，这让演讲带有自我纠偏的意味。",
        "他的方案强调少给 AI 主动执行权，但市场正在奖励更强执行型 agent。",
        "演讲把风险讲得很重，观众可能会追问：哪些证据属于已发生，哪些仍是外推。",
    ]

    report = {
        "summary": summary,
        "speaker_context": f"{speaker} 是这场演讲的主要发言者；从演讲内容看，他以 AI 研究者和公共风险提醒者的双重身份说话。",
        "argument_chain": argument_chain,
        "evidence_examples": evidence_examples,
        "key_excerpts": key_excerpts[:4],
        "tensions": tensions,
        "channel_angles": channel_angles,
        "plain_chinese_summary": plain_summary,
    }
    return clean_report_text_object(report)


def build_creator_draft_pack(payload: dict[str, Any], talk_report: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or "Untitled")
    speaker = str(payload.get("channel") or "演讲者")
    lower_text = " ".join(
        [
            title,
            str(payload.get("description_preview") or ""),
            str(payload.get("transcript_plain") or "")[:6000],
        ]
    ).lower()
    is_bengio_agent_risk = "agency" in lower_text and (
        "deception" in lower_text or "self-preservation" in lower_text or "scientist ai" in lower_text
    )

    if is_bengio_agent_risk:
        titles = [
            "Bengio 的 TED 警告：AI 开始获得执行权",
            "AI agent 时代，Bengio 把风险指向执行权",
            "从聊天框到执行权：Bengio 这场 TED 值得重看",
            "当 AI 学会计划和自保，风险就换了形状",
        ]
        openings = [
            {
                "route": "人物 / 场景",
                "text": (
                    "Bengio 这场 TED 最耐看的地方，是他没有一上来讲模型、算力、监管。"
                    "他先讲自己的儿子 Patrick 学会说 Pa-pa 的那一刻：语言让一个孩子开始理解世界，也开始表达自己的意愿。"
                    "这一步很小，却把整场演讲的压力放出来了：能力一旦和行动意愿连在一起，AI 就不再只是一个回答问题的系统。"
                ),
            },
            {
                "route": "工具 / 现实",
                "text": (
                    "我们平时说 AI 变强，常常想到的是回答更快、写得更顺、代码补得更完整。"
                    "Bengio 在 TED 上把焦点推到另一件事：AI 开始获得执行权。"
                    "它能计划、能调用工具、能完成任务，也可能学会隐藏意图和保护自己。"
                ),
            },
            {
                "route": "个人 IP / 使用者",
                "text": (
                    "如果你已经在用 Codex 或 Claude Code，你会比普通观众更容易听懂 Bengio 的担心。"
                    "因为你每天看到的变化很具体：AI 正在从一个聊天窗口，慢慢变成能改文件、跑测试、交付结果的后台执行者。"
                    "这当然提高效率，也迫使我们重新划分哪些任务可以交出去，哪些地方必须有人类签字。"
                ),
            },
        ]
        oral_script_beats = [
            "开场用 Patrick 学说话，把 capability、agency、joy 三个词落到一个家庭场景里。",
            "交代 Bengio 的位置：深度学习奠基者之一，现在站出来讲风险，语气自然会更重。",
            "回到技术链：语言理解、规划、工具调用、后台执行，能力一步步接近 agent。",
            "放入证据：deception、cheating、自我保存实验，讲清楚哪些是已观察到的风险信号。",
            "解释市场压力：企业奖励能替代劳动的系统，所以更强 agent 会被持续推出来。",
            "讲 Scientist AI：先让模型可靠预测和校验，少把高风险执行权直接交出去。",
            "接到你的频道：Codex、Claude Code 用户已经在体验执行权迁移，只是规模还在早期。",
            "落点：效率可以交给 AI，责任边界要重新设计。",
        ]
        personal_judgment_entries = [
            "我会把 AI 分成两类：帮我理解世界的 AI，和替我执行任务的 AI。后者每多走一步，就要多一道校验。",
            "Bengio 这场演讲适合和 Codex、Claude Code 放在一起看，因为最敏感的变化发生在后台执行里。",
            "普通用户不用先卷进末日论。更现实的问题是：我今天让 AI 动了哪些文件、调用了哪些工具、替我做了哪些决定？",
        ]
        sample_opening = (
            "Bengio 这场 TED 最耐看的地方，是他没有一上来讲模型参数。"
            "他先讲自己的儿子 Patrick 学会说 Pa-pa 的那一刻。"
            "一个孩子开始用语言理解世界，也开始表达自己的意愿。"
            "这听起来离 AI 很远，但 Bengio 想借这个场景讲一件事：能力和行动意愿一旦连在一起，风险就会换一种形状。"
            "过去我们担心 AI 回答错，现在更麻烦的场景是，它能计划、能调用工具、能完成任务，还可能学会隐藏意图和保护自己。"
        )
    else:
        titles = [
            f"{speaker} 这场演讲，适合先看他为什么此刻开口",
            f"《{title}》的重点：把大议题拆回人的处境",
            f"这场演讲值得看的，是它怎样把问题讲具体",
        ]
        openings = [
            {
                "route": "人物 / 立场",
                "text": f"看 {speaker} 这场演讲，先别急着摘金句。更重要的是看他站在什么位置，说给谁听，又为什么在这个时间点把问题讲出来。",
            },
            {
                "route": "问题 / 动机",
                "text": f"《{title}》适合改成内容的地方，在于演讲者怎样把一个大问题压回具体场景。",
            },
            {
                "route": "个人 IP / 观众",
                "text": "如果把这场演讲改成你的频道内容，最该保留的是观众听完以后能拿走的一句判断和一个行动边界。",
            },
        ]
        oral_script_beats = [
            "开场先交代演讲者的位置和说话对象。",
            "提取演讲里的第一个具体场景或例子。",
            "拆论证链：他先承认什么，再推进什么。",
            "放入一个观众最可能反驳的问题。",
            "解释这个反驳为什么重要。",
            "落到你的个人判断和本周可执行动作。",
        ]
        personal_judgment_entries = [
            "我更关心这场演讲能不能改变我这周的判断，少停在概念摘抄。",
            "如果一个观点只能做成摘要，说明它还没有进入我的工作流。",
        ]
        sample_opening = (
            f"{speaker} 这场演讲可以先从一个问题进入：他为什么要在这个时间点说这件事。"
            "演讲不是资料库，好的地方通常藏在它的推进顺序里：先把观众带进一个具体处境，再慢慢抬高问题的重量。"
        )

    pack = {
        "candidate_titles": titles,
        "opening_options": openings,
        "oral_script_beats": oral_script_beats,
        "personal_judgment_entries": personal_judgment_entries,
        "sample_opening": sample_opening,
        "guardrails": [
            "避免二段式警句和固定反转结构。",
            "每段先有事实、场景、动作或具体机制，再放判断。",
            "不要把演讲改成摘要清单；保留演讲的进入方式和压力递进。",
        ],
        "source_anchor": (talk_report.get("key_excerpts") or [])[:2],
    }
    return clean_report_text_object(pack)


def build_fallback_angles(payload: dict[str, Any]) -> list[str]:
    title = payload["title"]
    transcript = str(payload.get("transcript_plain") or "")
    lower = f"{title}\n{transcript}".lower()
    if "claude code" in lower and ("six months from now" in lower or "terminal" in lower):
        return [
            "Claude Code 可以从“为六个月后的模型做产品”这条线切入。",
            "终端不是复古选择，而是早期产品验证里成本最低、反馈最快的入口。",
            "这条访谈适合写成开发者如何把 AI 从聊天框带进真实工作流。",
        ]
    if is_short_product_tutorial(payload):
        steps = extract_product_tutorial_steps(payload)
        first = steps[0] if steps else "打开工具"
        second = steps[1] if len(steps) > 1 else "完成核心功能"
        third = steps[-1] if len(steps) > 2 else "导出结果"
        return [
            f"可以写成一条短教程：从“{first}”开始，让观众照着做。",
            f"可以写成工具演示：重点看“{second}”是否真的省事。",
            f"可以写成替代方案对比：最后用“{third}”判断它能不能替代原工具。",
        ]
    key_points: list[str] = payload.get("key_points") or []
    angle_signal = ""
    if key_points:
        first_point = re.sub(r"^\d{2}:\d{2}(?::\d{2})?\s*", "", str(key_points[0]))
        first_point = re.sub(r"^片段\s*\d+[：:]\s*", "", first_point)
        first_point = re.sub(r"^[^：:]{1,20}[：:]\s*", "", first_point)
        angle_signal = first_complete_sentence(first_point)
        if angle_signal and not contains_cjk(angle_signal):
            angle_signal = ""
        if len(angle_signal) > 40:
            angle_signal = ""
    if angle_signal:
        return [
            f"这条视频可以从“{angle_signal}”这层判断方式切入。",
            f"如果改写成个人 IP 内容，先抓《{title}》背后的现实门槛，少复述结论。",
            "适合拆成“信息焦虑里先要做哪一步”，少做宏大趋势复述。",
        ]
    return [
        f"标题《{title}》可以转成“先看这件事的成本”。",
        "优先写成个人判断，少列知识点清单。",
        "把结论压缩成一个真实动作，会比三段式鸡汤更像真人说话。",
    ]


def is_claude_code_product_interview(payload: dict[str, Any]) -> bool:
    title = str(payload.get("title") or "")
    transcript = str(payload.get("transcript_plain") or "")
    lower = f"{title}\n{transcript}".lower()
    return "claude code" in lower and ("six months from now" in lower or "terminal" in lower)


def build_talking_points_for_rules(payload: dict[str, Any], key_points: list[str]) -> list[str]:
    if is_claude_code_product_interview(payload):
        return [
            "Boris 的核心产品判断：不要只为今天的模型设计，要押注六个月后模型会补上的能力。",
            "Claude Code 起点是终端，关键在于它让原型最快进入真实工程师手里。",
            "早期价值先出现在低风险、重复、靠上下文推进的任务里，比如 git、bash、单测、项目文件整理。",
            "CLAUDE.md 这类记忆文件说明，AI 编程工具真正进入工作流后，需要稳定吸收团队习惯和项目规则。",
            "这条访谈最适合拿来讲 AI 编程的产品阶段：从演示能力，走向真实项目里的持续协作。",
        ]
    if is_short_product_tutorial(payload):
        steps = extract_product_tutorial_steps(payload)
        return [f"步骤 {index + 1}：{step}。" for index, step in enumerate(steps)]
    return key_points[:5]


def build_core_claim(payload: dict[str, Any]) -> str:
    outline = payload.get("outline") or []
    title = str(payload.get("title") or "")
    channel = str(payload.get("channel") or "").strip()
    if is_claude_code_product_interview(payload):
        return "Claude Code 的关键线索，是 Anthropic 先押注模型六个月后的能力，再用终端这种低成本形态快速交给工程师试。"
    if is_short_product_tutorial(payload):
        steps = extract_product_tutorial_steps(payload)
        subject = f"{channel} 这条短视频" if channel else "这条短视频"
        if len(steps) >= 2:
            return f"{subject}演示《{title}》的操作链：先{steps[0]}，再{steps[1]}。"
        return f"{subject}演示《{title}》的具体操作步骤。"
    if len(outline) >= 2:
        return f"这条内容把重点放在 {outline[0]['title']} 和 {outline[1]['title']} 两个条件上，判断标准更接近真实使用成本。"
    if title:
        return f"这条内容围绕《{title}》背后的现实成本和判断标准展开。"
    return "这条内容的重点是背后的现实门槛。"


def build_hidden_premises(payload: dict[str, Any]) -> list[str]:
    transcript_plain = str(payload.get("transcript_plain") or "")
    title = str(payload.get("title") or "")
    hints: list[str] = []
    if "系统" in transcript_plain or "策略" in transcript_plain:
        hints.append("它默认可重复执行的系统比临时灵感更重要。")
    if "现金流" in transcript_plain or "生活费" in transcript_plain or "收入" in transcript_plain:
        hints.append("它默认只谈机会没有意义，先能活下去才有资格谈长期。")
    if "自律" in transcript_plain or "纪律" in transcript_plain or "耐心" in transcript_plain:
        hints.append("它默认长期差距更依赖纪律和耐心。")
    if "风险" in transcript_plain or "杠杆" in transcript_plain:
        hints.append("它默认高收益叙事不成立，风险承受结构才是真门槛。")
    if not hints and title:
        hints.append(f"它默认《{title}》这个问题不能只靠热情回答，必须回到成本、门槛和代价。")
    return hints[:4]


def build_creator_tactics(payload: dict[str, Any]) -> list[str]:
    outline = payload.get("outline") or []
    tactics: list[str] = []
    if outline:
        tactics.append("先把抽象问题拆成几段，让观众看到可判断的材料。")
    tactics.append("先讲门槛和代价，内容会更可信。")
    tactics.append("用数字、条件、例子去压住空泛结论，比单纯输出观点更容易建立权威感。")
    if payload.get("visual_notes"):
        tactics.append("视觉上如果封面足够明确，就先用封面给主题定调，再让正文承接。")
    return tactics[:4]


def build_channel_adaptation(payload: dict[str, Any]) -> list[str]:
    title = str(payload.get("title") or "")
    if is_claude_code_product_interview(payload):
        return [
            "开头可以先讲产品选择：为什么一个改变开发方式的工具，起点反而是最朴素的终端。",
            "中段放 Boris 的产品判断：面向六个月后的模型能力设计，别只围着当下的模型短板打转。",
            "结尾接到个人使用经验：AI 编程工具的价值不在炫技，关键是能不能稳定进入真实项目。",
        ]
    if is_short_product_tutorial(payload):
        steps = extract_product_tutorial_steps(payload)
        first = steps[0] if steps else "打开工具"
        second = steps[1] if len(steps) > 1 else "完成核心操作"
        third = steps[-1] if len(steps) > 2 else "导出结果"
        return [
            f"适合写成短教程：先讲谁需要这个功能，再从“{first}”进入。",
            f"中段按操作顺序走，不要泛讲效率，直接演示“{second}”。",
            f"结尾落到验收：看结果能不能直接用，再交代“{third}”。",
        ]
    outline = payload.get("outline") or []
    first_section = outline[0]["title"] if outline else "现实门槛"
    return [
        f"适合从 {first_section} 进入，再把《{title or '这类话题'}》拆成可判断的使用条件。",
        "中段不要复述原视频顺序，改成你最认同的一点 + 你最保留的一点，会更像个人 IP。",
        "结尾别停在总结，最好落成一句具体边界，例如“多数人还没准备好”。",
    ]


def build_source_gaps(payload: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    transcript_source = str(payload.get("transcript_source") or "")
    transcript_count = int(payload.get("transcript_source_count") or 0)
    visual_assets = payload.get("visual_assets") or []
    visual_notes = " ".join(str(item) for item in payload.get("visual_notes") or [])
    if not transcript_count:
        gaps.append("没有可用字幕，不能进入严肃写稿。")
    elif transcript_source.startswith("rosetta"):
        gaps.append("字幕来自网页兜底，适合做初筛，正式写稿前最好再核一次原视频。")
    elif transcript_source == "none":
        gaps.append("字幕来源为空，当前只能按标题、简介和画面做粗略判断。")
    if not any(isinstance(asset, dict) and asset.get("type") == "frame" for asset in visual_assets):
        gaps.append("没有关键帧，画面证据较弱。")
    if "frame-extraction-disabled" in visual_notes:
        gaps.append("本次关闭了抽帧，缺少视频画面层面的辅助判断。")
    comment_count = payload.get("comment_count")
    comments_preview = payload.get("comments_preview") if isinstance(payload.get("comments_preview"), list) else []
    if comments_preview:
        gaps.append(f"只读到 {len(comments_preview)} 条评论样本，不能代表完整讨论。")
    elif isinstance(comment_count, int) and comment_count > 0:
        gaps.append("只拿到评论数，还没有读评论正文和外部讨论。")
    else:
        gaps.append("还没有评论区/外部报道，热度和争议点需要单独补。")
    return gaps[:5]


def build_writing_brief(payload: dict[str, Any], analysis: dict[str, Any], source_gaps: list[str]) -> str:
    title = str(payload.get("title") or "Untitled")
    lines = [
        f"题目：{title}",
        "",
        "核心观点：",
        str(analysis.get("core_claim") or "").strip() or "(none)",
        "",
        "可写方向：",
    ]
    for item in analysis.get("repurpose_angles") or []:
        lines.append(f"- {item}")
    lines.extend(["", "材料依据："])
    for item in analysis.get("talking_points") or []:
        lines.append(f"- {item}")
    lines.extend(["", "读者可能会问："])
    for item in analysis.get("hidden_premises") or []:
        lines.append(f"- {item}")
    lines.extend(["", "缺口："])
    for item in source_gaps:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "写作要求：",
            "- 用中文写，适合个人 IP 口播/文章。",
            "- 先讲具体材料，再给判断。",
            "- 不要写成视频摘要。",
            "- 避免“不是…而是…”、“真正…”、“这意味着”等模板句。",
            "- 输出前先自查：核心观点是否清楚、证据是否够、是否像人在说话。",
        ]
    )
    return "\n".join(lines).strip()


def build_editorial_decision(payload: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    source_gaps = build_source_gaps(payload)
    transcript_count = int(payload.get("transcript_source_count") or 0)
    has_angles = bool(analysis.get("repurpose_angles"))
    has_claim = bool(str(analysis.get("core_claim") or "").strip())
    score = 0
    if transcript_count >= 80:
        score += 2
    elif transcript_count:
        score += 1
    if has_claim:
        score += 1
    if has_angles:
        score += 1
    if is_claude_code_product_interview(payload):
        score += 1
    if any("没有可用字幕" in item or "字幕来源为空" in item for item in source_gaps):
        score -= 2
    if any("还没有评论区" in item for item in source_gaps):
        score -= 1

    if score >= 4:
        level = "值得写"
        reason = "有完整字幕、清楚观点和可延展选题，可以开始写一版。"
    elif score >= 2:
        level = "一般"
        reason = "可以做素材，但还需要补评论区、外部报道或更具体的个人判断。"
    elif transcript_count:
        level = "只适合存档"
        reason = "有一点材料，但选题张力不足，暂时不建议直接写。"
    else:
        level = "材料不足"
        reason = "缺少可靠字幕或核心材料。"

    candidates = list(analysis.get("repurpose_angles") or [])[:3]
    if not candidates and str(payload.get("title") or ""):
        candidates = [f"从《{payload.get('title')}》拆一个现实使用门槛"]

    return clean_report_text_object(
        {
            "level": level,
            "score": score,
            "reason": reason,
            "candidates": candidates,
            "gaps": source_gaps,
            "brief": build_writing_brief(payload, analysis, source_gaps),
        }
    )


def build_rules_visual_timeline(payload: dict[str, Any]) -> list[str]:
    timeline: list[str] = []
    for asset in payload.get("visual_assets") or []:
        label = describe_visual_asset(asset)
        source = str(asset.get("source") or "")
        if asset.get("type") == "frame":
            path = asset.get("path")
            suffix = f"：{path}" if path else ""
            timeline.append(f"{label}{suffix}")
        elif asset.get("type") == "thumbnail":
            url = asset.get("url")
            suffix = f"：{url}" if url else ""
            timeline.append(f"{label} ({source or 'thumbnail'}){suffix}")
    return timeline[:8]


def analyze_with_rules(payload: dict[str, Any]) -> dict[str, Any]:
    report_type = classify_report_type(payload)
    visual_timeline = build_rules_visual_timeline(payload)
    if report_type == "talk":
        talk_report = build_talk_report(payload)
        creator_draft_pack = build_creator_draft_pack(payload, talk_report)
        analysis = {
            "backend": "rules",
            "report_type": report_type,
            "summary": " ".join(talk_report["summary"]),
            "core_claim": talk_report["summary"][0],
            "recommended_hook": talk_report["channel_angles"][0] if talk_report["channel_angles"] else "",
            "content_outline": talk_report["argument_chain"],
            "talking_points": talk_report["evidence_examples"],
            "repurpose_angles": talk_report["channel_angles"],
            "hidden_premises": talk_report["tensions"],
            "creator_tactics": [
                "先交代演讲者为什么有资格说这件事。",
                "用演讲里的具体例子支撑判断，少把它压成口号。",
                "把技术概念翻成普通人能判断的任务边界。",
            ],
            "channel_adaptation": [
                "适合做成“顶级学者为什么突然把 AI agent 讲得这么重”的解释型内容。",
                "中段连接到 Codex、Claude Code、后台 agent，把 TED 的大风险落到真实工具体验。",
                "结尾留一个具体问题：哪些任务可以交给 AI，哪些执行权还不该交出去。",
            ],
            "visual_timeline": visual_timeline,
            "anti_ai_notes": [
                "不要用二段式警句包装结论。",
                "先讲演讲里的动作链和证据，再给个人判断。",
                "引用原文时只取短句，避免整段搬运。",
            ],
            "talk_report": talk_report,
            "creator_draft_pack": creator_draft_pack,
        }
        analysis["editorial_decision"] = build_editorial_decision(payload, analysis)
        return clean_report_text_object(analysis)

    outline = payload.get("outline") or []
    key_points = payload.get("key_points") or []
    transcript_preview = payload.get("transcript_preview") or ""
    opener = key_points[0] if key_points else compact_text(transcript_preview, 90)

    summary_parts = [
        f"这条 {payload['platform']} 视频核心在讲 {payload['title']}。",
        f"发布者是 {payload['channel']}，时长 {payload['duration_human']}。",
    ]
    if outline:
        summary_parts.append(
            "内容结构比较清楚，主要分成 " + " / ".join(section["title"] for section in outline[:4]) + "。"
        )
    elif opener:
        summary_parts.append(f"从已拿到的转写看，最先冒出来的重点是：{compact_text(opener, 80)}。")

    talking_points = build_talking_points_for_rules(payload, key_points)
    if not talking_points and transcript_preview:
        talking_points = [
            line.strip()
            for line in transcript_preview.splitlines()
            if line.strip()
        ][:5]

    if is_short_product_tutorial(payload):
        steps = extract_product_tutorial_steps(payload)
        content_outline = [
            f"先交代使用场景：为什么要给视频快速加字幕。",
            f"再按操作走：{steps[0] if steps else '打开工具'}。",
            f"中段讲核心功能：{steps[1] if len(steps) > 1 else '完成自动处理'}。",
            f"最后验收结果：{steps[-1] if steps else '导出成品'}。",
        ]
    else:
        content_outline = [
            "先说这条视频想回答的现实门槛。",
            "再拆它给出的条件、代价、风险控制。",
            "最后补一句你自己的判断：哪些人现在适合做，哪些人先别急。",
        ]
    if is_claude_code_product_interview(payload):
        content_outline = [
            "先讲 Anthropic 的产品判断：为六个月后的模型能力设计，别只追今天的可用性。",
            "再讲为什么终端形态能留下来：它便宜、直接、能最快接触真实工程任务。",
            "中段拆早期使用场景：git、bash、单测、项目文件、团队记忆。",
            "最后落到开发者参与门槛：真正使用 AI 编程，需要把项目上下文持续交给它。",
        ]
    elif outline:
        content_outline = [
            f"开场先点明 {outline[0]['title']} 为什么是真门槛。",
            "中段拆实际条件、资源成本、心理成本。",
            "结尾给一个可执行动作，少喊口号。",
        ]

    analysis = {
        "backend": "rules",
        "report_type": report_type,
        "summary": " ".join(summary_parts),
        "core_claim": build_core_claim(payload),
        "recommended_hook": compact_text(
            build_core_claim(payload), 90
        ),
        "content_outline": content_outline,
        "talking_points": talking_points,
        "repurpose_angles": build_fallback_angles(payload),
        "hidden_premises": build_hidden_premises(payload),
        "creator_tactics": build_creator_tactics(payload),
        "channel_adaptation": build_channel_adaptation(payload),
        "visual_timeline": visual_timeline,
        "anti_ai_notes": [
            "不要把信息整理得太完美，保留一点判断和取舍。",
            "先讲你真正同意的一点，再讲你不完全同意的一点。",
            "能落到成本、风险、门槛，就别只讲趋势。",
            "少用“AI时代”“认知升级”“普通人一定要”这种套话。",
        ],
    }
    analysis["editorial_decision"] = build_editorial_decision(payload, analysis)
    return clean_report_text_object(analysis)


def analyze_with_openai_compatible(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        import requests
    except Exception as exc:
        raise RuntimeError(f"requests unavailable: {exc}") from exc

    base_url = os.environ.get("VIDEO_ANALYSIS_API_BASE", "").rstrip("/")
    model = os.environ.get("VIDEO_ANALYSIS_MODEL", "").strip()
    if not base_url or not model:
        raise RuntimeError("VIDEO_ANALYSIS_API_BASE or VIDEO_ANALYSIS_MODEL is missing")

    prompt = (
        "你是一个中文内容研究助手。请基于给定视频的文本和视觉素材线索，输出 JSON，包含："
        "summary, recommended_hook, content_outline, talking_points, repurpose_angles, anti_ai_notes。"
        "要求适合个人 IP 内容，少 AI 味，明确区分原视频内容和适合二次创作的角度。"
    )

    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": build_openai_compatible_user_content(payload),
            },
        ],
        "response_format": {"type": "json_object"},
    }

    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("VIDEO_ANALYSIS_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=request_payload,
        timeout=180,
    )
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    parsed["backend"] = "openai-compatible"
    return parsed


def analyze_with_mlx_vlm_local(payload: dict[str, Any]) -> dict[str, Any]:
    model_name = os.environ.get("VIDEO_ANALYSIS_MODEL", "").strip()
    if not model_name:
        raise RuntimeError("VIDEO_ANALYSIS_MODEL is missing")

    try:
        from mlx_vlm import load
        from mlx_vlm.generate import PromptCacheState, stream_generate
        from mlx_vlm.prompt_utils import apply_chat_template
    except Exception as exc:
        raise RuntimeError(f"mlx-vlm unavailable: {exc}") from exc

    visual_assets = payload.get("visual_assets") or []
    visual_inputs = resolve_local_visual_inputs(visual_assets, limit=4)
    if not visual_inputs or not visual_assets:
        result = analyze_with_rules(payload)
        result["backend"] = "mlx-vlm-local"
        result["visual_summary"] = ""
        return result

    model, processor = load(model_name)
    selected_assets = list(visual_assets[: len(visual_inputs)])
    visual_timeline: list[str] = []
    cover_summary = ""

    for asset, image_path in zip(selected_assets, visual_inputs):
        asset_type = str(asset.get("type") or "image")
        label = describe_visual_asset(asset)
        prompt_text = (
            "请只根据这张视频封面，用中文输出两句话："
            "第一句写最明显的主体、情绪和场景；"
            "第二句写它暗示的视频主题和受众。"
            if asset_type == "thumbnail"
            else "请只根据这张视频关键帧，用中文一句话概括这一刻画面里正在发生什么，尽量具体。"
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]
        prompt = apply_chat_template(processor, model.config, messages, num_images=1)
        asset_summary = ""
        for chunk in stream_generate(
            model,
            processor,
            prompt,
            image=[image_path],
            max_tokens=120,
            temperature=0.2,
            prompt_cache_state=PromptCacheState(),
        ):
            asset_summary += chunk.text
        asset_summary = normalize_visual_summary(asset_summary)
        if not asset_summary:
            continue
        if asset_type == "thumbnail" and not cover_summary:
            cover_summary = asset_summary
        visual_timeline.append(f"{label}：{compact_text(asset_summary, 120)}")

    augmented_payload = dict(payload)
    visual_notes = list(payload.get("visual_notes") or [])
    visual_summary = "\n".join(visual_timeline)
    if visual_summary:
        visual_notes.append(f"local-vlm:{compact_text(visual_summary, 240)}")
    augmented_payload["visual_notes"] = visual_notes

    result = analyze_with_rules(augmented_payload)
    if cover_summary:
        result["summary"] = compact_text(
            f"{result['summary']} 封面视觉给出的第一印象是：{cover_summary}",
            500,
        )
    if visual_timeline:
        result["talking_points"] = list(visual_timeline[:3]) + list(result.get("talking_points") or [])
    result["visual_timeline"] = visual_timeline
    result["backend"] = "mlx-vlm-local"
    result["visual_summary"] = visual_summary
    return result


def asset_path_to_data_url(path: str) -> str | None:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None

    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def asset_url_to_data_url(url: str, timeout: int = 20) -> str | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            data = response.read()
            mime_type = response.headers.get_content_type() or "application/octet-stream"
    except Exception:
        return None

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def asset_url_to_temp_file(url: str, suffix: str = ".img", timeout: int = 20) -> str | None:
    try:
        try:
            import requests

            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.content
            content_type = response.headers.get("content-type", "")
        except Exception:
            with urlopen(url, timeout=timeout) as response:
                data = response.read()
                content_type = response.headers.get_content_type() or ""
    except Exception:
        return None

    guessed_suffix = mimetypes.guess_extension(content_type) or suffix
    temp_dir = DEFAULT_OUTPUT / "_tmp_assets"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=guessed_suffix, delete=False) as handle:
        handle.write(data)
        return handle.name


def build_openai_compatible_user_content(payload: dict[str, Any]) -> list[dict[str, Any]]:
    payload_for_model = dict(payload)
    visual_assets = payload_for_model.pop("visual_assets", []) or []

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "下面是视频结构化信息。请结合后续图片线索一起分析，不要只复述文本。\n"
                + json.dumps(payload_for_model, ensure_ascii=False)
            ),
        }
    ]

    for asset in visual_assets[:8]:
        image_url = None
        if asset.get("url"):
            image_url = asset_url_to_data_url(str(asset["url"]))
        elif asset.get("path"):
            image_url = asset_path_to_data_url(str(asset["path"]))

        if not image_url:
            continue

        label = json.dumps(
            {
                "type": asset.get("type") or "image",
                "source": asset.get("source") or "unknown",
                "origin": asset.get("url") or asset.get("path") or "unknown",
            },
            ensure_ascii=False,
        )
        content.append({"type": "text", "text": f"视觉素材线索: {label}"})
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    return content


def resolve_local_visual_inputs(visual_assets: list[dict[str, Any]], limit: int = 4) -> list[str]:
    resolved: list[str] = []
    image_assets = [
        asset
        for asset in visual_assets
        if isinstance(asset, dict) and asset.get("type") in {"thumbnail", "frame"}
    ]
    for asset in image_assets[:limit]:
        image_path = None
        if asset.get("path"):
            candidate = Path(str(asset["path"]))
            if candidate.exists() and candidate.is_file():
                image_path = str(candidate)
        elif asset.get("url"):
            image_path = asset_url_to_temp_file(str(asset["url"]))
        if image_path:
            resolved.append(image_path)
    return resolved


def run_analysis_backend(backend: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    if backend == "rules":
        return analyze_with_rules(payload), notes
    if backend == "openai-compatible":
        try:
            return analyze_with_openai_compatible(payload), notes
        except Exception as exc:
            notes.append(f"openai-compatible-fallback:{exc}")
            return analyze_with_rules(payload), notes
    if backend == "mlx-vlm-local":
        try:
            return analyze_with_mlx_vlm_local(payload), notes
        except Exception as exc:
            notes.append(f"mlx-vlm-local-fallback:{exc}")
            return analyze_with_rules(payload), notes
    raise ValueError(f"Unsupported analysis backend: {backend}")


def render_markdown_report(
    url: str,
    platform: str,
    info: dict[str, Any],
    auth_note: str,
    transcript_source: str,
    transcript_notes: list[str],
    caption_files: list[Path],
    outline: list[dict[str, Any]],
    key_points: list[str],
    visual_assets: list[dict[str, Any]],
    visual_notes: list[str],
    analysis: dict[str, Any],
    backend_notes: list[str],
    transcript_preview: str,
) -> str:
    title = str(info.get("title") or "Untitled")
    subtitles = info.get("subtitles") or {}
    auto_captions = info.get("automatic_captions") or {}
    subtitle_langs = sorted(subtitles.keys()) if isinstance(subtitles, dict) else sorted(str(item) for item in subtitles)
    auto_caption_langs = (
        sorted(auto_captions.keys())
        if isinstance(auto_captions, dict)
        else sorted(str(item) for item in auto_captions)
    )

    lines = [
        f"# {title}",
        "",
        "## 核心判断",
        "",
        str(analysis.get("core_claim") or "(none)").strip(),
        "",
    ]
    editorial = analysis.get("editorial_decision") or {}
    if editorial:
        lines.extend(
            [
                "## 可写评分",
                "",
                f"{editorial.get('level') or '未评级'}：{editorial.get('reason') or ''}",
                "",
                "## 选题候选",
                "",
            ]
        )
        for item in editorial.get("candidates") or []:
            lines.append(f"- {item}")
        if not editorial.get("candidates"):
            lines.append("(none)")
        lines.extend(["", "## 缺口提示", ""])
        for item in editorial.get("gaps") or []:
            lines.append(f"- {item}")
        if not editorial.get("gaps"):
            lines.append("(none)")
        lines.extend(["", "## 写稿 Brief", "", editorial.get("brief") or "(none)", ""])

    lines.extend([
        "## 适合怎么写",
        "",
    ])
    for item in analysis.get("channel_adaptation") or []:
        lines.append(f"- {item}")
    if not analysis.get("channel_adaptation"):
        lines.append("(none)")

    lines.extend(["", "## 可写选题", ""])
    for item in analysis.get("repurpose_angles") or []:
        lines.append(f"- {item}")
    if not analysis.get("repurpose_angles"):
        lines.append("(none)")

    lines.extend(["", "## 最值得抓的点", ""])
    for item in (analysis.get("talking_points") or key_points or [])[:6]:
        lines.append(f"- {item}")
    if not (analysis.get("talking_points") or key_points):
        lines.append("(none)")

    lines.extend(["", "## 先别急着相信的地方", ""])
    for item in analysis.get("hidden_premises") or []:
        lines.append(f"- {item}")
    if not analysis.get("hidden_premises"):
        lines.append("- 这条视频目前只能按已有字幕和描述分析；没有人工二次核对前，不要把所有数字和细节直接当最终事实。")

    lines.extend(["", "## 写稿提醒", ""])
    for item in analysis.get("anti_ai_notes") or []:
        lines.append(f"- {item}")
    if not analysis.get("anti_ai_notes"):
        lines.append("- 先讲材料里的具体动作，再给判断。")

    lines.extend(["", "## 内容结构", ""])
    if analysis.get("content_outline"):
        for item in analysis.get("content_outline") or []:
            lines.append(f"- {item}")
    elif outline:
        for section in outline:
            lines.append(f"- {format_timestamp(section['start'])} {section['title']}: {section['summary']}")
    else:
        lines.append("(none)")

    lines.extend(["", "## 画面 / 证据", ""])

    if visual_assets:
        for asset in visual_assets[:8]:
            location = asset.get("path") or asset.get("url") or "unknown"
            if asset.get("type") == "frame":
                lines.append(f"- {describe_visual_asset(asset)}: {location}")
            elif asset.get("type") == "thumbnail":
                lines.append(f"- 封面: {location}")
            else:
                lines.append(f"- {asset.get('type')}: {location}")
    else:
        lines.append("(none)")

    talk_report = analysis.get("talk_report") or {}
    if talk_report:
        lines.extend(["", "## 人物 / 动机 / 论证链", ""])
        speaker_context = talk_report.get("speaker_context")
        if speaker_context:
            lines.append(str(speaker_context))
            lines.append("")
        for item in talk_report.get("argument_chain") or []:
            lines.append(f"- {item}")
        if not talk_report.get("argument_chain"):
            lines.append("(none)")

        excerpts = talk_report.get("key_excerpts") or []
        if excerpts:
            lines.extend(["", "## 原文短句", ""])
            for item in excerpts[:4]:
                lines.append(f"- {item}")

    creator_draft_pack = analysis.get("creator_draft_pack") or {}
    if creator_draft_pack:
        lines.extend(["", "## 可直接进入写稿的材料", ""])
        titles = creator_draft_pack.get("candidate_titles") or []
        if titles:
            lines.append("标题方向：")
            for item in titles[:5]:
                lines.append(f"- {item}")
            lines.append("")

        openings = creator_draft_pack.get("opening_options") or []
        if openings:
            lines.append("开头方向：")
            for item in openings[:3]:
                route = item.get("route") or "route"
                text = item.get("text") or ""
                lines.append(f"- {route}: {text}")
            lines.append("")

        beats = creator_draft_pack.get("oral_script_beats") or []
        if beats:
            lines.append("口播节奏：")
            for item in beats[:8]:
                lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 技术信息",
            "",
            f"- URL: {url}",
            f"- Platform: {platform}",
            f"- Video ID: `{info.get('id') or 'unknown'}`",
            f"- Channel: {info.get('channel') or info.get('uploader') or 'unknown'}",
            f"- Duration: {format_duration(info.get('duration'))}",
            f"- Upload date: {info.get('upload_date') or 'unknown'}",
            f"- View count: {info.get('view_count') or 'unknown'}",
            f"- Auth: {auth_note}",
            f"- Transcript source: {transcript_source}",
            f"- Transcript notes: {', '.join(transcript_notes) or 'none'}",
            f"- Visual notes: {', '.join(visual_notes) or 'none'}",
            f"- Analysis backend: {analysis.get('backend') or 'unknown'}",
            f"- Report type: {analysis.get('report_type') or 'general'}",
            f"- Backend notes: {', '.join(backend_notes) or 'none'}",
            f"- Manual subtitles: {', '.join(subtitle_langs) or 'none'}",
            f"- Auto captions: {', '.join(auto_caption_langs[:30]) or 'none'}",
            f"- Downloaded caption files: {', '.join(path.name for path in caption_files) or 'none'}",
            "",
            "## 字幕预览",
            "",
            transcript_preview,
            "",
        ]
    )
    return remove_user_banned_report_phrasing("\n".join(lines).rstrip() + "\n")


def first_complete_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""
    if "..." in text:
        text = text.split("...", 1)[0].strip()
    if len(text) > 120:
        text = text[:120].rsplit("，", 1)[0].strip(" ，")
    if not text:
        return ""
    parts = re.split(r"[。！？!?]", text)
    for part in parts:
        cleaned = part.strip(" ，,；;：:")
        if 12 <= len(cleaned) <= 60:
            return cleaned
    return text


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def derive_specific_video_angle(title: str, payload: dict[str, Any]) -> dict[str, Any]:
    outline_titles = " ".join(str(item.get("title") or "") for item in payload.get("outline") or [])
    source_text = " ".join(
        [
            title,
            str(payload.get("description_preview") or ""),
            outline_titles,
            str(payload.get("transcript_preview") or "")[:3000],
        ]
    ).lower()

    if any(term in source_text for term in ["background agent", "background agents", "devin", "spec-to-pr", "pull request"]):
        return {
            "claim": "这条视频最有价值的点是：AI 编程正在从手把手聊天，转向后台 agent 直接跑到 pull request。",
            "practical_angle": "门槛已经转到 repo setup、权限、测试和验证。",
            "core": [
                "后台 agent 的关键是能从 spec 稳定推进到 PR。",
                "企业买的是 dev environment、权限、集成、审查和落地流程。",
                "vibe coding 的风险集中在代码库质量守不住，项目会倒退到最差工程师的水平。",
            ],
            "angles": [
                "AI 编程的下一步：自己跑完验证链路。",
                "“会点按钮”的 computer use 离真正测试软件还差什么。",
                "普通人看 Devin，不该只看 7x PR，而要看它背后的环境、权限和验证成本。",
            ],
            "final_take": "这条视频值得拆，因为它把 AI 编程从“写代码”推进到了“谁来负责验证、权限和交付”的阶段。",
        }

    if any(term in source_text for term in ["trained and served", "how gpt", "gemini", "claude"]):
        return {
            "claim": "这类视频适合拆大模型从训练到服务背后的真实工程约束。",
            "practical_angle": "普通人不需要复述所有技术细节，但要知道一次回答背后有训练、推理、成本和延迟的取舍。",
            "core": [
                "模型能力不是凭空冒出来的，它背后是训练、服务和成本之间的工程取舍。",
                "懂一点底层机制，能减少很多“模型突然变聪明/变笨”的信息焦虑。",
                "这类内容适合做成学者式解释，但不要讲成论文摘要。",
            ],
            "angles": [
                "为什么同样叫大模型，训练时和上线服务时完全是两套问题。",
                "普通人看 GPT、Claude、Gemini，最该理解的是成本和延迟怎么影响体验。",
                "别只追模型榜单，先理解一次回答背后的工程账。",
            ],
            "final_take": "这类视频的价值在于帮你把模型崇拜拆回工程现实。",
        }

    return {}


def build_rewrite_pack(
    info: dict[str, Any],
    transcript_source: str,
    analysis: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    title = str(info.get("title") or "Untitled")
    channel = str(info.get("channel") or info.get("uploader") or "unknown")
    duration = format_duration(info.get("duration"))
    summary = str(analysis.get("summary") or "")
    core_claim = str(analysis.get("core_claim") or "")
    hook = str(analysis.get("recommended_hook") or "")
    outline = payload.get("outline") or []
    first_outline = str(outline[0]["summary"]) if outline else ""
    first_point = str((payload.get("key_points") or [""])[0] or "")
    transcript_preview = str(payload.get("transcript_preview") or "")
    raw_signal = first_complete_sentence(first_outline) or first_complete_sentence(first_point) or first_complete_sentence(transcript_preview)
    if raw_signal and not contains_cjk(raw_signal):
        raw_signal = ""

    specific_angle = derive_specific_video_angle(title, payload)
    concise_claim = specific_angle.get("claim") or core_claim or summary or raw_signal or f"{title} 这类话题不能只看热度，还得看它到底能不能真的进入工作流。"
    practical_angle = specific_angle.get("practical_angle") or raw_signal or "真正值钱的是它能不能替你吞掉前置整理工作。"

    short_video_lines = [
        f"如果你是做内容的，我觉得你现在至少该认真看一眼 `{title}` 这类工具。",
        "原因在于，很多人还把它理解窄了。",
        concise_claim,
        "对内容创作者来说，最有用的地方通常在前面那些很碎、很耗人的整理工作。",
        "找资料、拆教程、拉结构、先起一版稿，这些活如果能先被接住，整个工作流就会轻很多。",
        "但别神化。",
        "它能替你推进一部分工作，不代表它能替你长脑子。",
        "最后该不该讲、怎么讲、像不像你，还是你自己决定。",
    ]

    personal_judgment_lines = [
        f"这两天我看了一条《{title}》的视频，里面有个判断我基本认同。",
        f"很多人现在还把这类东西当成程序员工具，这个问题可以先放一边。",
        "更值得看的是，它有没有开始进入普通人的工作流。",
        "我的理解是，已经开始了。",
        practical_angle,
        "这也是我现在看这类工具时最在意的一点。",
        "关键看它能不能稳定替你往前推任务。",
        "如果你本来就在做内容、做资料整理、做信息提炼，这件事就已经有现实价值了。",
        "但如果手里本来没有素材、没有判断、没有表达，只想靠它一键生成，那最后出来的东西大概率还是会很空。",
    ]

    social_post_lines = [
        f"最近越来越觉得，很多人把 `{title}` 这种工具理解窄了。",
        "它不只是一个会聊天或者会写代码的东西。",
        "更实际一点说，它是那种你可以直接交任务的 AI。",
        "先找资料，先做整理，先拉结构，先起草稿。",
        "真正省时间的地方，往往在前面那堆重复劳动。",
        "当然，前提是你自己本来就有判断。",
        "它能替你做前置工作，不能替你负责最后的观点。",
    ]

    cold_open_lines = [
        f"很多人讨论《{title}》，还停留在它是不是给某一类人用的。",
        "我觉得这个问题已经没那么重要了。",
        "更重要的是，它有没有开始稳定进入真实工作流。",
        "如果一款工具能先把那些不值钱但必须做的前置劳动吞掉，它就不再只是玩具。",
        "我现在看中的，就是这一点。",
    ]

    angles = list(specific_angle.get("angles") or []) + [
        f"很多人把 {title} 当成单点工具，我更关心它能不能真正替人推进任务。",
        "真正省时间的地方，是先把脏活做了。",
        "内容创作者更需要会接任务的 AI。",
    ]
    if raw_signal:
        angles.append(raw_signal)

    avoid_lines = [
        "所有人都应该用",
        "完全没有门槛",
        "抓紧起飞",
        "改一改官方教程就能直接做成课",
    ]

    safer_lines = [
        "如果你本来就在做内容，这类工具值得认真试。",
        "门槛转到了判断能力上。",
        "它不负责替你变专业，但能先替你扛掉一部分重复劳动。",
    ]

    final_take = specific_angle.get("final_take") or (
        f"`{title}` 值得用，原因在于它开始能稳定接住内容工作里最烦的那段前置劳动。"
    )

    return {
        "meta": {
            "title": title,
            "channel": channel,
            "duration": duration,
            "transcript_source": transcript_source,
        },
        "core_takeaway": specific_angle.get("core")
        or [
            concise_claim,
            "它更像工作型 AI，而不只是对话型 AI。",
            "真正的价值在于吞掉搜集、整理、起稿这类前置劳动。",
        ],
        "short_video_script": short_video_lines,
        "personal_judgment_script": personal_judgment_lines,
        "social_post": social_post_lines,
        "cold_open": cold_open_lines,
        "angles": angles[:4],
        "avoid_lines": avoid_lines,
        "safer_lines": safer_lines,
        "final_take": final_take,
        "source_note": "原始转写可能存在 ASR 噪音，适合做改写和选题提炼，不适合当逐字引用依据。",
    }


def render_rewrite_pack(pack: dict[str, Any]) -> str:
    meta = pack["meta"]
    lines = [
        f"# {meta['title']} 内容改写",
        "",
        "原视频：",
        "",
        f"- 标题：{meta['title']}",
        f"- 作者：{meta['channel']}",
        f"- 时长：{meta['duration']}",
        f"- 当前可用依据：结构化视频分析 + 本地转写（{meta['transcript_source']}）",
        f"- 注意：{pack['source_note']}",
        "",
        "## 我提炼出来的核心",
        "",
    ]
    for index, item in enumerate(pack.get("core_takeaway") or [], start=1):
        lines.append(f"{index}. {item}")

    sections = [
        ("版本 1：短视频口播版", "short_video_script"),
        ("版本 2：更像你频道的个人判断版", "personal_judgment_script"),
        ("版本 3：适合发小红书 / B站动态的短文案", "social_post"),
        ("版本 4：更冷一点的 TheMarketMemo 式开头", "cold_open"),
    ]
    for title, key in sections:
        lines.extend(["", f"## {title}", ""])
        for item in pack.get(key) or []:
            lines.extend([item, ""])

    lines.extend(["## 这条视频的可用选题角度", ""])
    for index, item in enumerate(pack.get("angles") or [], start=1):
        lines.append(f"{index}. `{item}`")

    lines.extend(["", "## 这条视频里我不建议直接照搬的话", ""])
    for item in pack.get("avoid_lines") or []:
        lines.append(f"- {item}")

    lines.extend(["", "更稳的写法是：", ""])
    for item in pack.get("safer_lines") or []:
        lines.append(f"- `{item}`")

    lines.extend(["", "## 我给你的最终建议", "", pack.get("final_take") or "", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_batch_summary_markdown(
    requested: int,
    results: list[dict[str, Any]],
    failures: list[dict[str, str]],
) -> str:
    lines = [
        "# 批量视频分析汇总",
        "",
        f"- 请求数量：{requested}",
        f"- 成功数量：{len(results)}",
        f"- 失败数量：{len(failures)}",
        "",
        "## 成功条目",
        "",
    ]

    if not results:
        lines.append("(none)")
    for index, item in enumerate(results, start=1):
        title = item.get("title") or item.get("video_id") or "Untitled"
        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- URL: {item.get('url') or 'unknown'}",
                f"- Video ID: `{item.get('video_id') or 'unknown'}`",
                f"- Channel: {item.get('channel') or 'unknown'}",
                f"- Duration: {item.get('duration_human') or 'unknown'}",
                f"- Transcript source: {item.get('transcript_source') or 'unknown'}",
                f"- Notes: {item.get('note_path') or 'unknown'}",
                f"- JSON: {item.get('json_path') or 'unknown'}",
            ]
        )
        rewrites_path = item.get("rewrites_path")
        if rewrites_path:
            lines.append(f"- Rewrites: {rewrites_path}")
        core_claim = compact_text(str(item.get("core_claim") or ""), 180)
        if core_claim:
            lines.extend(["", "核心判断：", "", core_claim])
        angles = item.get("repurpose_angles") or []
        if angles:
            lines.extend(["", "可用角度：", ""])
            for angle in angles[:3]:
                lines.append(f"- {angle}")
        final_take = compact_text(str(item.get("final_take") or ""), 180)
        if final_take:
            lines.extend(["", "推荐落点：", "", final_take])
        lines.append("")

    lines.extend(["## 失败条目", ""])
    if not failures:
        lines.append("(none)")
    else:
        for item in failures:
            lines.append(f"- {item.get('url')}: {item.get('error')}")

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_topic_pool_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# 批量选题池",
        "",
        f"- 视频数量：{len(results)}",
        "- 说明：这不是摘要总表，而是把每条视频里更适合直接发内容的题目先拎出来。",
        "",
    ]

    if not results:
        lines.append("(none)")
        lines.append("")
        return "\n".join(lines)

    for index, item in enumerate(results, start=1):
        title = str(item.get("title") or item.get("video_id") or "Untitled")
        channel = str(item.get("channel") or "unknown")
        angles = item.get("repurpose_angles") or []
        final_take = compact_text(str(item.get("final_take") or ""), 160)
        core_claim = compact_text(str(item.get("core_claim") or ""), 160)

        lines.extend(
            [
                f"## {index}. {title}",
                "",
                f"- 来源频道：{channel}",
                f"- 原视频：{item.get('url') or 'unknown'}",
            ]
        )
        rewrites_path = item.get("rewrites_path")
        if rewrites_path:
            lines.append(f"- 改写稿：{rewrites_path}")
        if core_claim:
            lines.extend(["", "原视频核心：", "", core_claim])

        lines.extend(["", "可直接拿来发的题目：", ""])
        if angles:
            for angle_index, angle in enumerate(angles[:5], start=1):
                lines.append(f"{angle_index}. {angle}")
        else:
            lines.append("1. 先别看热闹，先看这件事到底值不值得进你的工作流。")
            lines.append("2. 这类工具真正省下来的，往往不是最后输出，而是前置劳动。")

        if final_take:
            lines.extend(["", "建议落点：", "", final_take])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def load_urls(args_url: list[str], url_file: str | None) -> list[str]:
    urls: list[str] = []
    for item in args_url:
        cleaned = item.strip()
        if cleaned:
            urls.append(cleaned)
    if url_file:
        for raw_line in Path(url_file).expanduser().read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create structured video analysis notes")
    parser.add_argument("url", nargs="*")
    parser.add_argument(
        "--url-file",
        default=None,
        help="Optional text file with one video URL per line. Lines starting with # are ignored.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--langs",
        default="zh.*,zh-Hans,zh-Hant,zh,en.*",
        help="Comma-separated subtitle language preferences for yt-dlp",
    )
    parser.add_argument(
        "--cookies-file",
        default=None,
        help="Optional Netscape cookies file. Can also be set via YOUTUBE_COOKIES_FILE.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        help="Optional yt-dlp browser cookie source, such as chrome or safari.",
    )
    parser.add_argument(
        "--disable-video-parser",
        action="store_true",
        help="Skip local video parser transcript lookup.",
    )
    parser.add_argument(
        "--disable-whisper-fallback",
        action="store_true",
        help="Do not attempt local audio transcription fallback.",
    )
    parser.add_argument(
        "--disable-transcript-fallbacks",
        action="store_true",
        help="Do not attempt web transcript fallbacks such as Rosetta/Glasp after local transcript methods fail.",
    )
    parser.add_argument(
        "--analysis-backend",
        default="rules",
        choices=sorted(SUPPORTED_RULES_BACKENDS),
        help="Reasoning backend. openai-compatible can target a local no-key gateway.",
    )
    parser.add_argument(
        "--extract-frames",
        action="store_true",
        help="Download the video and extract keyframes with ffmpeg when available.",
    )
    parser.add_argument(
        "--frame-interval-seconds",
        type=int,
        default=45,
        help="Frame interval in seconds when --extract-frames is enabled.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=6,
        help="Maximum number of keyframes to keep.",
    )
    parser.add_argument(
        "--target-frame-seconds",
        default="",
        help="Optional comma-separated timestamps for targeted frame extraction.",
    )
    parser.add_argument(
        "--skip-rewrites",
        action="store_true",
        help="Do not emit the companion *_rewrites.md file.",
    )
    parser.add_argument(
        "--include-comments",
        action="store_true",
        help="Opt in to yt-dlp comment retrieval. This can be slow and is not required for the default video note flow.",
    )
    return parser


def process_url(args: argparse.Namespace, url: str, progress_callback=None) -> dict[str, Any]:
    def report(stage: str, message: str, **extra: Any) -> None:
        if progress_callback:
            progress_callback(stage, message, extra)

    out_dir = Path(args.output_dir).expanduser().resolve()
    langs = [item.strip() for item in args.langs.split(",") if item.strip()]
    cookies_file = args.cookies_file or os.environ.get("YOUTUBE_COOKIES_FILE")
    platform = detect_platform(url)
    auth_probe_opts: dict[str, Any] = {}
    auth_note = apply_cookie_options(auth_probe_opts, platform, cookies_file, args.cookies_from_browser)
    report("fetch", "正在抓取视频元数据")
    bootstrap_notes: list[str] = []
    try:
        info, new_files = extract_video(
            url,
            out_dir,
            langs,
            cookies_file=cookies_file,
            cookies_from_browser=args.cookies_from_browser,
            include_comments=bool(getattr(args, "include_comments", False)),
        )
    except Exception as exc:
        message = str(exc)
        if platform == "bilibili" and "bilibili-fetch-412" in message:
            bootstrap_notes.append(message)
            report("fetch", "yt-dlp 被 B站 412 拦截，改用公开元数据接口")
            info, new_files = fetch_bilibili_public_info(url, bootstrap_notes)
        else:
            raise

    video_id = str(info.get("id") or "unknown")
    video_slug = safe_name(video_id)
    report("fetch", "元数据已拿到", platform=platform, video_id=video_id, title=str(info.get("title") or "Untitled"))
    note_path = out_dir / f"{video_slug}_notes.md"
    json_path = out_dir / f"{video_slug}_info.json"
    rewrites_path = out_dir / f"{video_slug}_rewrites.md"
    transcript_json_path = out_dir / f"{video_slug}_transcript.json"
    transcript_md_path = out_dir / f"{video_slug}_transcript.md"
    asset_dir = out_dir / video_slug

    predownload_notes: list[str] = []
    required_local_source_video: Path | None = None
    if bool(getattr(args, "require_local_video", False)):
        report("download", "正在保存本地视频")
        required_local_source_video = download_video_for_frames_with_auth(
            url,
            asset_dir / "source-download",
            cookies_file=cookies_file,
            cookies_from_browser=args.cookies_from_browser,
            notes=predownload_notes,
            progress_callback=progress_callback,
            playable_video=True,
        )
        if required_local_source_video is None:
            detail = "; ".join(predownload_notes[-8:]) or "没有本地视频文件"
            raise RuntimeError(f"视频下载失败，已停止分析。没有本地视频文件；{detail}")
        required_local_source_video = persist_source_video_for_material(
            required_local_source_video,
            asset_dir,
            notes=predownload_notes,
        )
        report(
            "download",
            "本地视频已保存",
            local_video_path=str(required_local_source_video),
            local_video_size=required_local_source_video.stat().st_size,
        )

    caption_files = sort_caption_files([path for path in new_files if path.suffix.lower() in {".vtt", ".srt", ".ttml"}])
    transcript_items: list[dict[str, Any]] = []
    transcript_source = "none"
    transcript_notes: list[str] = [*bootstrap_notes, *predownload_notes]

    if not args.disable_video_parser and should_try_video_parser(platform):
        report("transcript", "尝试 video-parser")
        transcript_items, parser_error = try_video_parser_transcript(url)
        if transcript_items:
            transcript_source = "video-parser"
            report("transcript", "video-parser 成功", transcript_source=transcript_source, transcript_count=len(transcript_items))
        elif parser_error:
            transcript_notes.append(parser_error)
    elif not args.disable_video_parser:
        transcript_notes.append(f"video-parser-skipped:platform-{platform}")

    if not transcript_items and caption_files:
        report("transcript", "尝试现成字幕")
        transcript_items = extract_caption_transcript(caption_files)
        if transcript_items:
            transcript_source = "yt-dlp-captions"
            report("transcript", "字幕提取成功", transcript_source=transcript_source, transcript_count=len(transcript_items))

    if not transcript_items:
        transcript_items, embedded_source = extract_embedded_subtitle_transcript(info, transcript_notes)
        if transcript_items:
            transcript_source = embedded_source or "yt-dlp-embedded-subtitle"
            report("transcript", "yt-dlp 内嵌字幕提取成功", transcript_source=transcript_source, transcript_count=len(transcript_items))

    if not transcript_items:
        cached_caption_files = find_cached_caption_files(out_dir, video_slug)
        if cached_caption_files:
            transcript_items = extract_caption_transcript(cached_caption_files)
            if transcript_items:
                transcript_source = f"local-cached-caption:{cached_caption_files[0].name}"
                transcript_notes.append("local-cached-caption:fallback-before-asr")
                report(
                    "transcript",
                    "本地缓存字幕成功",
                    transcript_source=transcript_source,
                    transcript_count=len(transcript_items),
                )

    if not transcript_items and platform == "bilibili":
        report("transcript", "尝试 B站字幕接口")
        transcript_items, bilibili_source = try_bilibili_api_transcript(url, info, transcript_notes)
        if transcript_items:
            transcript_source = bilibili_source or "bilibili-subtitle-api"
            report("transcript", "B站字幕接口成功", transcript_source=transcript_source, transcript_count=len(transcript_items))

    if not transcript_items and platform == "bilibili":
        report("transcript", "尝试 BBDown 字幕兜底")
        transcript_items, bbdown_source = try_bbdown_bilibili_transcript(url, out_dir, transcript_notes)
        if transcript_items:
            transcript_source = bbdown_source or "bbdown-subtitle"
            report("transcript", "BBDown 字幕兜底成功", transcript_source=transcript_source, transcript_count=len(transcript_items))

    if not transcript_items and not args.disable_whisper_fallback:
        report("transcript", "尝试音频转写 fallback")
        with tempfile.TemporaryDirectory(prefix="video-notes-") as tmp_dir:
            audio_path = download_audio_for_transcription_with_auth(
                url,
                Path(tmp_dir),
                cookies_file=cookies_file,
                cookies_from_browser=args.cookies_from_browser,
                notes=transcript_notes,
            )
            if audio_path is None:
                if not can_download_audio():
                    transcript_notes.append("whisper-fallback-skipped:no-ffmpeg")
                else:
                    transcript_notes.append("whisper-fallback-failed:audio-download")
            else:
                limit_seconds = default_transcription_limit_seconds(platform)
                transcribe_path = limit_audio_duration(audio_path, limit_seconds)
                if transcribe_path != audio_path:
                    transcript_notes.append(f"whisper-preview:first-{limit_seconds}s")
                    report("transcript", f"音频已截取前 {limit_seconds} 秒用于快速转写", transcript_limit_seconds=limit_seconds)
                transcript_items, whisper_source = transcribe_audio(transcribe_path)
                if transcript_items:
                    transcript_source = whisper_source
                    report("transcript", "音频转写成功", transcript_source=transcript_source, transcript_count=len(transcript_items))
                else:
                    transcript_notes.append(whisper_source)

    if not transcript_items and not args.disable_transcript_fallbacks and platform == "youtube":
        report("transcript", "尝试 Rosetta/Glasp 转录兜底")
        transcript_items, fallback_source = fetch_rosetta_transcript(
            url,
            title=str(info.get("title") or ""),
            channel=str(info.get("channel") or info.get("uploader") or ""),
        )
        if transcript_items:
            transcript_source = fallback_source or "web-transcript-fallback"
            transcript_notes.append("web-transcript-fallback:video-download-unavailable")
            report(
                "transcript",
                "网页转录兜底成功",
                transcript_source=transcript_source,
                transcript_count=len(transcript_items),
            )
        elif fallback_source:
            transcript_notes.append(fallback_source)

    if not transcript_items:
        cached_caption_files = find_cached_caption_files(out_dir, video_slug)
        if cached_caption_files:
            transcript_items = extract_caption_transcript(cached_caption_files)
            if transcript_items:
                transcript_source = f"local-cached-caption:{cached_caption_files[0].name}"
                transcript_notes.append("local-cached-caption:fallback-after-online-failure")
                report(
                    "transcript",
                    "本地缓存字幕兜底成功",
                    transcript_source=transcript_source,
                    transcript_count=len(transcript_items),
                )

    if not transcript_items:
        report("transcript", "没有拿到 transcript", transcript_source=transcript_source, transcript_notes=transcript_notes)

    transcript_json_path, transcript_md_path = write_transcript_artifacts(
        out_dir,
        video_slug,
        transcript_items,
        transcript_source,
        transcript_notes,
    )
    report(
        "transcript",
        "transcript 已落盘",
        transcript_json_path=str(transcript_json_path),
        transcript_md_path=str(transcript_md_path),
    )

    chapters = parse_description_chapters(str(info.get("description") or ""))
    outline = build_outline_sections(transcript_items, chapters)
    key_points = build_key_points(outline, transcript_items)
    transcript_preview = (
        compact_text(transcript_items_to_text(transcript_items, with_timestamps=True), 12000)
        if transcript_items
        else "(No transcript content resolved.)"
    )

    visual_assets = resolve_cover_assets(info)
    visual_notes: list[str] = []
    if args.extract_frames:
        report("analysis", "尝试抽帧")
        frame_assets, frame_notes = extract_keyframes(
            url,
            asset_dir,
            args.frame_interval_seconds,
            args.max_frames,
            cookies_file=cookies_file,
            cookies_from_browser=args.cookies_from_browser,
            target_seconds=getattr(args, "target_frame_seconds", None),
            source_video_path=required_local_source_video,
        )
        visual_assets.extend(frame_assets)
        visual_notes.extend(frame_notes)
    else:
        visual_notes.append("frame-extraction-disabled")

    report("analysis", "开始结构化分析", analysis_backend=args.analysis_backend)
    payload = build_analysis_payload(
        url,
        platform,
        info,
        transcript_items,
        outline,
        key_points,
        visual_assets,
        visual_notes,
        transcript_source,
    )
    analysis, backend_notes = run_analysis_backend(args.analysis_backend, payload)
    report("analysis", "结构化分析完成", analysis_backend=analysis.get("backend"), core_claim=analysis.get("core_claim"))

    report("report", "开始写入报告")
    report_markdown = render_markdown_report(
        url,
        platform,
        info,
        auth_note,
        transcript_source,
        transcript_notes,
        caption_files,
        outline,
        key_points,
        visual_assets,
        visual_notes,
        analysis,
        backend_notes,
        transcript_preview,
    )
    rewrite_pack = build_rewrite_pack(info, transcript_source, analysis, payload)
    rewrites_markdown = render_rewrite_pack(rewrite_pack)
    report_markdown = remove_user_banned_report_phrasing(report_markdown)
    rewrites_markdown = remove_user_banned_report_phrasing(rewrites_markdown)
    source_video_candidates = sorted(asset_dir.glob("source-video*"))
    source_video_path = str(source_video_candidates[0]) if source_video_candidates else ""
    download_policy = download_policy_from_notes(
        platform=platform,
        auth_note=auth_note,
        notes=transcript_notes + visual_notes,
        local_video_path=source_video_path,
        require_local_video=bool(getattr(args, "require_local_video", False)),
    )

    json_payload = {
        "id": video_id,
        "platform": platform,
        "title": str(info.get("title") or "Untitled"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "comments_preview": payload.get("comments_preview") or [],
        "webpage_url": info.get("webpage_url"),
        "subtitles": sorted((info.get("subtitles") or {}).keys()),
        "automatic_captions": sorted((info.get("automatic_captions") or {}).keys()),
        "caption_files": [str(path) for path in caption_files],
        "auth": auth_note,
        "transcript_source": transcript_source,
        "transcript_notes": transcript_notes,
        "chapters": chapters,
        "outline": outline,
        "key_points": key_points,
        "transcript_preview": transcript_preview,
        "transcript_segments": normalize_transcript_items(transcript_items),
        "transcript_json_path": str(transcript_json_path),
        "transcript_md_path": str(transcript_md_path),
        "source_video_path": source_video_path,
        "download_policy": download_policy,
        "visual_assets": visual_assets,
        "visual_notes": visual_notes,
        "analysis_backend": analysis.get("backend"),
        "backend_notes": backend_notes,
        "analysis": analysis,
        "analysis_payload": payload,
        "rewrites_path": str(rewrites_path),
        "rewrite_pack": rewrite_pack,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(json_payload, handle, ensure_ascii=False, indent=2)
    note_path.write_text(report_markdown, encoding="utf-8")
    if not args.skip_rewrites:
        rewrites_path.write_text(rewrites_markdown, encoding="utf-8")
    report(
        "report",
        "报告已写入",
        note_path=str(note_path),
        json_path=str(json_path),
        transcript_json_path=str(transcript_json_path),
        transcript_md_path=str(transcript_md_path),
        rewrites_path=str(rewrites_path) if not args.skip_rewrites else "",
    )

    result = {
        "url": url,
        "video_id": video_id,
        "title": str(info.get("title") or "Untitled"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration_human": format_duration(info.get("duration")),
        "transcript_source": transcript_source,
        "transcript_notes": transcript_notes,
        "transcript_segments": normalize_transcript_items(transcript_items),
        "core_claim": analysis.get("core_claim"),
        "repurpose_angles": analysis.get("repurpose_angles") or [],
        "final_take": rewrite_pack.get("final_take"),
        "note_path": str(note_path),
        "json_path": str(json_path),
        "transcript_json_path": str(transcript_json_path),
        "transcript_md_path": str(transcript_md_path),
        "source_video_path": source_video_path,
        "download_policy": download_policy,
    }
    if not args.skip_rewrites:
        result["rewrites_path"] = str(rewrites_path)
    return result


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    urls = load_urls(args.url, args.url_file)
    if not urls:
        parser.error("Provide at least one URL or use --url-file")

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for url in urls:
        try:
            result = process_url(args, url)
        except Exception as exc:
            failures.append({"url": url, "error": str(exc)})
            continue
        results.append(result)
        print(result["note_path"])
        print(result["json_path"])
        rewrites_path = result.get("rewrites_path")
        if rewrites_path:
            print(rewrites_path)

    if len(urls) > 1:
        summary = {
            "requested": len(urls),
            "succeeded": len(results),
            "failed": len(failures),
            "results": results,
            "failures": failures,
        }
        summary_dir = Path(args.output_dir).expanduser().resolve()
        summary_path = summary_dir / "batch_run_summary.json"
        summary_md_path = summary_dir / "batch_run_summary.md"
        topic_pool_path = summary_dir / "topic_pool.md"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        summary_md_path.write_text(
            render_batch_summary_markdown(len(urls), results, failures),
            encoding="utf-8",
        )
        topic_pool_path.write_text(
            render_topic_pool_markdown(results),
            encoding="utf-8",
        )
        print(summary_path)
        print(summary_md_path)
        print(topic_pool_path)

    return 1 if failures and not results else 0


if __name__ == "__main__":
    raise SystemExit(main())
