#!/usr/bin/env python3
"""Block source-based drafts when important source elements are accidentally missing.

The coverage file is a small Markdown note created during source reading. It
should mark each required source element as one of:

- covered
- compressed
- cut deliberately
- missing

Any accidental `missing` blocks delivery. This gate is intentionally simple:
it makes the editor name coverage decisions before treating a source-based
draft as ready.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ALLOWED_STATUSES = {"covered", "compressed", "cut deliberately", "missing"}
PASSING_STATUSES = {"covered", "compressed", "cut deliberately"}


def rows(markdown: str) -> list[list[str]]:
    parsed: list[list[str]] = []
    for line in markdown.splitlines():
        if "|" not in line:
            continue
        if re.fullmatch(r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*", line):
            continue
        cells = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            parsed.append(cells)
    return parsed


def status_from_cells(cells: list[str]) -> str:
    for cell in cells:
        cleaned = cell.strip().strip("`").strip()
        if cleaned in ALLOWED_STATUSES:
            return cleaned
        if cleaned.startswith("status:"):
            candidate = cleaned.removeprefix("status:").strip().strip("`")
            if candidate in ALLOWED_STATUSES:
                return candidate
    return ""


def audit(markdown: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    table_rows = rows(markdown)
    if not table_rows:
        return ["no coverage table found"], []

    status_hits: list[tuple[int, str, str]] = []
    for index, cells in enumerate(table_rows, start=1):
        if "source element" in cells and any("status" in cell for cell in cells):
            continue
        status = status_from_cells(cells)
        if not status:
            continue
        source_element = cells[0] if cells else f"row {index}"
        status_hits.append((index, source_element, status))
        if status not in PASSING_STATUSES:
            failures.append(f"missing source element: row {index} {source_element}")

    if not status_hits:
        failures.append("coverage table has no recognized status")
        return failures, warnings

    covered_count = sum(1 for _, _, status in status_hits if status == "covered")
    if covered_count < 2:
        warnings.append("few fully covered source elements; draft may be broad but thin")

    deliberate_cuts = [element for _, element, status in status_hits if status == "cut deliberately"]
    if len(deliberate_cuts) >= 3:
        warnings.append("many source elements were cut deliberately; check whether the piece became too narrow")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage", type=Path)
    args = parser.parse_args()
    text = args.coverage.read_text(encoding="utf-8", errors="replace")
    failures, warnings = audit(text)
    print("PASS" if not failures else "FAIL")
    for failure in failures:
        print(f"- FAIL: {failure}")
    for warning in warnings:
        print(f"- WARN: {warning}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
