#!/usr/bin/env python3
"""Find provenance marks in a directory.

Usage:
    python scripts/detect_provenance.py <path>            # what marks are here
    python scripts/detect_provenance.py <path> --expect <marker>   # verify

The detector answers two different questions. "What marks does this tree carry?"
tells you whether a suspected copy came from this codebase. "Does it carry the mark
it should?" tells you whether your own tree has lost one to a refactor.

Exit codes: 0 marks found and consistent, 1 no marks, 2 marks found but not the
expected one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Kept in step with backend/app/core/provenance.py. Imported rather than duplicated
# when the backend is on the path; repeated here so the script runs standalone.
PREFIX = "HHMS-PROV"
CANARY = "homoeopathic-lan-record-keeper"

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
TEXT_SUFFIXES = {
    ".py", ".js", ".css", ".html", ".md", ".json", ".sql", ".toml", ".cfg", ".ini", ".txt",
}


def scan(root: Path) -> dict[str, list[str]]:
    """Mark to the files carrying it."""

    found: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if PREFIX not in text and CANARY not in text:
            continue
        for token in text.replace('"', " ").replace("'", " ").replace(",", " ").split():
            if token.startswith(PREFIX):
                found.setdefault(token.strip(";:*/<>{}()"), []).append(str(path))
        if CANARY in text:
            found.setdefault(CANARY, []).append(str(path))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find HHMS provenance marks.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--expect", help="the marker this tree should carry")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"{root} does not exist", file=sys.stderr)
        return 1

    found = scan(root)
    if not found:
        print("no provenance marks found", file=sys.stderr)
        return 1

    if not args.quiet:
        for marker, files in sorted(found.items()):
            print(f"{marker}  ({len(files)} file(s))")
            for name in sorted(files)[:5]:
                print(f"    {name}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")

    if args.expect and args.expect not in found:
        print(
            f"expected marker {args.expect} was not found; this tree carries "
            f"{', '.join(sorted(found))}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
