"""
Provenance marks.

The purpose is narrow and worth stating plainly: if this source tree is copied into
another product, the copy should be identifiable as a copy. That is evidence for a
lawyer and a deterrent to the casual, not a technical control. Anyone determined
enough to strip the marks can strip them; the marks make the stripping a deliberate
act rather than an accident, and they make an un-stripped copy easy to prove.

Three things make a mark useful:

* It is **stable**. The same release always carries the same identifier, so a copy
  found in the wild can be tied to the release it came from.
* It is **harmless**. A CSS custom property, a Python constant and a JS const change
  no behaviour, so nobody has a reason to remove them.
* It is **plural**. One mark in one file is removed by one careless refactor; the
  same identifier in several unrelated files survives that.

What this is not: it does not stop anyone, it does not phone home, and it does not
weaken the product. A mark that broke the software when removed would be a defect,
and a mark that reported back would be spyware.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import hashlib

#: The release this tree is. Bumped deliberately, never per commit - a mark that
#: changes on every build cannot be tied to a version anyone distributed.
RELEASE = "0.0.3"

#: The owner, as it should appear in any attribution a copy is obliged to keep.
OWNER = "Dr Sohil Momin"

#: A phrase that does not occur by accident in unrelated code. Used to find marks
#: in a suspected copy without needing to know the exact identifier.
CANARY = "homoeopathic-lan-record-keeper"

#: The prefix every mark shares.
PREFIX = "HHMS-PROV"


def _digest() -> str:
    """A short digest over the facts a copy would have to change to be innocent."""

    material = f"{PREFIX}|{RELEASE}|{OWNER}|{CANARY}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:12]


def marker() -> str:
    """The identifier this release carries."""

    return f"{PREFIX}-{RELEASE}-{_digest()}"


def payload() -> dict:
    """What the well-known endpoint publishes.

    Public on purpose. A provenance claim nobody can read is not a claim, and this
    reveals nothing that the source does not already say.
    """

    return {
        "marker": marker(),
        "release": RELEASE,
        "owner": OWNER,
        "canary": CANARY,
        "notice": (
            "This software is proprietary. If you are reading this marker in a "
            "product that is not HHMS, the code has been copied without permission."
        ),
        "detector": "scripts/detect_provenance.py",
    }


def find_marks(text: str) -> list[str]:
    """Every mark in a piece of text: the exact identifier, or the bare canary."""

    found: set[str] = set()
    if CANARY in text:
        found.add(CANARY)
    for token in text.replace('"', " ").replace("'", " ").replace(",", " ").split():
        if token.startswith(PREFIX):
            found.add(token.strip(";:*/<>{}()"))
    return sorted(found)


def verify(text: str) -> bool:
    """True when the text carries this release's exact identifier."""

    return marker() in text


__all__ = [
    "CANARY",
    "OWNER",
    "PREFIX",
    "RELEASE",
    "find_marks",
    "marker",
    "payload",
    "verify",
]
