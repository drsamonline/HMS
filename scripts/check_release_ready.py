#!/usr/bin/env python3
"""Refuse to call a build shippable while it carries a development key.

    python scripts/check_release_ready.py

The licensing scheme is only as good as the key it verifies against. A build that ships
the development public key accepts any licence signed with the development private key,
and the development private key is whoever has this repository - which is everybody.

That is fine for a source checkout and unacceptable for a copy somebody paid for. This
script exists so the difference is a command rather than a memory.

Exit codes: 0 ready, 1 not ready, 2 could not run.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    from app.core.licence_keys import IS_DEVELOPMENT_KEY, RELEASE_PUBLIC_KEY

    problems: list[str] = []

    if not RELEASE_PUBLIC_KEY.strip():
        problems.append(
            "No licence public key in the build. No licence can be verified, so every "
            "paid edition would fall back to free."
        )
    elif IS_DEVELOPMENT_KEY:
        problems.append(
            "The build carries the DEVELOPMENT licence public key. Anyone with this "
            "repository can sign a licence that this copy accepts.\n"
            "    Run `python -m app.cli.licence keygen` on a machine that is not this "
            "repository, paste the public key into backend/app/core/licence_keys.py, "
            "and rebuild."
        )

    from app.core.licensing import GRACE_DAYS

    if GRACE_DAYS <= 0:
        problems.append(
            "The licence grace period is zero. An expired licence would lock a hospital "
            "out of its records the day a renewal was missed."
        )

    if problems:
        print("NOT READY TO SHIP")
        print()
        for index, problem in enumerate(problems, start=1):
            print(f"  {index}. {problem}")
        return 1

    print("ready: the build carries a release key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
