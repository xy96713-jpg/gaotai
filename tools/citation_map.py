#!/usr/bin/env python3
"""Build a heuristic citation/source-support map for a Chinese article draft."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STOPWORDS = {
    "一个",
    "这个",
    "不是",
    "没有",
    "可以",
    "如果",
    "因为",
    "但是",
    "还是",
    "自己",
    "什么",
    "就是",
    "人工智能",
}


@dataclass(frozen=True)
class SourceChunk:
    anchor: str
    text: str
    keywords: set[str]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def chinese_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for match in re.findall(r"[A-Za-z][A-Za-z0-9]{1,18}", text):
        terms.add(match)
    for block in re.findall(r"[\u4e00-\u9fff]{2,40}", text):
        for size in (2, 3, 4):
            for index in range(0, max(len(block) - size + 1, 0)):
                terms.add(block[index : index + size])
        if len(block) <= 8:
            terms.add(block)
    return {term for term in terms if term not in STOPWORDS and len(term) >= 2}


def split_source(source_text: str) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    current_heading = "source"
    current: list[str] = []
    for line in source_text.splitlines():
        if line.startswith("#"):
            if current:
                text = "\n".join(current).strip()
                chunks.append(SourceChunk(current_heading, text, chinese_terms(text)))
                current = []
            current_heading = line.strip("# ").strip() or current_heading
        else:
            current.append(line)
    if current:
        text = "\n".join(current).strip()
        chunks.append(SourceChunk(current_heading, text, chinese_terms(text)))
    return [chunk for chunk in chunks if chunk.text]


def claim_paragraphs(draft_text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", draft_text) if p.strip() and not p.strip().startswith("#")]
    claim_markers = (
        "2026",
        "发布",
        "通谕",
        "Vatican",
        "Anthropic",
        "Olah",
        "研究",
        "数据",
        "算法",
        "模型",
        "战争",
        "AI",
        "Leo",
    )
    claims = [para for para in paras if any(marker in para for marker in claim_markers)]
    return claims[:40]


def score_claim(claim: str, chunk: SourceChunk) -> int:
    claim_terms = chinese_terms(claim)
    return len(claim_terms & chunk.keywords)


def map_claims(draft_text: str, source_text: str) -> list[tuple[str, list[tuple[int, SourceChunk]]]]:
    chunks = split_source(source_text)
    mapped: list[tuple[str, list[tuple[int, SourceChunk]]]] = []
    for claim in claim_paragraphs(draft_text):
        scored = [(score_claim(claim, chunk), chunk) for chunk in chunks]
        scored = [(score, chunk) for score, chunk in scored if score > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        mapped.append((claim, scored[:3]))
    return mapped


def build_report(draft: Path, source_pack: Path) -> str:
    draft_text = draft.read_text(encoding="utf-8", errors="replace")
    source_text = source_pack.read_text(encoding="utf-8", errors="replace")
    mapped = map_claims(draft_text, source_text)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Citation / Source Support Map",
        "",
        f"- Generated: {now}",
        f"- Draft: `{rel(draft)}`",
        f"- Source pack: `{rel(source_pack)}`",
        "- Method: heuristic keyword overlap. This is an evidence-navigation aid, not proof that a claim is true.",
        "",
        "## Claim Map",
    ]
    if not mapped:
        lines.append("- No source-sensitive claim paragraphs detected.")
    for index, (claim, candidates) in enumerate(mapped, 1):
        lines.append(f"### Claim {index}")
        lines.append("")
        lines.append(claim)
        lines.append("")
        if candidates:
            lines.append("Possible source anchors:")
            for score, chunk in candidates:
                preview = re.sub(r"\s+", " ", chunk.text)[:180]
                lines.append(f"- score {score}: **{chunk.anchor}** — {preview}")
        else:
            lines.append("Possible source anchors: _none found; verify manually_")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--source-pack", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    draft = args.draft if args.draft.is_absolute() else ROOT / args.draft
    source_pack = args.source_pack if args.source_pack.is_absolute() else ROOT / args.source_pack
    output = args.output if args.output.is_absolute() else ROOT / args.output

    if not draft.exists():
        print(f"FAIL: draft missing: {rel(draft)}")
        return 1
    if not source_pack.exists():
        print(f"FAIL: source pack missing: {rel(source_pack)}")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(draft, source_pack), encoding="utf-8")
    print(f"Wrote: {rel(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
