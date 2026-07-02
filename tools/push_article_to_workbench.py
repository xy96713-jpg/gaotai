#!/usr/bin/env python3
"""Push a local article draft into the writing workbench document store."""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from pathlib import Path


DEFAULT_SERVER = "http://127.0.0.1:8766"
DEFAULT_DOCUMENT_ID = "real_loop_ai_writing_workbench_kimi"


def split_title_and_body(text: str, fallback_title: str, *, title_is_explicit: bool) -> tuple[str, str]:
    stripped = text.strip()
    lines = stripped.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines[0].removeprefix("# ").strip() or fallback_title
        return title, "\n".join(lines[1:]).strip()
    if title_is_explicit:
        return fallback_title, stripped
    first_block = re.split(r"\n\s*\n", stripped, maxsplit=1)[0].strip()
    if first_block and len(first_block) <= 60:
        return first_block, stripped
    return fallback_title, stripped


def markdownish_to_html(text: str) -> str:
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", text.strip()) if block.strip()]
    rendered: list[str] = []
    for index, block in enumerate(blocks):
        escaped = html.escape(block).replace("\n", "<br>")
        if index == 0 and len(block) <= 80:
            rendered.append(f"<h2>{escaped}</h2>")
        else:
            rendered.append(f"<p>{escaped}</p>")
    return "\n".join(rendered)


def post_document(server: str, payload: dict[str, str]) -> dict[str, object]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        server.rstrip("/") + "/api/document",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="Markdown or plain text draft to push.")
    parser.add_argument("--title", default="", help="Title to use when the draft has no Markdown # title line.")
    parser.add_argument("--document-id", default=DEFAULT_DOCUMENT_ID, help="Workbench document id.")
    parser.add_argument("--document-type", choices=("formal", "experiment"), default="formal", help="Document lane in the workbench.")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Workbench server base URL.")
    args = parser.parse_args()

    text = args.draft.read_text(encoding="utf-8")
    fallback_title = args.title.strip() or "未命名稿件"
    title, body = split_title_and_body(text, fallback_title, title_is_explicit=bool(args.title.strip()))
    content_text = body if body.startswith(title) else f"{title}\n\n{body}".strip()
    payload = {
        "documentId": args.document_id,
        "title": title,
        "contentHtml": markdownish_to_html(content_text),
        "contentText": content_text,
        "documentType": args.document_type,
    }
    result = post_document(args.server, payload)
    url = f"{args.server.rstrip()}/v2/?documentId={args.document_id}"
    print(json.dumps({"ok": True, "url": url, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
