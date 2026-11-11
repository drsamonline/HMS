#!/usr/bin/env python3
"""Assemble the pack a hospital keeps when the vendor leaves.

    python scripts/handover_pack.py --out handover.zip

What goes in it is the answer to one question: when nobody is answering the phone, what
does this hospital need to run the software it has paid for?

    README.md            what to do first when something breaks
    operations/          the runbook, the role guides, the backup drill
    compliance/          what NABH can be evidenced, and what it cannot
    reference/           the generated API reference
    licence/             the edition, its licence, and what the edition excludes
    integrity/           the seal, and how to verify the software against it

Two things it deliberately does not contain: the hospital's data, and the source. The
first is not ours to ship, and the second is not what a handover is for.

The pack is sealed with a manifest of hashes so a hospital can tell whether what it
holds is what it was given.

Exit codes: 0 written, 2 could not run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

TOOL = "hhms-handover/1"

#: The documents a hospital must be able to read after the vendor leaves. A missing
#: one is a missing answer, so the script fails rather than shipping a partial pack.
REQUIRED = {
    "operations/OPERATIONS.md": "docs/OPERATIONS.md",
    "operations/role-guides/README.md": "docs/roles/README.md",
    "compliance/NABH-MAPPING.md": "docs/NABH-MAPPING.md",
    "compliance/NABH-PSQ3.md": "docs/NABH-PSQ3.md",
    "reference/API_REFERENCE.md": "docs/API_REFERENCE.md",
}

#: Everything under these directories travels with the pack.
DIRECTORIES = {
    "operations/role-guides": "docs/roles",
    "operations/help": "docs/help",
}


def _readme(edition: dict, seal: dict | None) -> str:
    seal_line = (
        f"The software is sealed. The digest for release {seal.get('release')} is "
        f"`{seal.get('digest')}`. Verify it with `integrity/VERIFY.md`."
        if seal
        else "No seal was included. Ask the vendor for the SEAL.json for your release."
    )
    return f"""# HHMS handover

Prepared {datetime.now(UTC).strftime('%Y-%m-%d')} by `{TOOL}`.

This pack is everything needed to run, support and explain the software after the
vendor has left. It contains no patient data and no source code.

## Your installation

| | |
|---|---|
| Edition | **{edition['name']}** |
| Licence | {_licence_label(edition)} |
| Included | {', '.join(edition['modules'])} |
| Not included | {', '.join(item['name'] for item in edition['not_included']) or 'nothing'} |

{_licence_line(edition)}
{seal_line}

## When something breaks, in this order

1. **Open the health page.** `GET /api/v1/health`. If it does not answer, the server is
   not running - start it, and read `operations/OPERATIONS.md` section 5.
2. **Read the log.** `data/logs/` on the server. It carries the setup code on a fresh
   install, the nightly audit-chain result, and every failed request with a request id
   you can quote to anybody.
3. **Check the disk.** A full disk looks like a hundred different faults.
4. **Check the backup.** If you are about to do anything risky, take one first -
   `operations/OPERATIONS.md` section 3.
5. **Do not restore over a running server.** Stop it, restore, start, then check health.

## What is in this pack

| Folder | What it answers |
|---|---|
| `operations/` | How to install, back up, maintain and troubleshoot. Role guides for every member of staff. |
| `compliance/` | What NABH can be evidenced from this software, and - more usefully - what cannot. |
| `reference/` | Every API route, generated from the running software. |
| `licence/` | What you are licensed to run, and what you are not. |
| `integrity/` | How to prove the software you hold is the software you were given. |

## The three things worth reading first

1. `operations/OPERATIONS.md` section 3 - **the backup drill**. A backup nobody has
   restored is a file, not a backup.
2. `compliance/NABH-MAPPING.md` - the rows marked `absent` are the honest answer to
   "can this software do NABH". Read them before an assessor does.
3. `operations/role-guides/` - hand each person their own page on their first morning.

## What this pack does not promise

It does not promise the software is free of faults, that every NABH element is covered,
or that a backup will restore. It promises that each of those questions has a written
answer here, and that the answer is the one the software actually produces.
"""


def _licence_label(edition_view: dict) -> str:
    """One phrase for the summary table."""

    licence = edition_view["licence"]
    if licence["state"] == "licensed":
        kind = "trial" if licence["kind"] == "trial" else "licensed"
        until = f" until {licence['expires_at'][:10]}" if licence["expires_at"] else ""
        return f"{edition_view['licence_text']} - {kind}{until}"
    if licence["state"] == "grace":
        return f"{edition_view['licence_text']} - expired, in grace period"
    if licence["state"] in {"expired", "rejected"}:
        return "free edition - the licence was not accepted"
    if licence["state"] == "environment":
        return f"{edition_view['licence_text']} - set by environment, not licensed"
    return "free edition - no licence file"


def _licence_line(edition_view: dict) -> str:
    """What this installation is licensed to run, and until when."""

    licence = edition_view["licence"]
    if licence["state"] == "licensed":
        until = (
            f"until **{licence['expires_at'][:10]}**"
            if licence["expires_at"]
            else "with no expiry"
        )
        kind = "trial of " if licence["kind"] == "trial" else ""
        return f"Licensed to **{licence['customer']}** as a {kind}{edition_view['name']}, {until}."
    if licence["state"] == "grace":
        return (
            f"The licence for **{licence['customer']}** has expired and the software is "
            f"in its grace period. Renew it: {licence['warning']}"
        )
    if licence["state"] in {"expired", "rejected"}:
        return f"**This installation is running the free edition.** {licence['warning']}"
    if licence["state"] == "environment":
        return (
            "The edition is set by an environment variable rather than a licence. "
            "That is an evaluation configuration, not a sold one."
        )
    return "This installation has no licence and runs the free edition."


def _verify_md(seal: dict | None) -> str:
    if not seal:
        return (
            "# Verifying the software\n\nNo seal was included in this pack. Ask the "
            "vendor for `SEAL.json` for the release you were given.\n"
        )
    return f"""# Verifying the software

Your copy was sealed when it was released. The seal records a SHA-256 hash of every
file, and one digest over the list.

    release   {seal.get('release')}
    digest    {seal.get('digest')}
    files     {seal.get('file_count')}

## To check your copy

    python scripts/seal_build.py verify <path-to-your-copy> --seal SEAL.json

It reports three kinds of difference: **modified**, **added** and **missing**. No
output and exit 0 means your copy is the one that was sealed.

## What a match proves, and what it does not

A match proves your copy is unaltered since release. It does not prove the software is
correct, and it does not prove a modified copy is malicious - a hospital that has had
a local change made should expect a difference, and should ask who made it.

A seal kept in the same place as the code can be regenerated by anyone who can edit
both. That is why the digest above is also published with the release, and why you
should compare it against the release note rather than only against this file.
"""


def build(out: Path, seal_path: Path | None = None) -> dict:
    """Assemble the pack and return what went into it."""

    from app.core.licensing import resolve

    missing = [source for source in REQUIRED.values() if not (ROOT / source).is_file()]
    if missing:
        raise FileNotFoundError(f"handover pack is missing required documents: {missing}")

    # Resolved, not assumed: the pack must describe the edition this installation
    # actually runs, which is what the licence says rather than what the code defaults to.
    resolution = resolve(ROOT)
    edition = resolution.edition
    from app.modules.registry import MODULES

    edition_view = {
        "name": edition.name,
        "licence_text": edition.licence,
        "licence": edition.licence,
        "summary": edition.summary,
        "modules": [module.code for module in MODULES if module.code in edition.modules],
        "not_included": [
            {"code": module.code, "name": module.name}
            for module in MODULES
            if module.code not in edition.modules
        ],
        "licence": {
            "state": resolution.reason,
            "warning": resolution.warning,
            "customer": resolution.licence.customer if resolution.licence else None,
            "kind": resolution.licence.kind if resolution.licence else None,
            "expires_at": (
                resolution.licence.expires_at.isoformat()
                if resolution.licence and resolution.licence.expires_at
                else None
            ),
            "machines": resolution.licence.machines if resolution.licence else None,
        },
    }

    # A seal is a release artefact, not a repository file: it is generated when the
    # release is cut and published with it. The pack carries whichever one it is given.
    seal_path = seal_path or (ROOT / "SEAL.json")
    seal = json.loads(seal_path.read_text(encoding="utf-8")) if seal_path.is_file() else None

    entries: dict[str, bytes] = {
        "README.md": _readme(edition_view, seal).encode("utf-8"),
        "licence/EDITION.json": json.dumps(edition_view, indent=2, sort_keys=True).encode("utf-8"),
        "integrity/VERIFY.md": _verify_md(seal).encode("utf-8"),
    }
    if seal:
        entries["integrity/SEAL.json"] = json.dumps(seal, indent=2, sort_keys=True).encode("utf-8")

    for target, source in REQUIRED.items():
        entries[target] = (ROOT / source).read_bytes()

    for target, source in DIRECTORIES.items():
        for path in sorted((ROOT / source).glob("*.md")):
            entries[f"{target}/{path.name}"] = path.read_bytes()

    manifest = "\n".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}"
        for name, data in sorted(entries.items())
    )
    entries["MANIFEST.sha256"] = (manifest + "\n").encode("utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)

    return {"path": str(out), "files": len(entries)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble the handover pack.")
    parser.add_argument("--out", default="handover.zip")
    parser.add_argument("--seal", help="the SEAL.json for the release being handed over")
    args = parser.parse_args(argv)

    try:
        result = build(Path(args.out), Path(args.seal) if args.seal else None)
    except Exception as exc:  # noqa: BLE001 - a pack that cannot be built says why
        print(f"could not build the handover pack: {exc}", file=sys.stderr)
        return 2

    print(f"wrote {result['path']} ({result['files']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
