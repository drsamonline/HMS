"""Gate tests for trials, the advisory machine count, and the licence in the handover pack.

A trial is the easiest sale there is: the full product for a month, then a decision. Two
things have to be true for it to work - the trial has to be the *full* product, and the
hospital has to be told the date rather than discovering it.

The machine count is deliberately advisory. It records what both sides agreed so the
conversation can happen with the same number in front of them; it does not refuse
anything, because a software product that stops working because a hospital added a
second server has made an enemy of a customer who was expanding.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest


@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public


@pytest.fixture()
def licensed(monkeypatch, keys):
    _private, public = keys
    monkeypatch.setenv("HHMS_LICENCE_PUBLIC_KEY", public)
    monkeypatch.delenv("HHMS_EDITION", raising=False)
    yield


def _token(private: str, **claims) -> str:
    payload = {"customer": "Trial Clinic", "iat": int(datetime.now(UTC).timestamp())}
    payload.update(claims)
    return jwt.encode(payload, private, algorithm="RS256")


# --------------------------------------------------------------------- trial
def test_a_trial_verifies_and_is_marked_as_one(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    licence = verify(
        _token(
            private,
            edition="hospital",
            kind="trial",
            exp=int((datetime.now(UTC) + timedelta(days=30)).timestamp()),
        )
    )

    assert licence.is_trial is True
    assert licence.edition.code == "hospital", "a trial is the full product"


def test_a_paid_licence_is_not_a_trial(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    assert verify(_token(private, edition="clinic")).is_trial is False


def test_an_unknown_kind_is_refused(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    with pytest.raises(ValueError, match="does not know"):
        verify(_token(private, edition="clinic", kind="evaluation"))


def test_a_trial_expires_on_its_date(licensed, keys) -> None:
    """A trial with no expiry is a free copy with a nice name."""

    from app.core.licensing import resolve

    private, _public = keys
    expired = datetime.now(UTC) - timedelta(days=1)
    token = _token(private, edition="hospital", kind="trial", exp=int(expired.timestamp()))

    import tempfile

    with tempfile.TemporaryDirectory() as root:
        (Path(root) / "data").mkdir()
        (Path(root) / "data" / "licence.key").write_text(token)
        resolution = resolve(Path(root))

    assert resolution.reason == "grace"
    assert resolution.licence.is_trial is True


# ------------------------------------------------------------- machine count
def test_the_machine_count_is_recorded(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    assert verify(_token(private, edition="hospital", machines=3)).machines == 3


def test_a_nonsense_machine_count_is_refused(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    with pytest.raises(ValueError, match="machine count"):
        verify(_token(private, edition="hospital", machines=0))


def test_the_machine_count_never_refuses_anything() -> None:
    """Advisory. A hospital that added a second server is a customer, not a pirate."""

    source = " ".join(
        (Path(__file__).resolve().parents[1] / "app" / "core" / "licensing.py")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "Advisory only" in source

    # And nothing in the app reads it to make a decision.
    root = Path(__file__).resolve().parents[1] / "app"
    readers = [
        path.name
        for path in root.rglob("*.py")
        if "licence.machines" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert readers == [], f"something is making a decision on the machine count: {readers}"


# ------------------------------------------------------------- the tool
def test_the_tool_issues_a_trial_by_default_for_one_month(tmp_path, keys) -> None:
    import subprocess
    import sys

    private, _public = keys
    key_file = tmp_path / "private.pem"
    key_file.write_text(private)
    out = tmp_path / "trial.key"

    result = subprocess.run(
        [
            sys.executable, "-m", "app.cli.licence", "issue",
            "--private", str(key_file),
            "--edition", "hospital",
            "--customer", "Trial Clinic",
            "--trial",
            "--out", str(out),
        ],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, result.stderr
    assert "one month" not in result.stdout  # the message names the date instead
    assert "valid until" in result.stdout

    claims = jwt.decode(out.read_text(), options={"verify_signature": False})
    assert claims["kind"] == "trial"
    assert claims["exp"] > claims["iat"]


# ------------------------------------------------------------- handover pack
def test_the_handover_pack_states_the_licence() -> None:
    """A hospital should know what it bought and until when, in the pack it keeps."""

    import subprocess
    import sys
    import zipfile

    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / "handover.zip"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[2] / "scripts" / "handover_pack.py"),
             "--out", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

        readme = zipfile.ZipFile(out).read("README.md").decode()
        edition = zipfile.ZipFile(out).read("licence/EDITION.json").decode()

    import json

    assert "| Licence |" in readme
    data = json.loads(edition)
    assert "licence" in data
    assert data["licence"]["state"]
