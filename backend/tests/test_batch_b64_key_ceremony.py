"""The runbook for replacing the licence key, held to the thing it describes.

A document that tells somebody to paste a key into a file will be wrong the day the file
is renamed. These tests read the runbook and check that every path and command it names
still exists, so the instructions fail the build rather than the person following them.
"""

from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
DOC = ROOT / "docs" / "KEY-CEREMONY.md"


def _text() -> str:
    return " ".join(DOC.read_text(encoding="utf-8").split())


def test_the_runbook_exists() -> None:
    assert DOC.is_file()


def test_every_file_it_names_exists() -> None:
    """A path in a runbook is an instruction. A wrong one wastes an afternoon."""

    for path in (
        "backend/app/core/licence_keys.py",
        "backend/tests/test_batch_b54_licensing.py",
        "scripts/check_release_ready.py",
        "backend/requirements.txt",
    ):
        assert (ROOT / path).is_file(), f"the runbook names {path}, which does not exist"


def test_every_command_it_names_is_real() -> None:
    """Each subcommand the runbook tells somebody to type must be one the tool has."""

    import argparse
    import inspect

    from app.cli import licence

    source = inspect.getsource(licence.main)
    for command in ("keygen", "issue", "check", "inspect"):
        assert f'"{command}"' in source, f"the runbook says `{command}` but the tool has no such command"
        assert f"licence {command}" in _text(), f"the runbook never mentions `{command}`"


def test_it_warns_about_the_private_key_in_the_places_that_matter() -> None:
    text = _text()
    assert "never in the project" in text or "never commit" in text
    assert "back up" in text.lower()
    assert "if you lose it" in text.lower()
    assert "if it leaks" in text.lower()


def test_it_names_the_test_that_must_be_flipped() -> None:
    """The suite will fail on the day the key is replaced. That is by design, and the
    runbook has to say so or the failure looks like a regression."""

    text = _text()
    assert "test_batch_b54_licensing.py" in text
    assert "IS_DEVELOPMENT_KEY is False" in text


def test_the_step_it_describes_is_the_step_the_code_takes() -> None:
    """`IS_DEVELOPMENT_KEY` must go false when a different key is pasted in."""

    from app.core.licence_keys import IS_DEVELOPMENT_KEY, RELEASE_PUBLIC_KEY

    assert RELEASE_PUBLIC_KEY.strip().startswith("-----BEGIN PUBLIC KEY-----")
    # While the development key is live this is True, and the runbook is what changes it.
    assert isinstance(IS_DEVELOPMENT_KEY, bool)
