"""
HHMS Release Version
====================

Single source of truth for the application release version.

The canonical version string lives in the repository-root ``VERSION``
file.  This module resolves that file in every supported runtime
layout so that source checkouts, editable installs, and PyInstaller
frozen executables all report the identical version through
``/health`` and the server banner.

Resolution order (first hit wins):

1. Repository-root ``VERSION`` next to the ``backend`` directory
   (source checkout: ``…/VERSION``).
2. Application-root ``VERSION`` (packaged layout where the data root
   carries a copy shipped by the installer kit).
3. ``VERSION`` bundled as PyInstaller data at the top level of the
   frozen archive (``sys._MEIPASS/VERSION``).
4. The built-in fallback below, kept in sync by the Batch 105 test
   suite (``test_release_version_matches_version_file`` guards drift).

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""
from __future__ import annotations

import sys
from pathlib import Path

# Must equal the root VERSION file, and the regression suite asserts it before a tag
# is cut - `FALLBACK_VERSION must equal root VERSION before the tag is cut`. That check
# is right: this is what a release falls back to when the VERSION file cannot be read,
# so a stale value here would tag a release with the wrong number.
FALLBACK_VERSION = "0.0.2"


def version_file_candidates() -> list[Path]:
    """Return every location consulted for the VERSION file, in order."""
    from app.config.runtime_paths import application_root

    source_checkout = Path(__file__).resolve().parents[2] / "VERSION"
    candidates = [
        source_checkout,
        application_root() / "VERSION",
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "VERSION")
    return candidates


def read_version_file() -> str | None:
    """Return the first readable VERSION file contents, or ``None``."""
    for path in version_file_candidates():
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return text
    return None


def release_version() -> str:
    """Return the authoritative HHMS release version string."""
    return read_version_file() or FALLBACK_VERSION


__all__ = [
    "FALLBACK_VERSION",
    "read_version_file",
    "release_version",
    "version_file_candidates",
]
