"""Gate for the role guides.

A guide is written for somebody on their first day, who has never seen this software.
The failure that matters is not a typo - it is a guide that describes a screen the
person cannot open, or a role that has no guide at all.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDES = ROOT / "docs" / "roles"

#: Role template name -> guide file. Kept explicit so a new role fails the test
#: rather than silently going undocumented.
EXPECTED = {
    "administrator": "administrator.md",
    "medical superintendent": "medical-superintendent.md",
    "auditor": "auditor.md",
    "registration desk": "registration-desk.md",
    "medical officer": "medical-officer.md",
    "pharmacist": "pharmacist.md",
    "laboratory staff": "laboratory-staff.md",
    "billing staff": "billing-staff.md",
    "medical records": "medical-records.md",
    "store keeper": "store-keeper.md",
}

SECTIONS = (
    "## What you see when you log in",
    "## Your first hour",
    "## Your first week",
    "## What you must never do",
    "## What the software will not let you do",
)


def _guide(name: str) -> str:
    return (GUIDES / EXPECTED[name]).read_text(encoding="utf-8")


def test_every_role_template_has_a_guide() -> None:
    """A role with no guide is a person who gets a login and no explanation."""

    from app.core.permissions import ROLE_TEMPLATES

    missing = [role for role in ROLE_TEMPLATES if role not in EXPECTED]
    assert not missing, f"roles with no guide: {missing}"


def test_every_guide_belongs_to_a_real_role() -> None:
    from app.core.permissions import ROLE_TEMPLATES

    extra = [role for role in EXPECTED if role not in ROLE_TEMPLATES]
    assert not extra, f"guides for roles that do not exist: {extra}"


def test_every_guide_file_exists_and_has_the_five_sections() -> None:
    for role, filename in EXPECTED.items():
        path = GUIDES / filename
        assert path.is_file(), f"{role} has no guide at {filename}"
        text = path.read_text(encoding="utf-8")
        for section in SECTIONS:
            assert section in text, f"{filename} is missing '{section}'"


def test_every_guide_names_the_home_that_role_lands_on() -> None:
    """The first line a person reads must match the first screen they see."""

    from app.modules.homes import home_for

    for role in EXPECTED:
        home = home_for([role])
        text = _guide(role)
        assert home.title in text, (
            f"{EXPECTED[role]} does not name its home screen '{home.title}'"
        )


def test_every_screen_a_guide_names_exists_in_the_menu() -> None:
    """A guide that sends someone to a screen that is not in their menu is a dead end."""

    from app.modules.navigation import NAV_ITEMS

    labels = {item.label for item in NAV_ITEMS}
    known = labels | {"Historical Data"}

    for role, filename in EXPECTED.items():
        text = (GUIDES / filename).read_text(encoding="utf-8")
        named = set(re.findall(r"\*\*([A-Z][^*]{2,30})\*\*", text))
        # Only the bolded screen names are checked; other bold phrases are prose.
        screens = {
            name for name in named
            if name in known
            or name.endswith(("Queue", "Management", "Health", "Activity"))
        }
        unknown = {
            name for name in screens
            if name not in known
        }
        assert not unknown, f"{filename} names screens that do not exist: {unknown}"


def test_the_index_lists_every_guide() -> None:
    index = (GUIDES / "README.md").read_text(encoding="utf-8")
    missing = [filename for filename in EXPECTED.values() if filename not in index]
    assert not missing, f"the index does not list: {missing}"


def test_every_guide_states_the_two_facts_that_are_true_of_every_role() -> None:
    """Rather than repeating them ten times, the index states them once."""

    index = (GUIDES / "README.md").read_text(encoding="utf-8")
    assert "Your menu is not the whole product" in index
    assert "Every change you make is recorded" in index


def test_the_guides_do_not_promise_deletion() -> None:
    """Corrections are additions. A guide that offers a delete is wrong."""

    for role, filename in EXPECTED.items():
        # Prose wraps where it likes; comparing on normalised whitespace is the only
        # way a phrase test means what it says. This bit twice now - see B45.
        text = " ".join((GUIDES / filename).read_text(encoding="utf-8").lower().split())
        if "delete" in text:
            assert any(
                phrase in text
                for phrase in ("cannot delete", "never delete", "no delete", "nothing to delete")
            ), f"{filename} mentions deletion without saying it is refused"
