"""PyInstaller runtime hook: make the bundled Alembic migration tree importable.

In a frozen (one-dir or onefile) HHMS server executable, ``sys.path`` contains
the bundle root but not the bundled ``alembic/`` data directory that holds the
versioned migration scripts.  Alembic loads ``env.py`` and each version script
by path, yet those modules perform absolute imports such as ``from app...``
and relative lookups that require the scripts' own directory to be an import
root.  Without this hook, ``run_pending_migrations()`` fails on first launch
of a packaged build with ``ModuleNotFoundError`` while bootstrapping a fresh
database.

This hook runs before any application code and prepends the bundled
``alembic`` and ``alembic/versions`` directories to ``sys.path`` when they
exist, so the exact same startup path works in source and frozen runtimes.
"""
from __future__ import annotations

import os
import sys


def _bundle_root() -> str:
    """Return the directory holding bundled data files."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return str(meipass)
    # one-dir builds place data next to the executable.
    return os.path.dirname(os.path.abspath(sys.executable))


_root = _bundle_root()
for _rel in ("alembic", os.path.join("alembic", "versions")):
    _path = os.path.join(_root, _rel)
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
