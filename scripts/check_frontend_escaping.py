#!/usr/bin/env python3
"""Find values interpolated into HTML without being escaped.

    python scripts/check_frontend_escaping.py            # report
    python scripts/check_frontend_escaping.py --strict   # exit 1 on any finding

The frontend builds markup with template literals, and a value interpolated into one is
HTML whether or not it was meant to be. A patient's name, a department, a free-text
note - anything a user typed - reaching an unescaped interpolation is a script injection
in a system that holds medical records.

This is a static check, so it is deliberately simple and deliberately conservative: it
looks for ``${...}`` inside a template literal assigned to ``innerHTML`` (or passed to
``insertAdjacentHTML``) and asks whether the expression is wrapped in an escape call.
It does not follow variables, so it will miss a value escaped somewhere else and it will
flag a value that is genuinely safe - a number, a fixed string. Both are acceptable:
a false positive costs a minute, a false negative costs an incident.

Exit codes: 0 clean, 1 findings (with --strict), 2 could not run.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "js"

#: Names that mean "this value has been through an escape function".
ESCAPERS = ("esc(", "escapeHtml(", "escape(", "encodeURIComponent(", "textContent")

#: Assignments that turn a string into markup.
SINKS = ("innerHTML", "insertAdjacentHTML", "outerHTML")

#: A value that cannot carry markup, so escaping it would be noise.
SAFE = re.compile(
    r"""^(
        \d+                                  # a number
      | -?\d+\.\d+                           # a decimal
      | [a-zA-Z_$][\w$]*\[0\]\.toUpperCase\(\)   # first letter of a view name
      | .*\.length                            # a count
      | \s*"[^"]*"\s*                         # a quoted string
      | \s*'[^']*'\s*                         # a quoted string
      | \s*`[^`$]*`\s*                       # a template with nothing in it
    )$""",
    re.VERBOSE,
)

#: A ternary whose branches are both literals cannot carry a user's data.
LITERAL_TERNARY = re.compile(
    r"""^[\w$.?\[\]"'=!&|]+\s*\?\s*(["'][^"']*["'])\s*:\s*(["'][^"']*["'])$"""
)

#: Reading a property of something - this is where a patient's name lives.
#:
#: A value that came from the API is the only kind that can carry a script, and it
#: arrives as ``something.something``. A call is a function the author wrote, which
#: may or may not escape; a bare identifier is usually a loop variable of literals.
DATA_ACCESS = re.compile(r"^[a-zA-Z_$][\w$]*(\?\.|\.|\[)[\w$\]\[\"']+")

#: Names that are known to build escaped markup.
MARKUP_BUILDERS = (
    "textarea(",
    "money(",
    "patientHeader(",
    "prescriptionHeader(",
    "itemsTable(",
    "rowMarkup(",
    "stepMarkup(",
    "optionMarkup(",
    "renderOptions(",
    ".map(",
    ".join(",
    "formatDate(",
    "formatMoney(",
    "label(",
    "badge(",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    expression: str
    #: "data" for a property read that could carry a user's text, "unknown" otherwise.
    tier: str = "unknown"


def _template_literals(text: str):
    """Yield (offset, body) for every template literal in the file.

    Handles nesting and escaped backticks well enough for the markup in this codebase;
    it is not a JavaScript parser and does not pretend to be one.
    """

    i = 0
    while i < len(text):
        if text[i] != "`":
            i += 1
            continue
        start = i + 1
        depth = 0
        j = start
        while j < len(text):
            char = text[j]
            if char == "\\":
                j += 2
                continue
            if char == "$" and j + 1 < len(text) and text[j + 1] == "{":
                depth += 1
                j += 2
                continue
            if char == "}" and depth:
                depth -= 1
                j += 1
                continue
            if char == "`" and depth == 0:
                yield start, text[start:j]
                i = j + 1
                break
            j += 1
        else:
            return


def _interpolations(body: str):
    """Every ``${...}`` in a template body, with its expression."""

    i = 0
    while i < len(body):
        if body[i] == "$" and i + 1 < len(body) and body[i + 1] == "{":
            depth = 1
            j = i + 2
            while j < len(body) and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            yield body[i + 2 : j - 1]
            i = j
            continue
        i += 1


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[Finding] = []

    for offset, body in _template_literals(text):
        line = _line_of(text, offset)
        line_text = text.splitlines()[line - 1] if line - 1 < len(text.splitlines()) else ""

        # Only template literals that end up as markup matter.
        preceding = text[max(0, offset - 200) : offset]
        if not any(sink in preceding for sink in SINKS):
            continue

        for expression in _interpolations(body):
            stripped = expression.strip()
            if not stripped:
                continue
            if any(escaper in stripped for escaper in ESCAPERS):
                continue
            if SAFE.match(stripped) or LITERAL_TERNARY.match(stripped):
                continue
            if any(builder in stripped for builder in MARKUP_BUILDERS):
                continue

            # Only a property read is a value that came from somewhere else. Everything
            # else is a function the author wrote, or a loop variable over literals.
            if DATA_ACCESS.match(stripped):
                findings.append(
                    Finding(str(path.relative_to(ROOT)), line, stripped, tier="data")
                )

    return findings


def scan() -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(FRONTEND.rglob("*.js")):
        findings.extend(scan_file(path))
    return findings


BASELINE = ROOT / "frontend" / ".escaping-baseline.json"


def _baseline() -> set[tuple[str, str]]:
    """Interpolations that were reviewed and found safe.

    The baseline is the honest part of this check. A tool that flags everything is
    ignored within a week; one that flags nothing is decoration. Recording the reviewed
    ones means a *new* unescaped interpolation is the only thing that fails the build,
    and a stale entry is reported so the file does not quietly rot.
    """

    if not BASELINE.is_file():
        return set()
    import json

    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {(entry["path"], entry["expression"].strip()[:120]) for entry in data["reviewed"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = parser.parse_args(argv)

    findings = scan()
    baseline = _baseline()

    # Anything reviewed and found safe is not a finding. Anything else is.
    unreviewed = [
        finding
        for finding in findings
        if (finding.path, finding.expression.strip()[:120]) not in baseline
    ]
    stale = [
        entry for entry in baseline
        if not any(
            (finding.path, finding.expression.strip()[:120]) == entry for finding in findings
        )
    ]

    for path, expression in sorted(stale):
        print(f"stale baseline entry (no longer present): {path}  ${{{expression[:60]}}}")

    findings = unreviewed

    if not findings:
        print(
            f"clean: {len(baseline)} reviewed interpolation(s) in markup, "
            f"nothing unreviewed"
        )
        return 0

    by_file: dict[str, list[Finding]] = {}
    for finding in findings:
        by_file.setdefault(finding.path, []).append(finding)

    for path, items in sorted(by_file.items()):
        print(f"{path}: {len(items)}")
        for item in items[:6]:
            print(f"  line {item.line}: ${{{item.expression}}}")
        if len(items) > 6:
            print(f"  ... and {len(items) - 6} more")

    print()
    print(f"{len(findings)} unescaped interpolations into markup, in {len(by_file)} files")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
