#!/usr/bin/env python3
"""Convert source files/URLs into Markdown source packs for writing workflows."""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / ".cache" / "source-ingest"


@dataclass
class SourceDoc:
    source: str
    title: str
    text: str
    converter: str


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def slugify(value: str, fallback: str = "source") -> str:
    value = value.strip().lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    if not value:
        value = fallback
    return value[:80]


def stable_suffix(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def read_source_list(path: Path) -> list[str]:
    sources: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            sources.append(stripped)
    return sources


def strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "\n", raw_html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|h[1-6]|section|article)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fallback_convert(source: str) -> SourceDoc:
    if is_url(source):
        response = requests.get(source, timeout=25, headers={"User-Agent": "Codex source-ingest"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            text = strip_html(response.text)
        else:
            text = response.text
        title = source
        match = re.search(r"(?is)<title[^>]*>(.*?)</title>", response.text)
        if match:
            title = html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
        return SourceDoc(source=source, title=title, text=text, converter="fallback-requests")

    path = Path(source).expanduser()
    text = path.read_text(encoding="utf-8", errors="replace")
    return SourceDoc(source=str(path), title=path.name, text=text, converter="fallback-text")


def markitdown_convert(source: str) -> SourceDoc:
    try:
        from markitdown import MarkItDown
    except Exception:
        return fallback_convert(source)

    converter = MarkItDown()
    result = converter.convert(source)
    text = getattr(result, "text_content", "") or ""
    title = getattr(result, "title", None) or source
    if not text.strip():
        return fallback_convert(source)
    return SourceDoc(source=source, title=title, text=text, converter="markitdown")


def write_source_pack(docs: list[SourceDoc], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths: list[Path] = []
    for index, doc in enumerate(docs, start=1):
        slug = slugify(doc.title, fallback=f"source-{index}")
        filename = f"{index:02d}_{slug}_{stable_suffix(doc.source)}.md"
        path = out_dir / filename
        path.write_text(
            "\n".join(
                [
                    "---",
                    f"source: {doc.source}",
                    f"title: {doc.title}",
                    f"converter: {doc.converter}",
                    f"ingested_at: {datetime.now().isoformat(timespec='seconds')}",
                    "---",
                    "",
                    f"# {doc.title}",
                    "",
                    doc.text.strip(),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        source_paths.append(path)

    index_path = out_dir / "index.md"
    index_path.write_text(
        "# Source Pack Index\n\n"
        + "\n".join(f"- [{path.name}]({path.name})" for path in source_paths)
        + "\n",
        encoding="utf-8",
    )

    combined_path = out_dir / "source_pack.md"
    combined = ["# Combined Source Pack", ""]
    for path in source_paths:
        combined.append(f"<!-- source-file: {path.name} -->")
        combined.append(path.read_text(encoding="utf-8"))
        combined.append("")
    combined_path.write_text("\n".join(combined), encoding="utf-8")
    return {"index": index_path, "combined": combined_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", help="Local files or URLs to convert")
    parser.add_argument("--file", type=Path, help="Text file containing one source per line")
    parser.add_argument("--name", help="Output pack name under .cache/source-ingest")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-markitdown", action="store_true", help="Use simple fallback converter")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = list(args.sources)
    if args.file:
        sources.extend(read_source_list(args.file))
    if not sources:
        print("FAIL: pass at least one source path or URL", file=sys.stderr)
        return 2

    pack_name = args.name or datetime.now().strftime("source_pack_%Y%m%d_%H%M%S")
    out_dir = args.out_dir / slugify(pack_name, fallback="source-pack")

    docs: list[SourceDoc] = []
    for source in sources:
        doc = fallback_convert(source) if args.no_markitdown else markitdown_convert(source)
        docs.append(doc)

    outputs = write_source_pack(docs, out_dir)
    print(f"OK: wrote {len(docs)} source(s)")
    print(f"index: {outputs['index']}")
    print(f"combined: {outputs['combined']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
