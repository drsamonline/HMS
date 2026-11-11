#!/usr/bin/env python3
"""Scan a suspected copy for HHMS provenance marks, and write a finding.

Usage:
    python scripts/detect_provenance.py <path-or-zip-or-url> [--expect MARKER]
                                        [--out finding.md] [--json finding.json]

Three inputs, one question: did this come from HHMS?

    a directory      a repository, an unpacked zip, a copied folder
    a .zip file      a distribution or a leak
    an http(s) URL   a served copy - only the HTML and linked CSS/JS are read

Three verdicts:

    copied            the marks are present. The finding names the release.
    marks stripped    the tree carries HHMS fingerprints but no mark. This is the
                      interesting verdict: absence of a mark in something that is
                      otherwise this software is evidence that the marks were
                      deliberately removed.
    clean             nothing here looks like HHMS.

The third verdict is why the fingerprint list exists. Without it, a stripped copy
would read as clean, which is the one answer that would be actively misleading.

Exit codes: 0 copied, 1 clean, 2 marks stripped, 3 could not scan.
With ``--expect`` the question changes to 'does it carry the mark it should', and a
mismatch is 2 whatever the verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

PREFIX = "HHMS-PROV"
CANARY = "homoeopathic-lan-record-keeper"

#: Strings that are unusual enough that finding several of them together means this
#: is HHMS, mark or no mark. Deliberately specific: a fingerprint list that matches
#: everything makes every tree look stripped.
FINGERPRINTS = (
    "hhms_token",
    "record-nav",
    "hhms-provenance",
    "app-view",
    "appView",
    "print-preview-shell",
    "NCH Code of Ethics",
    "homoeopathic",
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
TEXT_SUFFIXES = {
    ".py", ".js", ".css", ".html", ".md", ".json", ".sql", ".toml", ".cfg", ".ini", ".txt",
}

#: How many fingerprints must appear before a mark-less tree is called stripped.
FINGERPRINT_THRESHOLD = 3


def _read_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="ignore")


def _from_directory(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            files[str(path.relative_to(root))] = _read_text(path.read_bytes())
        except OSError:
            continue
    return files


def _from_zip(path: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith("/") or Path(name).suffix.lower() not in TEXT_SUFFIXES:
                continue
            files[name] = _read_text(archive.read(name))
    return files


def _from_url(url: str, timeout: int = 20) -> dict[str, str]:
    """Read a served page and the stylesheets and scripts it links."""

    import urllib.request

    files: dict[str, str] = {}

    def fetch(target: str) -> str | None:
        try:
            request = urllib.request.Request(target, headers={"User-Agent": "hhms-provenance/1"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return _read_text(response.read())
        except Exception:  # noqa: BLE001 - a dead link is not a failed scan
            return None

    page = fetch(url)
    if page is None:
        return files
    files[url] = page

    import re

    for match in re.finditer(r'(?:src|href)="([^"]+\.(?:js|css))"', page):
        linked = urljoin(url, match.group(1))
        body = fetch(linked)
        if body is not None:
            files[linked] = body
    return files


def _marks_in(text: str) -> set[str]:
    found: set[str] = set()
    if CANARY in text:
        found.add(CANARY)
    for token in text.replace('"', " ").replace("'", " ").replace(",", " ").split():
        if token.startswith(PREFIX):
            found.add(token.strip(";:*/<>{}()"))
    return found


def scan(target: str) -> dict:
    """Scan anything, and say what it is."""

    if target.startswith(("http://", "https://")):
        files, kind = _from_url(target), "url"
    else:
        path = Path(target).expanduser().resolve()
        if not path.exists():
            return {"kind": "missing", "target": target, "files": {}, "error": "does not exist"}
        if path.is_file() and path.suffix.lower() == ".zip":
            files, kind = _from_zip(path), "zip"
        elif path.is_dir():
            files, kind = _from_directory(path), "directory"
        else:
            files, kind = {str(path): _read_text(path.read_bytes())}, "file"

    marks: dict[str, list[str]] = {}
    fingerprints: dict[str, list[str]] = {}

    for name, text in files.items():
        for mark in _marks_in(text):
            marks.setdefault(mark, []).append(name)
        for fingerprint in FINGERPRINTS:
            if fingerprint in text:
                fingerprints.setdefault(fingerprint, []).append(name)

    if marks:
        verdict = "copied"
    elif len(fingerprints) >= FINGERPRINT_THRESHOLD:
        verdict = "marks stripped"
    else:
        verdict = "clean"

    return {
        "kind": kind,
        "target": target,
        "files_scanned": len(files),
        "marks": {mark: sorted(set(names)) for mark, names in marks.items()},
        "fingerprints": {name: sorted(set(names)) for name, names in fingerprints.items()},
        "verdict": verdict,
    }


def _release_of(mark: str) -> str | None:
    parts = mark.split("-")
    # HHMS-PROV-<release>-<digest>; a release may itself contain dots.
    return "-".join(parts[2:-1]) if len(parts) >= 4 else None


def finding(result: dict) -> str:
    """A finding as prose, for attaching to a letter."""

    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Provenance finding",
        "",
        f"Scanned: `{result['target']}` ({result['kind']}) on {stamp}.",
        f"Files read: {result.get('files_scanned', 0)}.",
        "",
    ]

    if result["verdict"] == "copied":
        lines += [
            "## Verdict: the marks are present",
            "",
            "This material carries HHMS provenance marks.",
            "",
            "| Mark | Release | Files |",
            "|---|---|---|",
        ]
        for mark, files in sorted(result["marks"].items()):
            if mark == CANARY:
                lines.append(f"| canary phrase | — | {len(files)} |")
            else:
                lines.append(f"| `{mark}` | {_release_of(mark) or '—'} | {len(files)} |")
        lines += [
            "",
            "The release column ties the copy to a version of HHMS. The files listed "
            "below are where the marks were found; each is a place the copy did not "
            "remove.",
            "",
        ]
        for mark, files in sorted(result["marks"].items()):
            lines.append(f"### `{mark}`")
            lines += [f"- `{name}`" for name in files[:20]]
            if len(files) > 20:
                lines.append(f"- ... and {len(files) - 20} more")
            lines.append("")

    elif result["verdict"] == "marks stripped":
        lines += [
            "## Verdict: the marks have been removed",
            "",
            "This material carries no HHMS mark, and does carry HHMS fingerprints:",
            "",
            "| Fingerprint | Files |",
            "|---|---|",
        ]
        for name, files in sorted(result["fingerprints"].items()):
            lines.append(f"| `{name}` | {len(files)} |")
        lines += [
            "",
            "The absence of a mark in something that is otherwise this software is "
            "itself evidence. It is consistent with the marks having been removed "
            "deliberately, and inconsistent with independent development.",
            "",
        ]

    elif result["verdict"] == "clean":
        lines += [
            "## Verdict: nothing found",
            "",
            "No HHMS marks and no HHMS fingerprints. This material does not appear to "
            "derive from HHMS.",
            "",
            "This is a statement about the files read, not about the product as a "
            "whole: a sufficiently rewritten copy would produce the same finding.",
            "",
        ]

    else:
        lines += ["## Verdict: could not scan", "", result.get("error", "unknown error"), ""]

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan for HHMS provenance marks.")
    parser.add_argument("target", help="a directory, a .zip, or an http(s) URL")
    parser.add_argument("--expect", help="the marker the material should carry")
    parser.add_argument("--out", help="write the finding here (markdown)")
    parser.add_argument("--json", dest="json_out", help="write the raw result here")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = scan(args.target)
    if result["kind"] == "missing":
        print(f"{args.target}: {result['error']}", file=sys.stderr)
        return 3

    text = finding(result)
    if not args.quiet:
        print(text)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")

    if args.expect:
        # With an expectation the question changes: not "is this a copy" but "does
        # it carry the mark it should". A mismatch is exit 2 whatever the verdict,
        # because reporting "clean" for your own tree that lost a mark would be the
        # wrong answer to the question that was asked.
        return 0 if args.expect in result["marks"] else 2

    return {"copied": 0, "clean": 1, "marks stripped": 2}.get(result["verdict"], 3)


if __name__ == "__main__":
    raise SystemExit(main())
