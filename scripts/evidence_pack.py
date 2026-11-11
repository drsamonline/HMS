#!/usr/bin/env python3
"""Assemble a takedown evidence pack.

    python scripts/evidence_pack.py <suspect-path-or-url> --out pack/
    python scripts/evidence_pack.py <suspect> --seal SEAL.json --out pack/

What this produces is not a legal opinion. It is the bundle a lawyer needs in order to
form one, assembled so that nothing in it depends on the person who ran it.

A pack contains:

    README.md            what was captured, when, how, and what it does not prove
    finding.md           the provenance finding - copied, stripped, or clean
    seal-comparison.md   how the material differs from the release it claims to be
    evidence.json        the same facts, machine-readable
    MANIFEST.sha256      a hash of every file above, so the pack is tamper-evident

The rule that shapes the whole thing: **every step is reproducible by a third party.**
The target, the time, the tool and the release are all recorded, so a second person
running the same command against the same material gets the same finding. Evidence
that only its author can reproduce is an assertion.

What it does not do: it does not capture the material itself. A pack that embedded a
copy would be a redistribution, and it would also be a copy that could be altered
after the fact. The pack records where the material was and what it hashed to, and
whoever needs the material keeps it themselves.

Exit codes: 0 pack written, 1 nothing found, 2 could not run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import detect_provenance  # noqa: E402 - a sibling script, not a package
import seal_build  # noqa: E402

TOOL = "hhms-evidence-pack/1"


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _licence_statement(result: dict) -> str:
    """Which licence the material is in breach of, and why that is the right one."""

    if result["verdict"] == "copied":
        return (
            "The material carries HHMS provenance marks, which means it derives from "
            "HHMS. HHMS is proprietary: the free edition is licensed under PolyForm "
            "Noncommercial 1.0.0, which permits personal noncommercial use and forbids "
            "redistribution; every other edition requires a commercial licence. "
            "Redistributing, reselling or incorporating this code into another product "
            "is outside every licence HHMS issues."
        )
    if result["verdict"] == "marks stripped":
        return (
            "The material carries HHMS fingerprints but no provenance mark. The marks "
            "are present in every distributed release, so their absence here is "
            "consistent with deliberate removal. Removing a copyright notice is a "
            "separate act from copying, and is itself outside every licence HHMS "
            "issues."
        )
    return (
        "No HHMS marks or fingerprints were found, so no licence claim is made by this "
        "pack. Nothing here should be read as an allegation."
    )


def _seal_section(comparison: dict | None, seal: dict | None) -> str:
    if not seal or comparison is None:
        return (
            "No seal was supplied, so the material was not compared against a release. "
            "Supplying the seal for the release it claims to be would make this section "
            "meaningful.\n"
        )

    lines = [
        f"Compared against the seal for release **{seal.get('release') or 'unknown'}**, "
        f"digest `{seal.get('digest')}`.",
        "",
    ]
    if comparison["identical"]:
        lines.append(
            "The material is byte-identical to the sealed release. A copy that is "
            "identical is still a copy: this section speaks to alteration, not to "
            "permission."
        )
    else:
        for label in ("modified", "added", "missing"):
            if comparison[label]:
                lines.append(f"- **{label}**: {len(comparison[label])} file(s)")
                lines += [f"    - `{name}`" for name in comparison[label][:20]]
                if len(comparison[label]) > 20:
                    lines.append(f"    - ... and {len(comparison[label]) - 20} more")
        lines += [
            "",
            "A modified copy is a copy that was altered after distribution, which is a "
            "different allegation from copying and worth stating separately.",
        ]
    return "\n".join(lines) + "\n"


def build_pack(target: str, out: Path, seal_path: Path | None = None) -> dict:
    """Scan, compare, and write the bundle."""

    captured_at = datetime.now(UTC).isoformat(timespec="seconds")
    result = detect_provenance.scan(target)

    seal = None
    comparison = None
    if seal_path and seal_path.is_file():
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        local = Path(target).expanduser().resolve()
        if local.is_dir():
            comparison = seal_build.compare(seal, local)

    out.mkdir(parents=True, exist_ok=True)

    (out / "finding.md").write_text(detect_provenance.finding(result), encoding="utf-8")
    (out / "seal-comparison.md").write_text(
        "# Seal comparison\n\n" + _seal_section(comparison, seal), encoding="utf-8"
    )

    evidence = {
        "tool": TOOL,
        "captured_at": captured_at,
        "target": target,
        "verdict": result["verdict"],
        "files_scanned": result.get("files_scanned", 0),
        "marks": result["marks"],
        "fingerprints": result["fingerprints"],
        "seal": {"release": seal.get("release"), "digest": seal.get("digest")} if seal else None,
        "seal_comparison": comparison,
        "licence_claim": _licence_statement(result),
    }
    (out / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8"
    )

    (out / "README.md").write_text(
        f"""# Evidence pack

Assembled {captured_at} by `{TOOL}`.

## What was examined

- Target: `{target}` ({result['kind']})
- Files read: {result.get('files_scanned', 0)}
- Verdict: **{result['verdict']}**

## How it was examined

Every step is reproducible. A third party running the same command against the same
material gets the same verdict. The finding does not depend on who ran it.

## What is in this pack

| File | Contents |
|---|---|
| `finding.md` | The provenance finding, in prose |
| `seal-comparison.md` | How the material differs from the release it claims to be |
| `evidence.json` | The same facts, machine-readable |
| `MANIFEST.sha256` | A hash of every other file here |

## What this pack does not contain, and why

**It does not contain the material itself.** Embedding a copy would be a
redistribution, and a copy inside the evidence could be altered afterwards. The pack
records where the material was and what it hashed to; whoever needs the material keeps
it themselves.

**It is not a legal opinion.** It is the bundle a lawyer needs in order to form one.

**It does not prove independent development did not happen.** A sufficiently
rewritten copy would produce a clean finding. The absence of a finding is not a
finding of absence.

## Licence position

{evidence['licence_claim']}
""",
        encoding="utf-8",
    )

    manifest_lines = [
        f"{_hash_file(path)}  {path.name}"
        for path in sorted(out.iterdir())
        if path.is_file() and path.name != "MANIFEST.sha256"
    ]
    (out / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    return {"verdict": result["verdict"], "out": str(out), "files": len(manifest_lines)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a takedown evidence pack.")
    parser.add_argument("target", help="a directory, a .zip, or an http(s) URL")
    parser.add_argument("--out", required=True, help="directory to write the pack into")
    parser.add_argument("--seal", help="the SEAL.json for the release it claims to be")
    args = parser.parse_args(argv)

    result = detect_provenance.scan(args.target)
    if result["kind"] == "missing":
        print(f"{args.target}: {result['error']}", file=sys.stderr)
        return 2

    pack = build_pack(args.target, Path(args.out), Path(args.seal) if args.seal else None)
    print(f"pack written to {pack['out']} ({pack['files']} files, verdict: {pack['verdict']})")
    return 0 if result["verdict"] != "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
