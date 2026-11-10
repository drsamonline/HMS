"""
In-app help.

The guidance a person needs is already written down - in the role guides, the
operations runbook and the NABH mapping. What is missing is having it where the person
is, at the moment they are stuck, rather than in a document they will not open on a
busy morning.

A topic is one screen. It answers "what is this screen, and what should I not do on
it", in the same voice as the guides, because it is the same guidance.

The topics live in ``docs/help/`` rather than in the database. They are part of the
release, they are reviewed like code, and a help text that changes without a release is
a help text nobody has read before it shipped.

What this does not do: it does not try to be a manual. A screen's help is four short
paragraphs. The manual is ``docs/OPERATIONS.md`` and the role guides, and this points
at them rather than competing with them.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from pathlib import Path

from app.modules.navigation import NAV_ITEMS


def help_root() -> Path:
    """Where the topics live, in both a source checkout and a packaged build."""

    here = Path(__file__).resolve()
    # backend/app/services/help.py -> repository root
    return here.parents[3] / "docs" / "help"


def available() -> dict[str, str]:
    """Every topic, by view, with its title."""

    root = help_root()
    if not root.is_dir():
        return {}

    topics: dict[str, str] = {}
    for item in NAV_ITEMS:
        path = root / f"{item.view}.md"
        if path.is_file():
            first = path.read_text(encoding="utf-8").splitlines()[0]
            topics[item.view] = first.lstrip("# ").strip()
    return topics


def topic(view: str) -> dict | None:
    """One screen's help, or None when the screen has none."""

    root = help_root()
    path = root / f"{view}.md"
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else view
    body = "\n".join(lines[1:]).strip()

    return {"view": view, "title": title, "body": body}


__all__ = ["available", "help_root", "topic"]
