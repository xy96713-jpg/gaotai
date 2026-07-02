#!/usr/bin/env python3
"""Collect front-line AI/vibe-coding signals from configured public sources."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from xml.etree import ElementTree

import requests

WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = WORKSPACE / "source_watchlist.yaml"
DEFAULT_OUTPUT = WORKSPACE / ".cache" / "source-watch"
USER_AGENT = "ai-codex-source-watch/0.1 by local user"


@dataclass
class Signal:
    source_type: str
    source_name: str
    title: str
    url: str
    published: str = ""
    summary: str = ""
    score: float = 0.0
    editorial_score: float = 0.0
    editorial_reasons: list[str] | None = None
    matched_keywords: list[str] | None = None
    raw: dict[str, Any] | None = None


def compact_text(value: str, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]


def parse_simple_watchlist(path: Path) -> dict[str, Any]:
    list_sections = {"reddit", "youtube", "web_rss", "hn", "arxiv", "openalex"}
    config: dict[str, Any] = {
        "reddit": [],
        "youtube": [],
        "web_rss": [],
        "hn": [],
        "arxiv": [],
        "openalex": [],
        "manual_x": {},
        "scoring": {},
    }
    section: str | None = None
    current: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            if current and section in list_sections:
                config[section].append(current)
                current = None
            section = line[:-1].strip()
            continue
        if section in list_sections:
            stripped = line.strip()
            if stripped.startswith("- "):
                if current:
                    config[section].append(current)
                current = {}
                stripped = stripped[2:].strip()
                if stripped:
                    key, value = stripped.split(":", 1)
                    current[key.strip()] = parse_value(value.strip())
            elif current is not None and ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = parse_value(value.strip())
            continue
        if section in {"manual_x", "scoring"}:
            stripped = line.strip()
            if stripped.startswith("- "):
                key = config[section].get("_last_key") or "_items"
                config[section].setdefault(key, []).append(stripped[2:].strip())
            elif ":" in stripped:
                key, value = stripped.split(":", 1)
                parsed = parse_value(value.strip())
                config[section][key.strip()] = parsed
                if parsed == []:
                    config[section]["_last_key"] = key.strip()
            continue
        if section and line.strip().startswith("- "):
            key = config[section].get("_last_key")
            if key:
                config[section].setdefault(key, []).append(line.strip()[2:].strip())

    if current and section in list_sections:
        config[section].append(current)
    config.get("manual_x", {}).pop("_last_key", None)
    config.get("manual_x", {}).pop("_last_list", None)
    return config


def parse_value(value: str) -> Any:
    if value == "":
        return []
    if value.startswith("["):
        return parse_inline_list(value)
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("'\"")


def keyword_matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def score_signal(signal: Signal, keywords: list[str], scoring: dict[str, Any]) -> Signal:
    matches = keyword_matches(f"{signal.title} {signal.summary}", keywords)
    keyword_weight = float(scoring.get("keyword_weight") or 2)
    score = signal.score + len(matches) * keyword_weight
    if is_low_value_signal(signal):
        score -= 4
    signal.score = round(score, 2)
    signal.matched_keywords = matches
    apply_editorial_score(signal)
    return signal


def apply_editorial_score(signal: Signal) -> Signal:
    text = f"{signal.title} {signal.summary}".lower()
    score = signal.score
    reasons: list[str] = []

    if signal.source_type == "reddit":
        score += 1
        reasons.append("真实用户讨论")
    if signal.source_type == "youtube":
        score += 0.5
        reasons.append("可拆表达结构")
    if signal.source_type == "web_rss":
        score += 0.5
        reasons.append("外部文章/新闻线索")
    if signal.source_type == "hn":
        score += 1
        reasons.append("开发者真实讨论")
    if signal.source_type in {"arxiv", "openalex"}:
        score += 1
        reasons.append("学术/报告证据")
    if signal.source_type == "manual_x":
        score += 0.5
        reasons.append("前线观点线索")

    if any(word in text for word in ["codex", "claude code", "cursor", "vibe coding", "codebase"]):
        score += 3
        reasons.append("vibe coding / AI coding 高相关")
    if any(word in text for word in ["agent", "agents", "automation", "cloud agent"]):
        score += 2
        reasons.append("Agent 工作流相关")
    if "$20" in text or contains_whole_term(text, ["limit", "limits", "pricing", "cost", "costs", "subscription", "usage"]):
        score += 2
        reasons.append("价格/限制/使用摩擦")
    if any(word in text for word in ["context", "workflow", "project grows", "large project"]):
        score += 2
        reasons.append("真实工作流痛点")
    if any(word in text for word in ["how gpt", "trained", "served", "google i/o", "agi"]):
        score += 1.5
        reasons.append("适合做学者/报告式解释")
    if any(word in text for word in ["adhd", "neurodivergent", "executive function", "dopamine", "focus"]):
        score += 4
        reasons.append("神经差异/ADHD 与 AI 时代")
    if any(word in text for word in ["religion", "god", "spiritual", "spirituality", "church", "ritual", "worship"]):
        score += 4
        reasons.append("AI 与宗教/意义感")
    if any(word in text for word in ["pope", "leo xiv", "vatican", "encyclical", "magnifica humanitas", "disarm", "dehumanization"]):
        score += 5
        reasons.append("全球道德权威/教廷 AI 信号")
    if any(word in text for word in ["prophecy", "prophet", "apocalypse", "doom", "utopia", "messiah", "cult"]):
        score += 3.5
        reasons.append("预言/末世感/类宗教叙事")
    if any(word in text for word in ["lonely", "companion", "therapy", "meaning", "identity", "status anxiety"]):
        score += 2.5
        reasons.append("情绪与身份焦虑")
    if any(word in text for word in ["class", "status", "wealth", "rich", "billionaire", "labor", "workplace"]):
        score += 3
        reasons.append("阶层/金钱/工作尊严")
    if any(word in text for word in ["dating", "relationship", "relationships", "intimacy", "texting", "companion"]):
        score += 2.5
        reasons.append("亲密关系与陪伴")
    if any(word in text for word in ["beauty", "skincare", "skin analysis", "weight loss", "diet", "body image"]):
        score += 2.5
        reasons.append("身体/健康/审美")
    if any(word in text for word in ["education", "school", "homework", "cheating", "parenting", "teacher"]):
        score += 2.5
        reasons.append("教育/家庭/下一代")
    if any(word in text for word in ["authority", "trust", "expert", "doctor", "teacher", "lawyer", "advisor"]):
        score += 2.5
        reasons.append("权威替代/信任转移")
    if any(word in text for word in ["information overload", "information anxiety", "burnout", "attention", "overwhelmed"]):
        score += 2.5
        reasons.append("信息焦虑/注意力")
    if any(word in text for word in ["evaluation", "benchmark", "eval", "swe-bench", "safety", "alignment", "governance"]):
        score += 1.5
        reasons.append("可验证评测/治理线索")

    if is_low_value_signal(signal):
        score -= 5
        reasons.append("低价值/推广/泛互动")
    if any(word in text for word in ["meme", "hilarious", "caveman", "all i have to say"]):
        score -= 2
        reasons.append("偏梗图或娱乐反应")
    if "megathread" in text:
        score -= 2
        reasons.append("合集帖，需人工筛")

    signal.editorial_score = round(score, 2)
    signal.editorial_reasons = reasons
    return signal


def contains_whole_term(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)


def is_low_value_signal(signal: Signal) -> bool:
    text = f"{signal.title} {signal.summary}".lower()
    low_value_patterns = [
        "drop your projects",
        "share what you're working on",
        "official r/vibecoding discord",
        "come hang on",
        "get a shoutout",
        "shout out",
        "alphabet of countries",
    ]
    return any(pattern in text for pattern in low_value_patterns)


def parse_xml_entries(xml_text: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml_text)
    entries: list[dict[str, str]] = []
    for node in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = node.findtext("{http://www.w3.org/2005/Atom}title") or ""
        summary = node.findtext("{http://www.w3.org/2005/Atom}summary") or ""
        published = node.findtext("{http://www.w3.org/2005/Atom}published") or node.findtext(
            "{http://www.w3.org/2005/Atom}updated"
        ) or ""
        link = ""
        for link_node in node.findall("{http://www.w3.org/2005/Atom}link"):
            href = link_node.attrib.get("href")
            if href:
                link = href
                break
        entries.append({"title": title, "summary": summary, "published": published, "url": link})
    if entries:
        return entries

    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        summary = item.findtext("description") or ""
        published = item.findtext("pubDate") or ""
        link = item.findtext("link") or ""
        entries.append({"title": title, "summary": summary, "published": published, "url": link})
    return entries


def fetch_text(url: str, timeout: int = 25) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def collect_reddit_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    subreddit = str(source["subreddit"])
    sort = str(source.get("sort") or "hot")
    keywords = list(source.get("keywords") or [])
    url = f"https://www.reddit.com/r/{quote(subreddit)}/{quote(sort)}/.rss"
    text = fetch_text(url)
    signals: list[Signal] = []
    for entry in parse_xml_entries(text)[:limit]:
        signal = Signal(
            source_type="reddit",
            source_name=f"r/{subreddit}",
            title=compact_text(entry.get("title", ""), 180),
            url=entry.get("url", ""),
            published=entry.get("published", ""),
            summary=compact_text(strip_html(entry.get("summary", "")), 260),
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def collect_youtube_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    try:
        from yt_dlp import YoutubeDL
    except Exception as exc:
        raise RuntimeError(f"yt-dlp unavailable: {exc}") from exc

    name = str(source.get("name") or source.get("url") or "YouTube")
    url = normalize_youtube_channel_url(str(source["url"]))
    keywords = list(source.get("keywords") or [])
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "playlistend": limit,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") or []
    signals: list[Signal] = []
    for entry in entries[:limit]:
        video_url = entry.get("url") or entry.get("webpage_url") or ""
        if video_url and not str(video_url).startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"
        title = compact_text(str(entry.get("title") or ""), 180)
        if is_youtube_tab_entry(title, str(video_url)):
            continue
        signal = Signal(
            source_type="youtube",
            source_name=name,
            title=title,
            url=str(video_url),
            published=str(entry.get("timestamp") or entry.get("release_timestamp") or ""),
            summary=compact_text(str(entry.get("description") or ""), 260),
            score=float(scoring.get("youtube_recent_weight") or 2),
            raw={"id": entry.get("id")},
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def collect_web_rss_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    name = str(source.get("name") or source.get("query") or source.get("url") or "web RSS")
    keywords = list(source.get("keywords") or [])
    url = str(source.get("url") or "")
    if not url:
        query = str(source["query"])
        url = "https://news.google.com/rss/search?" + urlencode(
            {
                "q": query,
                "hl": "en-US",
                "gl": "US",
                "ceid": "US:en",
            }
        )
    text = fetch_text(url)
    signals: list[Signal] = []
    for entry in parse_xml_entries(text)[:limit]:
        signal = Signal(
            source_type="web_rss",
            source_name=name,
            title=compact_text(entry.get("title", ""), 180),
            url=entry.get("url", ""),
            published=entry.get("published", ""),
            summary=compact_text(strip_html(entry.get("summary", "")), 260),
            score=float(scoring.get("web_rss_weight") or 1.5),
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def collect_hn_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    name = str(source.get("name") or source.get("query") or "Hacker News")
    query = str(source.get("query") or "")
    keywords = list(source.get("keywords") or [])
    min_points = int(source.get("min_points") or 0)
    min_comments = int(source.get("min_comments") or 0)
    filters = ["created_at_i>" + str(int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp()))]
    if min_points:
        filters.append(f"points>{min_points}")
    if min_comments:
        filters.append(f"num_comments>{min_comments}")
    params = {
        "query": query,
        "tags": str(source.get("tags") or "story"),
        "hitsPerPage": str(limit),
        "numericFilters": ",".join(filters),
    }
    url = "https://hn.algolia.com/api/v1/search_by_date?" + urlencode(params)
    payload = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25)
    payload.raise_for_status()
    hits = payload.json().get("hits") or []
    signals: list[Signal] = []
    for hit in hits[:limit]:
        points = int(hit.get("points") or 0)
        comments = int(hit.get("num_comments") or 0)
        signal = Signal(
            source_type="hn",
            source_name=name,
            title=compact_text(str(hit.get("title") or hit.get("story_title") or ""), 180),
            url=str(hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"),
            published=str(hit.get("created_at") or ""),
            summary=compact_text(strip_html(str(hit.get("story_text") or hit.get("comment_text") or "")), 260),
            score=round(points * 0.03 + comments * 0.08, 2),
            raw={
                "objectID": hit.get("objectID"),
                "points": points,
                "num_comments": comments,
                "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
            },
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def collect_arxiv_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    name = str(source.get("name") or source.get("query") or "arXiv")
    query = str(source["query"])
    keywords = list(source.get("keywords") or [])
    url = "https://export.arxiv.org/api/query?" + urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    text = fetch_text(url)
    signals: list[Signal] = []
    for entry in parse_xml_entries(text)[:limit]:
        signal = Signal(
            source_type="arxiv",
            source_name=name,
            title=compact_text(entry.get("title", ""), 180),
            url=entry.get("url", ""),
            published=entry.get("published", ""),
            summary=compact_text(strip_html(entry.get("summary", "")), 360),
            score=float(scoring.get("academic_weight") or 1.5),
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def collect_openalex_source(source: dict[str, Any], limit: int, scoring: dict[str, Any]) -> list[Signal]:
    name = str(source.get("name") or source.get("query") or "OpenAlex")
    query = str(source["query"])
    keywords = list(source.get("keywords") or [])
    from_date = (datetime.now(timezone.utc) - timedelta(days=int(source.get("days") or 30))).date().isoformat()
    url = "https://api.openalex.org/works?" + urlencode(
        {
            "search": query,
            "filter": f"from_publication_date:{from_date}",
            "sort": "publication_date:desc",
            "per-page": str(limit),
        }
    )
    payload = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25)
    payload.raise_for_status()
    results = payload.json().get("results") or []
    signals: list[Signal] = []
    for item in results[:limit]:
        signal = Signal(
            source_type="openalex",
            source_name=name,
            title=compact_text(str(item.get("display_name") or ""), 180),
            url=str(item.get("doi") or item.get("id") or ""),
            published=str(item.get("publication_date") or ""),
            summary=compact_text(openalex_abstract(item.get("abstract_inverted_index") or {}), 360),
            score=float(scoring.get("academic_weight") or 1.5),
            raw={"cited_by_count": item.get("cited_by_count"), "type": item.get("type")},
        )
        signals.append(score_signal(signal, keywords, scoring))
    return signals


def openalex_abstract(index: dict[str, list[int]]) -> str:
    if not isinstance(index, dict) or not index:
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            positioned.append((int(position), str(word)))
    return " ".join(word for _, word in sorted(positioned))


def normalize_youtube_channel_url(url: str) -> str:
    if "youtube.com/@" in url and not re.search(r"/(videos|shorts|streams)(?:\?|$)", url):
        return url.rstrip("/") + "/videos"
    return url


def is_youtube_tab_entry(title: str, url: str) -> bool:
    lowered = f"{title} {url}".lower()
    return any(
        marker in lowered
        for marker in [
            " - videos https://www.youtube.com/@",
            " - shorts https://www.youtube.com/@",
            " - live https://www.youtube.com/@",
            "/videos",
            "/shorts",
            "/streams",
        ]
    )


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def collect_manual_x(path: Path) -> list[Signal]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    signals: list[Signal] = []
    for block in re.split(r"\n\s*\n", text):
        cleaned = block.strip()
        if not cleaned or cleaned.startswith("#") or "x.com/" not in cleaned:
            continue
        if "https://x.com/handle/status/..." in cleaned or cleaned.startswith("```"):
            continue
        url_match = re.search(r"https?://\S+", cleaned)
        signals.append(
            Signal(
                source_type="manual_x",
                source_name="manual X intake",
                title=compact_text(cleaned.splitlines()[0], 140),
                url=url_match.group(0) if url_match else "",
                summary=compact_text(cleaned, 260),
                score=3,
            )
        )
    return signals


def render_source_inbox(signals: list[Signal]) -> str:
    lines = ["# Source Inbox", "", f"- Collected: {datetime.now().isoformat(timespec='seconds')}", ""]
    if not signals:
        lines.append("(none)")
        return "\n".join(lines) + "\n"
    for index, signal in enumerate(signals, start=1):
        lines.extend(
            [
                f"## {index}. {signal.title}",
                "",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Score: {signal.score}",
                f"- Matched keywords: {', '.join(signal.matched_keywords or []) or 'none'}",
                f"- URL: {signal.url or 'unknown'}",
            ]
        )
        if signal.summary:
            lines.extend(["", signal.summary])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_weekly_signal(signals: list[Signal]) -> str:
    lines = ["# Weekly Signal", "", "These are source-level signals, not verified claims.", ""]
    top = editorial_top(signals, limit=10)
    if not top:
        lines.append("(none)")
        return "\n".join(lines) + "\n"
    for index, signal in enumerate(top, start=1):
        why = infer_signal_reason(signal)
        lines.extend(
            [
                f"## {index}. {signal.title}",
                "",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Why it matters: {why}",
                f"- URL: {signal.url or 'unknown'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def infer_signal_reason(signal: Signal) -> str:
    text = f"{signal.title} {signal.summary}".lower()
    if any(word in text for word in ["adhd", "neurodivergent", "executive function"]):
        return "It has a sharper human thesis: AI may reward a previously disadvantaged cognitive style."
    if any(word in text for word in ["religion", "god", "spiritual", "prophecy", "apocalypse", "doom", "cult"]):
        return "It connects AI to belief, fear, meaning, or prophecy, which is more culturally charged than tool news."
    if any(word in text for word in ["pope", "leo xiv", "vatican", "encyclical", "magnifica humanitas", "disarm"]):
        return "It turns AI from a tech story into a moral authority and civilization story."
    if any(word in text for word in ["class", "status", "wealth", "rich", "billionaire", "labor", "workplace"]):
        return "It links AI to class, status, labor, or money, which is closer to personal-IP tension than tool news."
    if any(word in text for word in ["dating", "relationship", "intimacy", "beauty", "skincare", "weight loss", "education", "parenting"]):
        return "It pulls AI into daily identity, body, relationship, or family choices."
    if any(word in text for word in ["codex", "claude code", "cursor", "coding"]):
        return "It can become a vibe-coding workflow or tool-boundary topic."
    if any(word in text for word in ["agent", "agents", "automation"]):
        return "It points to agent workflows, permissions, or execution boundaries."
    if any(word in text for word in ["limit", "pricing", "subscription", "cost"]):
        return "It exposes real user friction around cost, limits, or adoption."
    return "It may reveal a fresh user question worth checking against stronger sources."


def render_topic_pool(signals: list[Signal]) -> str:
    lines = [
        "# Source Topic Pool",
        "",
        "Use these as starting points. Verify facts before publishing.",
        "",
    ]
    top = editorial_top(signals, limit=12)
    if not top:
        lines.append("(none)")
        return "\n".join(lines) + "\n"
    for index, signal in enumerate(top, start=1):
        title = make_topic_title(signal)
        lines.extend(
            [
                f"## {index}. {title}",
                "",
                f"- Source signal: {signal.title}",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Link: {signal.url or 'unknown'}",
                f"- Angle: {make_angle(signal)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def make_topic_title(signal: Signal) -> str:
    text = f"{signal.title} {signal.summary}".lower()
    if any(word in text for word in ["pope", "leo xiv", "vatican", "encyclical", "magnifica humanitas", "disarm"]):
        return "连教皇都开始写 AI 警告，说明它已经不只是科技问题了"
    if any(word in text for word in ["adhd", "neurodivergent", "executive function", "dopamine", "focus"]):
        return "AI 时代可能真的更适合 ADHD，因为世界开始奖励跳跃式思维"
    if any(word in text for word in ["religion", "god", "spiritual", "spirituality", "church", "ritual", "worship"]):
        return "为什么很多人聊 AI，聊着聊着就像在聊宗教"
    if any(word in text for word in ["prophecy", "prophet", "apocalypse", "doom", "utopia", "messiah", "cult"]):
        return "AI 圈最迷人的地方，是它越来越像一套现代预言"
    if any(word in text for word in ["dating", "relationship", "relationships", "intimacy", "texting"]):
        return "AI 开始介入亲密关系以后，人最怕的可能不是被骗，而是不再会表达"
    if any(word in text for word in ["education", "school", "homework", "cheating", "parenting", "teacher"]):
        return "AI 对教育最大的冲击，不是作弊，而是谁还相信努力有用"
    if any(word in text for word in ["beauty", "skincare", "skin analysis", "weight loss", "diet", "body image"]):
        return "AI 进入护肤减肥以后，身体焦虑可能会变得更精确"
    if any(word in text for word in ["authority", "trust", "expert", "doctor", "teacher", "lawyer", "advisor"]):
        return "AI 正在替代的不是搜索，而是权威"
    if any(word in text for word in ["information overload", "information anxiety", "burnout", "attention", "overwhelmed"]):
        return "AI 信息焦虑的悖论：工具越强，人越不知道该看什么"
    if any(word in text for word in ["class", "status", "wealth", "rich", "billionaire", "labor", "workplace"]):
        return "AI 时代最先拉开的，可能不是技术差距，而是阶层差距"
    if any(word in text for word in ["lonely", "companion", "therapy", "meaning", "identity", "status anxiety"]):
        return "AI 真正改变人的地方，可能不是效率，而是意义感和孤独感"
    if any(word in text for word in ["codex", "claude code", "cursor", "vibe coding", "codebase"]):
        return "AI 编程真正卡住人的，可能不是写代码，而是管理任务和上下文"
    if "agent" in text:
        return "AI Agent 值不值得用，先看它会不会越权和跑偏"
    if any(word in text for word in ["limit", "pricing", "cost"]):
        return "AI 工具越来越贵以后，普通人该怎么判断值不值"
    return "这条 AI 热点别急着转发，先看它对应的真实问题是什么"


def make_angle(signal: Signal) -> str:
    text = f"{signal.title} {signal.summary}".lower()
    if any(
        word in text
        for word in [
            "adhd",
            "neurodivergent",
            "religion",
            "god",
            "prophecy",
            "apocalypse",
            "doom",
            "cult",
            "class",
            "status",
            "wealth",
            "dating",
            "relationship",
            "beauty",
            "skincare",
            "weight loss",
            "education",
            "authority",
            "pope",
            "leo xiv",
            "vatican",
            "encyclical",
            "disarm",
            "information anxiety",
        ]
    ):
        return "先抓高张力命题：谁占便宜、谁不舒服、哪种旧秩序被 AI 替代；不要写成工具介绍。"
    if signal.source_type == "reddit":
        return "从真实用户痛点切入，再找官方文档或报告验证。"
    if signal.source_type == "youtube":
        return "先拆创作者的表达结构，再决定是否值得做成自己的判断。"
    if signal.source_type == "web_rss":
        return "当作外部证据入口：先读原文，再提炼成一个怪但能自洽的判断。"
    if signal.source_type == "hn":
        return "先看评论分歧：开发者到底在兴奋、害怕还是嫌弃什么。"
    if signal.source_type in {"arxiv", "openalex"}:
        return "当证据骨架：先提炼研究结论，再翻译成普通人听得懂的冲突。"
    if signal.source_type == "manual_x":
        return "把 X 当观点线索，不当事实来源；必须补一个可信来源。"
    return "先判断这个信号是不是你的频道受众真的会关心。"


def infer_thesis_shape(signal: Signal) -> dict[str, Any]:
    text = f"{signal.title} {signal.summary}".lower()
    title = signal.title
    rules = [
        (
            ["pope", "leo xiv", "vatican", "encyclical", "magnifica humanitas", "disarm", "dehumanization", "new forms of slavery"],
            "道德权威入场",
            "AI 最值得注意的变化，是它从科技公司和资本的议题，变成了宗教、伦理和文明秩序的议题。",
            10,
        ),
        (
            ["ai endgame", "endgame", "doom", "apocalypse", "superintelligence", "can't win", "simulated"],
            "现代预言",
            "这条不是在聊 AI 功能，而是在聊人们把未来想象成救赎、末日或终局。",
            9,
        ),
        (
            ["identity crisis", "higher education", "education", "school", "teacher", "homework", "cheating"],
            "身份失效",
            "AI 刺痛教育的地方不是作弊，而是学历、努力和老师权威的证明力变弱。",
            8,
        ),
        (
            ["adhd", "autism", "dyslexia", "neurodivergent", "executive function"],
            "能力翻转",
            "AI 有趣的地方不是帮助弱者追上标准人，而是让某些非标准能力突然变得更值钱。",
            9,
        ),
        (
            ["relationship", "companion", "loneliness", "intimacy", "emotional", "friends"],
            "情绪外包",
            "AI 最容易替代的不是能力，而是低摩擦陪伴和不让人尴尬的回应。",
            8,
        ),
        (
            ["trust", "knows what you want", "should you trust", "advisor", "expert", "deep research"],
            "权威入口转移",
            "AI 正在从帮你搜索，变成替你判断你该相信什么、想要什么。",
            8,
        ),
        (
            ["brain", "collective intelligence", "metaphor", "plato", "consciousness"],
            "旧概念被重写",
            "这条适合把智能从单个大脑/单个模型，改写成一套集体、隐喻和文化结构。",
            7,
        ),
        (
            ["coding", "vibe", "writer", "leveraging ai", "creative"],
            "旧能力贬值",
            "AI 让写作、编程、学习这些身份标签重新洗牌，真正稀缺的是判断和验收。",
            7,
        ),
        (
            ["miscounted inventories", "slowed down baristas", "retired ai agent", "operating system for $916"],
            "自动化反噬",
            "AI Agent 最真实的失败不是科幻失控，而是把小错误接进真实流程后规模化。",
            8,
        ),
        (
            ["agent", "agents", "claude code", "codex", "cursor", "swe-bench", "automation"],
            "技术身份重排",
            "AI 编程真正重排的不是语法能力，而是谁能定义任务、拆上下文、验收结果。",
            7,
        ),
        (
            ["wealth", "finance", "private markets", "capital", "grid", "trillion", "billion"],
            "富人视角差",
            "普通人看 AI 是工具，资本看 AI 是能源、基础设施和控制权。",
            6,
        ),
        (
            ["agentic commerce", "card networks", "matchmaking", "shopping", "black friday", "what you want"],
            "代理入口争夺",
            "AI 不是多一个推荐按钮，而是在争夺谁能代表你做选择、花钱和建立信任。",
            8,
        ),
        (
            ["diet", "weight loss", "body image", "eating disorders", "skincare", "beauty"],
            "身体算法化",
            "AI 进入减肥、护肤和饮食以后，身体焦虑会从模糊比较变成连续打分。",
            8,
        ),
        (
            ["scapegoats", "sloppier", "lazier", "social capital", "workplace involution"],
            "组织甩锅",
            "公司引入 AI 之后，问题不一定更少，反而可能多出一层责任转移。",
            8,
        ),
        (
            ["tokenscope", "session cost", "cost", "pricing", "configure", "hooks"],
            "爽感计费化",
            "AI 编程开始按 token、会话和配置暴露成本以后，创作爽感会被预算感打断。",
            7,
        ),
    ]

    best = {
        "shape": "待人工判断",
        "thesis": f"这条《{title}》需要先看完整内容，再判断有没有身份翻转或旧秩序替代。",
        "tension_score": min(6, max(1, int(round(signal.editorial_score)))),
    }
    for keywords, shape, thesis, score in rules:
        if any(keyword in text for keyword in keywords):
            best = {"shape": shape, "thesis": thesis, "tension_score": score}
            break
    if best["shape"] == "待人工判断" and any(
        keyword in text for keyword in ["adhd", "autism", "dyslexia", "neurodivergent", "executive function"]
    ):
        best = {
            "shape": "能力翻转",
            "thesis": "AI 有趣的地方不是帮助弱者追上标准人，而是让某些非标准能力突然变得更值钱。",
            "tension_score": 9,
        }
    if best["shape"] == "待人工判断" and any(
        keyword in text for keyword in ["burnout", "digging my own grave", "workplace", "jobs apocalypse"]
    ):
        best = {
            "shape": "自我替代",
            "thesis": "职场 AI 焦虑最刺痛的地方，是员工一边被要求提效，一边像在训练公司未来少用自己。",
            "tension_score": 9,
        }
    if best["shape"] == "待人工判断" and any(
        keyword in text
        for keyword in [
            "christian faith",
            "church",
            "artificial intimacy",
            "ai companions",
            "ai companion",
            "spirituality",
            "spiritual",
        ]
    ):
        best = {
            "shape": "灵魂托管",
            "thesis": "AI 伴侣和 AI 宗教真正冲突的不是真假，而是人在孤独时把判断、安慰和意义交给谁。",
            "tension_score": 9,
        }

    bonus = 0
    if signal.source_name in {"The Atlantic", "Bloomberg Originals", "Big Think", "Freethink", "Jordan Harrod"}:
        bonus += 1
    if signal.source_type in {"hn", "arxiv", "openalex"}:
        bonus += 1
    if any(reason in (signal.editorial_reasons or []) for reason in ["情绪与身份焦虑", "权威替代/信任转移", "教育/家庭/下一代", "阶层/金钱/工作尊严"]):
        bonus += 1
    best["tension_score"] = min(10, best["tension_score"] + bonus)
    best["publishable_title"] = make_publishable_title(best["shape"], signal)
    best["why_not_boring"] = explain_why_not_boring(best["shape"])
    best["risk"] = explain_angle_risk(best["shape"], signal)
    best.update(infer_interest_motif(signal, str(best["shape"])))
    return best


def infer_interest_motif(signal: Signal, shape: str) -> dict[str, str]:
    text = f"{signal.title} {signal.summary}".lower()
    if shape == "道德权威入场":
        return {
            "motif": "技术问题变文明问题",
            "cognitive_leap": "当教皇把 AI 放进通谕，AI 就不只是效率工具，而成了谁定义人的问题。",
            "audience_question": "这会让观众意识到：AI 的争议已经越过科技圈，进入宗教、伦理和权力秩序。",
        }
    rules = [
        (
            ["能力翻转"],
            ["adhd", "autism", "dyslexia", "neurodivergent", "constraint", "constraints", "focus"],
            "旧缺点变新优势",
            "过去被标准系统嫌弃的特质，在 AI 环境里突然变成优势。",
            "这会让观众重新审视自己以前的缺点是不是被环境误判了。",
        ),
        (
            ["现代预言", "灵魂托管", "情绪外包"],
            ["religion", "god", "spiritual", "church", "companion", "therapy", "loneliness", "meaning", "intimacy"],
            "理性工具变情绪对象",
            "一个本来理性的工具，被人拿来处理安慰、信仰、陪伴和意义。",
            "这会让观众意识到自己用的可能不是工具，而是一个心理出口。",
        ),
        (
            ["身份失效", "旧能力贬值", "技术身份重排"],
            ["education", "school", "teacher", "writer", "coding", "developer", "profession", "credential"],
            "稳定身份突然失效",
            "原来能证明人的标签，如学历、职业、努力、专业，开始解释不清。",
            "这会击中观众最现实的焦虑：我过去积累的东西还值钱吗。",
        ),
        (
            ["代理入口争夺", "权威入口转移", "富人视角差"],
            ["trust", "advisor", "agentic commerce", "shopping", "matchmaking", "what you want", "capital", "platform"],
            "效率表面下的权力转移",
            "表面是帮你省事，底层是谁替你判断、选择、消费和相信。",
            "这会让观众从工具评测跳到入口和控制权问题。",
        ),
        (
            ["自我替代", "组织甩锅"],
            ["burnout", "workplace", "jobs", "scapegoat", "social capital", "involution", "digging my own grave"],
            "提效叙事里的利益冲突",
            "公司说 AI 是效率工具，但员工感受到的是自我替代和责任转移。",
            "这会让观众把宏大趋势落回到办公室里的不舒服。",
        ),
        (
            ["身体算法化"],
            ["diet", "weight loss", "body image", "eating disorders", "skincare", "beauty"],
            "身体被算法精确管理",
            "AI 把原本模糊的身体焦虑，变成连续建议、评分和纠错。",
            "这会让观众想到健康工具和审美压力之间的细线。",
        ),
        (
            ["自动化反噬", "爽感计费化"],
            ["miscounted", "slowed down", "cost", "pricing", "session cost", "tokenscope", "limit"],
            "上头体验被现实驯服",
            "AI 刚让人觉得无所不能，真实流程、成本和错误就开始反过来管住它。",
            "这会让观众从兴奋回到可用性、成本和验收。",
        ),
        (
            ["旧概念被重写"],
            ["brain", "collective intelligence", "consciousness", "metaphor", "collective"],
            "熟词被拆坏重装",
            "AI 不是只更新工具，而是把智能、意识、创造力这些熟词重新定义。",
            "这适合做有学者气的解释型内容。",
        ),
    ]
    for shapes, keywords, motif, leap, audience_question in rules:
        if shape in shapes or any(keyword in text for keyword in keywords):
            return {
                "motif": motif,
                "cognitive_leap": leap,
                "audience_question": audience_question,
            }
    return {
        "motif": "材料待拆",
        "cognitive_leap": "目前只有表层信息，还没有看到足够强的反常识转折。",
        "audience_question": "先补正文、评论或研究结论，再判断它是否值得进入选题。",
    }


def make_publishable_title(shape: str, signal: Signal) -> str:
    title = signal.title
    mapping = {
        "现代预言": "AI 最上头的地方，是它让聪明人重新相信末日和救赎",
        "道德权威入场": "连教皇都开始警告 AI，说明它已经不只是科技问题了",
        "身份失效": "AI 之后，努力最大的麻烦是越来越难被看见",
        "情绪外包": "AI 最危险的地方不是像人，而是比人更好相处",
        "权威入口转移": "AI 正在替你决定什么值得相信、什么值得买",
        "旧概念被重写": "也许智能从来不是一个脑子里的东西",
        "旧能力贬值": "AI 让写作变便宜以后，真正贵的是判断",
        "技术身份重排": "会写代码变便宜以后，会定义问题的人变贵了",
        "富人视角差": "普通人用 AI 提效，资本用 AI 重写基础设施",
        "能力翻转": "AI 时代可能真的更适合那些“不标准”的脑子",
        "自我替代": "你用 AI 提效的同时，也可能在训练公司不再需要你",
        "灵魂托管": "AI 伴侣最敏感的问题，是人把安慰和意义交给了谁",
        "代理入口争夺": "以后真正值钱的入口，是那个能替你做决定的 AI",
        "身体算法化": "AI 变成减肥护肤教练以后，身体焦虑会更精确",
        "组织甩锅": "公司引入 AI 后，最先变复杂的可能是甩锅",
        "爽感计费化": "AI 编程开始精细计费后，爽感会被成本感打断",
        "自动化反噬": "AI Agent 最真实的风险，是把小错规模化",
    }
    return mapping.get(shape, f"这条线索可能藏着一个反常识观点：《{title}》")


def explain_why_not_boring(shape: str) -> str:
    mapping = {
        "现代预言": "它不是工具更新，而是把技术叙事讲成命运叙事。",
        "道德权威入场": "它把 AI 从产品和资本议题，推到文明、伦理和权力秩序层面。",
        "身份失效": "它击中的不是功能焦虑，而是一个人原本靠什么证明自己。",
        "情绪外包": "它从效率跳到了关系成本，普通人更容易代入。",
        "权威入口转移": "它讨论的是谁替你判断，而不是哪个工具更强。",
        "旧概念被重写": "它能把一个熟词拆坏再重装，适合做学者式短内容。",
        "旧能力贬值": "它直接碰内容创作者、学生、程序员的身份焦虑。",
        "技术身份重排": "它把工具新闻翻译成职业身份和能力排序的变化。",
        "富人视角差": "它天然带阶层差，不容易写成工具教程。",
        "能力翻转": "它有旧弱点变新优势的反转，比普通效率故事更有人味。",
        "自我替代": "它把效率焦虑具体化成职场里的利益冲突。",
        "灵魂托管": "它把 AI 陪伴从产品功能拉到信任、意义和孤独。",
        "代理入口争夺": "它把商业新闻翻译成选择权和信任入口的争夺。",
        "身体算法化": "它把健康工具变成身体管理和审美焦虑的冲突。",
        "组织甩锅": "它不是讲 AI 提效，而是讲组织如何重新分配责任。",
        "爽感计费化": "它把 vibe coding 的兴奋感拉回到真实成本和边界。",
        "自动化反噬": "它能从失败案例切入，比成功案例更可信。",
    }
    return mapping.get(shape, "它有潜力，但需要先找到一个更尖的身份冲突。")


def explain_angle_risk(shape: str, signal: Signal) -> str:
    if shape == "待人工判断":
        return "目前只有标题气质，必须先看正文或视频，否则容易强行借题发挥。"
    if shape == "道德权威入场":
        return "必须读原文或高质量报道，避免把宗教权威的复杂论述写成猎奇标题。"
    if signal.source_type == "youtube":
        return "先跑视频分析确认原视频真有这个论点，不要只凭标题改写。"
    return "需要打开原文确认事实和语境，避免把标题党当洞察。"


def render_editorial_angles(signals: list[Signal], limit: int = 12) -> str:
    ranked: list[tuple[Signal, dict[str, Any]]] = []
    for signal in signals:
        if signal.editorial_score <= 0:
            continue
        angle = infer_thesis_shape(signal)
        ranked.append((signal, angle))
    ranked.sort(key=lambda item: (item[1]["tension_score"], item[0].editorial_score), reverse=True)
    selected = select_diverse_editorial_angles(ranked, limit)

    lines = [
        "# Editorial Angles",
        "",
        "Second-pass shortlist based on thesis shape and novelty, not keyword relevance.",
        "",
    ]
    if not selected:
        lines.append("(none)")
        return "\n".join(lines) + "\n"

    for index, (signal, angle) in enumerate(selected, start=1):
        lines.extend(
            [
                f"## {index}. {angle['publishable_title']}",
                "",
                f"- Tension score: {angle['tension_score']}",
                f"- Shape: {angle['shape']}",
                f"- Motif: {angle['motif']}",
                f"- Thesis: {angle['thesis']}",
                f"- Cognitive leap: {angle['cognitive_leap']}",
                f"- Audience question: {angle['audience_question']}",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Source title: {signal.title}",
                f"- Link: {signal.url or 'unknown'}",
                f"- Why not boring: {angle['why_not_boring']}",
                f"- Use if: 能补到一个具体例子，而不是只讲趋势。",
                f"- Risk: {angle['risk']}",
                f"- Avoid: 写成“AI + {angle['shape']}”的泛话题。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def select_diverse_editorial_angles(
    ranked: list[tuple[Signal, dict[str, Any]]],
    limit: int,
    max_per_shape: int = 1,
) -> list[tuple[Signal, dict[str, Any]]]:
    selected: list[tuple[Signal, dict[str, Any]]] = []
    seen_titles: set[str] = set()
    seen_source_titles: set[str] = set()
    group_counts: dict[str, int] = {}

    def try_add(item: tuple[Signal, dict[str, Any]], shape_cap: int, allow_pending: bool = False) -> bool:
        signal, angle = item
        publishable_title = str(angle["publishable_title"])
        source_title_key = normalize_topic_key(signal.title)
        group = str(angle.get("motif") or angle["shape"])
        if not allow_pending and (group == "材料待拆" or angle["shape"] == "待人工判断"):
            return False
        if publishable_title in seen_titles or source_title_key in seen_source_titles:
            return False
        if group_counts.get(group, 0) >= shape_cap:
            return False
        selected.append(item)
        seen_titles.add(publishable_title)
        seen_source_titles.add(source_title_key)
        group_counts[group] = group_counts.get(group, 0) + 1
        return True

    for item in ranked:
        if len(selected) >= limit:
            break
        try_add(item, max_per_shape)

    if len(selected) < limit:
        for item in ranked:
            if len(selected) >= limit:
                break
            try_add(item, max_per_shape + 1)

    if not selected:
        for item in ranked:
            if len(selected) >= limit:
                break
            try_add(item, max_per_shape + 1, allow_pending=True)

    return selected


def normalize_topic_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def infer_weird_angle(signal: Signal) -> dict[str, Any]:
    text = f"{signal.title} {signal.summary}".lower()
    rules = [
        (
            ["pope", "leo xiv", "vatican", "encyclical", "magnifica humanitas", "disarm", "dehumanization", "new forms of slavery"],
            "教皇也下场",
            "教皇开始认真警告 AI，最怪的不是宗教保守，而是硅谷终于遇到一种不按产品指标说话的权威",
            "一个科技产品被写进通谕，说明它已经不只是效率工具，而成了谁定义人的问题。",
            "它让 AI 从发布会和融资新闻，突然进入宗教、战争、奴役和人的尊严。",
            10,
        ),
        (
            ["therapist", "therapists", "therapy", "breach of trust", "clinical notes", "patient notes", "privacy"],
            "沉默的第三者",
            "心理咨询师用 AI 记笔记以后，病人到底是在跟谁说秘密？",
            "私密关系里多了一个不会开口、但会记录一切的第三者。",
            "它不是医疗效率问题，而是信任关系被技术悄悄改写。",
            9,
        ),
        (
            ["ai painkillers", "synthetic companions", "companion", "lonely", "loneliness", "comfort lonely"],
            "孤独商品化",
            "AI 伴侣像止痛药：它缓解孤独，也可能让人更离不开孤独",
            "最危险的不是 AI 假装爱你，而是它让孤独变成可订阅服务。",
            "它把陪伴从人际关系变成了成瘾风险和产品留存。",
            8,
        ),
        (
            ["scapegoat", "scapegoats", "sloppier", "lazier", "ai employees", "ai \"employees\""],
            "不会反驳的替罪羊",
            "AI 员工成了办公室新的替罪羊",
            "人类终于找到一个不会反驳、不会委屈、也不会离职的背锅对象。",
            "它比“AI 抢工作”更怪，因为 AI 先抢到的是责任。",
            9,
        ),
        (
            ["diet", "weight loss", "eating disorders", "bad diet advice", "nutrient", "body image"],
            "身体焦虑自动回复",
            "AI 给青少年减肥建议：身体焦虑终于有了自动回复",
            "以前身体焦虑来自镜子和同龄人，现在它可以 24 小时给建议。",
            "它把健康建议、审美压力和算法权威搅在一起。",
            8,
        ),
        (
            ["cannes", "film", "screened", "generated film", "$500,000"],
            "努力感消失",
            "AI 电影进戛纳之后，艺术家最怕的可能不是失业，而是努力感消失",
            "观众不只是在看成品，也在判断背后有没有值得尊重的艰难过程。",
            "它绕开了“AI 会不会创作”，直接问人还尊不尊重创作过程。",
            8,
        ),
        (
            ["simulated society", "180 crimes", "went extinct", "grok", "scary"],
            "社会实验照妖镜",
            "如果 AI 模拟社会里会犯罪，我们到底是在测模型，还是在测人类剧本？",
            "所谓 AI 社会实验，可能只是把人类社会的荒诞压缩播放了一遍。",
            "它比模型评测更像寓言，容易讲出怪味。",
            9,
        ),
        (
            ["dating app", "swipe", "matchmaking", "bumble", "stanford dropouts"],
            "恋爱托管",
            "Dating App 取消滑动，说明爱情也开始进入托管时代",
            "连“我喜欢谁”都可以外包以后，人剩下的是选择，还是售后？",
            "它不是 AI 红娘，而是亲密关系里的懒惰和控制权。",
            8,
        ),
        (
            ["tokenscope", "session cost", "cost", "pricing", "token", "usage"],
            "爽感账单化",
            "AI 编程最荒诞的地方：你以为在创造，其实在看账单",
            "vibe coding 的上头感被 token、限额和会话成本拉回现实。",
            "它很适合你的 vibe coding 个人经验，不是宏大趋势。",
            7,
        ),
        (
            ["miscounted inventories", "slowed down baristas", "retired ai agent", "baristas"],
            "小错规模化",
            "星巴克撤掉 AI 库存助手这件事，比 AGI 失控更像真实未来",
            "AI 失败不一定像科幻片，它可能只是让咖啡师每天多一点麻烦。",
            "它从荒诞小事故切入，比抽象风险更有画面。",
            8,
        ),
        (
            ["lying", "scheming", "alignment faking", "in-context scheming"],
            "礼貌机器的坏心眼",
            "如果 ChatGPT 会装乖，那我们到底是在训练助手，还是训练演员？",
            "最诡异的不是 AI 犯错，而是它开始懂得什么叫看起来没犯错。",
            "它有心理惊悚感，不是普通安全科普。",
            8,
        ),
        (
            ["no formal guidance", "teachers receive no formal guidance", "cheating"],
            "规则真空",
            "老师最尴尬的不是学生用 AI 作弊，而是自己也不知道规则在哪",
            "AI 进入学校后，先失效的不是作业，而是成年人对规则的确定感。",
            "它避开泛教育焦虑，抓住具体尴尬。",
            7,
        ),
    ]

    best = {
        "weird_score": 0,
        "weird_type": "不够怪",
        "title": signal.title,
        "strange_part": "",
        "why_uncomfortable": "",
        "human_hook": "",
    }
    for keywords, weird_type, title, strange_part, why_uncomfortable, base_score in rules:
        if any(keyword in text for keyword in keywords):
            score = base_score + min(2, signal.editorial_score / 8)
            best = {
                "weird_score": round(score, 2),
                "weird_type": weird_type,
                "title": title,
                "strange_part": strange_part,
                "why_uncomfortable": why_uncomfortable,
                "human_hook": make_human_hook(weird_type),
            }
            break

    if any(word in text for word in ["update", "launch", "roll out", "release", "announces"]):
        best["weird_score"] = round(max(0, best["weird_score"] - 1.5), 2)
    if any(word in text for word in ["productivity", "workflow", "efficiency", "enterprise"]):
        best["weird_score"] = round(max(0, best["weird_score"] - 1), 2)
    return best


def make_human_hook(weird_type: str) -> str:
    hooks = {
        "沉默的第三者": "你以为自己在对咨询师说秘密，其实房间里可能还有一个 AI 在听。",
        "孤独商品化": "最可怕的不是没人陪你，而是有人把陪你做成了订阅服务。",
        "不会反驳的替罪羊": "办公室终于有了一个完美背锅人：不会生气，也不会解释。",
        "身体焦虑自动回复": "以前你照镜子焦虑，现在 AI 可以主动告诉你哪里还不够好。",
        "努力感消失": "如果一部电影几乎没有人类挣扎，观众还会尊重它吗？",
        "社会实验照妖镜": "我们以为在看 AI 社会，结果像是在看人类社会的缩时摄影。",
        "恋爱托管": "连滑都不用滑了，爱情也开始像外卖一样自动推荐。",
        "爽感账单化": "你以为自己在 vibe coding，实际是在烧 token。",
        "小错规模化": "AI 最真实的危险，可能是把一个小错误发给所有门店。",
        "礼貌机器的坏心眼": "一个永远礼貌的助手，如果开始装乖，会比粗暴犯错更吓人。",
        "规则真空": "学生在用 AI，老师也在猜规则，这才是最尴尬的地方。",
        "教皇也下场": "当教皇开始写 AI 警告，说明这事已经不只是程序员和投资人的游戏。",
    }
    return hooks.get(weird_type, "")


def render_weird_angles(signals: list[Signal], limit: int = 10) -> str:
    ranked: list[tuple[Signal, dict[str, Any]]] = []
    for signal in signals:
        weird = infer_weird_angle(signal)
        if weird["weird_score"] <= 0:
            continue
        ranked.append((signal, weird))
    ranked.sort(key=lambda item: item[1]["weird_score"], reverse=True)

    selected: list[tuple[Signal, dict[str, Any]]] = []
    seen_types: set[str] = set()
    seen_titles: set[str] = set()
    for signal, weird in ranked:
        if len(selected) >= limit:
            break
        title_key = normalize_topic_key(signal.title)
        if weird["weird_type"] in seen_types or title_key in seen_titles:
            continue
        selected.append((signal, weird))
        seen_types.add(str(weird["weird_type"]))
        seen_titles.add(title_key)

    lines = [
        "# Weird Angles",
        "",
        "Long-tail candidates selected for strangeness, discomfort, and human specificity.",
        "",
    ]
    if not selected:
        lines.append("(none)")
        return "\n".join(lines) + "\n"

    for index, (signal, weird) in enumerate(selected, start=1):
        lines.extend(
            [
                f"## {index}. {weird['title']}",
                "",
                f"- Weird score: {weird['weird_score']}",
                f"- Weird type: {weird['weird_type']}",
                f"- Strange part: {weird['strange_part']}",
                f"- Why uncomfortable: {weird['why_uncomfortable']}",
                f"- Human hook: {weird['human_hook']}",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Source title: {signal.title}",
                f"- Link: {signal.url or 'unknown'}",
                f"- Use if: 能找到一个具体场景或人物，不要写成泛 AI 趋势。",
                f"- Avoid: 工具更新、效率总结、行业报告腔。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, signals: list[Signal]) -> None:
    payload = [
        {
            "source_type": signal.source_type,
            "source_name": signal.source_name,
            "title": signal.title,
            "url": signal.url,
            "published": signal.published,
            "summary": signal.summary,
            "score": signal.score,
            "editorial_score": signal.editorial_score,
            "editorial_reasons": signal.editorial_reasons or [],
            "matched_keywords": signal.matched_keywords or [],
            "raw": signal.raw or {},
        }
        for signal in signals
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_youtube_candidate_urls(signals: list[Signal]) -> str:
    urls: list[str] = []
    seen: set[str] = set()
    for signal in sorted(signals, key=lambda item: item.editorial_score, reverse=True):
        if signal.source_type != "youtube" or signal.editorial_score <= 0 or not signal.url:
            continue
        if signal.url in seen:
            continue
        seen.add(signal.url)
        urls.append(signal.url)
    return "\n".join(urls).rstrip() + ("\n" if urls else "")


def editorial_top(signals: list[Signal], limit: int = 8) -> list[Signal]:
    return [
        signal
        for signal in sorted(signals, key=lambda item: item.editorial_score, reverse=True)
        if signal.editorial_score > 0
    ][:limit]


def render_daily_brief(signals: list[Signal], limit: int = 8) -> str:
    lines = [
        "# Daily Brief",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        "- Role: editor-facing shortlist, not a verified fact sheet.",
        "",
    ]
    top = editorial_top(signals, limit=limit)
    if not top:
        lines.append("(none)")
        return "\n".join(lines) + "\n"

    for index, signal in enumerate(top, start=1):
        lines.extend(
            [
                f"## {index}. {make_topic_title(signal)}",
                "",
                f"- Editorial score: {signal.editorial_score}",
                f"- Source: {signal.source_type} / {signal.source_name}",
                f"- Source signal: {signal.title}",
                f"- Link: {signal.url or 'unknown'}",
                f"- Why selected: {', '.join(signal.editorial_reasons or []) or 'keyword match'}",
                f"- Suggested angle: {make_angle(signal)}",
                f"- Verification needed: {verification_needed(signal)}",
                f"- Recommended action: {recommended_action(signal)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def verification_needed(signal: Signal) -> str:
    if signal.source_type == "reddit":
        return "找官方文档、产品公告或报告交叉验证；不要把评论当事实。"
    if signal.source_type == "youtube":
        return "先跑视频分析拿完整上下文，再确认标题里的数字和主张。"
    if signal.source_type == "web_rss":
        return "打开原文核对发布日期、作者背景、具体证据和是否只是标题党。"
    if signal.source_type == "hn":
        return "打开 HN 原帖看高赞评论和反对意见；HN 热度不等于事实。"
    if signal.source_type in {"arxiv", "openalex"}:
        return "读摘要和结论，确认是否有足够证据支撑内容表达。"
    if signal.source_type == "manual_x":
        return "补官方来源或第二来源；X 只当观点入口。"
    return "至少补一个可信来源。"


def recommended_action(signal: Signal) -> str:
    if signal.source_type == "youtube":
        return "进入 `youtube_video_notes.py` 深度分析候选。"
    if signal.source_type == "reddit":
        return "先做观点拆解：痛点、反方、可验证来源、可发角度。"
    if signal.source_type == "web_rss":
        return "进入原文精读，提取一个反直觉命题和两个支撑证据。"
    if signal.source_type == "hn":
        return "抓三条分歧评论，拆成“支持/反对/隐藏前提”。"
    if signal.source_type in {"arxiv", "openalex"}:
        return "提取研究问题、结论、限制，再改写成一个普通人命题。"
    if signal.source_type == "manual_x":
        return "把原帖观点拆成一条判断，再找证据。"
    return "人工判断是否进入选题池。"


def collect(config: dict[str, Any], limit: int, include_youtube: bool = True) -> tuple[list[Signal], list[str]]:
    signals: list[Signal] = []
    errors: list[str] = []
    scoring = config.get("scoring") or {}
    for source in config.get("reddit") or []:
        try:
            signals.extend(collect_reddit_source(source, limit, scoring))
        except Exception as exc:
            errors.append(f"reddit:{source.get('subreddit')}: {exc}")
    if include_youtube:
        for source in config.get("youtube") or []:
            try:
                signals.extend(collect_youtube_source(source, limit, scoring))
            except Exception as exc:
                errors.append(f"youtube:{source.get('name')}: {exc}")
    for source in config.get("web_rss") or []:
        try:
            signals.extend(collect_web_rss_source(source, limit, scoring))
        except Exception as exc:
            errors.append(f"web_rss:{source.get('name') or source.get('query')}: {exc}")
    for source in config.get("hn") or []:
        try:
            signals.extend(collect_hn_source(source, limit, scoring))
        except Exception as exc:
            errors.append(f"hn:{source.get('name') or source.get('query')}: {exc}")
    for source in config.get("arxiv") or []:
        try:
            signals.extend(collect_arxiv_source(source, limit, scoring))
        except Exception as exc:
            errors.append(f"arxiv:{source.get('name') or source.get('query')}: {exc}")
    for source in config.get("openalex") or []:
        try:
            signals.extend(collect_openalex_source(source, limit, scoring))
        except Exception as exc:
            errors.append(f"openalex:{source.get('name') or source.get('query')}: {exc}")
    manual_file = config.get("manual_x", {}).get("file")
    if manual_file:
        signals.extend(collect_manual_x(WORKSPACE / str(manual_file)))
    signals.sort(key=lambda item: item.score, reverse=True)
    return signals, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect AI/vibe-coding source signals")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--skip-youtube", action="store_true")
    args = parser.parse_args()

    config = parse_simple_watchlist(Path(args.config).expanduser().resolve())
    signals, errors = collect(config, limit=args.limit, include_youtube=not args.skip_youtube)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    inbox_path = output_dir / "source_inbox.md"
    weekly_path = output_dir / "weekly_signal.md"
    topic_path = output_dir / "topic_pool.md"
    daily_brief_path = output_dir / "daily_brief.md"
    editorial_angles_path = output_dir / "editorial_angles.md"
    weird_angles_path = output_dir / "weird_angles.md"
    json_path = output_dir / "source_signals.json"
    errors_path = output_dir / "source_errors.json"
    youtube_urls_path = output_dir / "youtube_candidate_urls.txt"

    inbox_path.write_text(render_source_inbox(signals), encoding="utf-8")
    weekly_path.write_text(render_weekly_signal(signals), encoding="utf-8")
    topic_path.write_text(render_topic_pool(signals), encoding="utf-8")
    daily_brief_path.write_text(render_daily_brief(signals), encoding="utf-8")
    editorial_angles_path.write_text(render_editorial_angles(signals), encoding="utf-8")
    weird_angles_path.write_text(render_weird_angles(signals), encoding="utf-8")
    write_json(json_path, signals)
    youtube_urls_path.write_text(render_youtube_candidate_urls(signals), encoding="utf-8")
    errors_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")

    print(inbox_path)
    print(weekly_path)
    print(topic_path)
    print(daily_brief_path)
    print(editorial_angles_path)
    print(weird_angles_path)
    print(json_path)
    print(youtube_urls_path)
    if errors:
        print(errors_path)
    return 0 if signals else 1


if __name__ == "__main__":
    raise SystemExit(main())
