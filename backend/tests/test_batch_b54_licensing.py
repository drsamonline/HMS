"""Gate tests for licensing.

The question this batch answers: how does a copy of the software learn what it may run,
when the hospital's LAN has no internet and the free tier is meant to mean something?

The answer is a signed licence file, verified against a public key shipped in the build.
These tests hold the parts that would quietly break: a forged licence must be refused, an
expired one must not brick a hospital, and the free edition must not carry the paid
feature.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest


# ------------------------------------------------------------------ key material
@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    """A throwaway keypair, so the tests never depend on the shipped key."""

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
    """Point the software at the throwaway key."""

    _private, public = keys
    monkeypatch.setenv("HHMS_LICENCE_PUBLIC_KEY", public)
    monkeypatch.delenv("HHMS_EDITION", raising=False)
    yield


def _token(private: str, **claims) -> str:
    payload = {"customer": "Test Clinic", "iat": int(datetime.now(UTC).timestamp())}
    payload.update(claims)
    return jwt.encode(payload, private, algorithm="RS256")


# ------------------------------------------------------------- verifying
def test_a_valid_licence_verifies(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    licence = verify(_token(private, edition="hospital", ref="H-001"))

    assert licence.edition.code == "hospital"
    assert licence.customer == "Test Clinic"
    assert licence.reference == "H-001"
    assert licence.expired is False


def test_a_tampered_licence_is_refused(licensed, keys) -> None:
    """The whole point: editing the payload invalidates the signature."""

    from app.core.licensing import verify

    private, _public = keys
    token = _token(private, edition="personal")
    header, payload, signature = token.split(".")

    # Rewrite the edition and keep the old signature.
    import base64

    decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))
    decoded["edition"] = "enterprise"
    forged_payload = base64.urlsafe_b64encode(
        json.dumps(decoded).encode()
    ).decode().rstrip("=")

    with pytest.raises(ValueError, match="signature does not match"):
        verify(f"{header}.{forged_payload}.{signature}")


def test_a_licence_signed_by_another_key_is_refused(licensed) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from app.core.licensing import verify

    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_private = other.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    with pytest.raises(ValueError, match="signature does not match"):
        verify(_token(other_private, edition="enterprise"))


def test_an_unknown_edition_is_refused(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    with pytest.raises(ValueError, match="does not have"):
        verify(_token(private, edition="platinum"))


def test_a_licence_without_an_edition_is_refused(licensed, keys) -> None:
    from app.core.licensing import verify

    private, _public = keys
    with pytest.raises(ValueError, match="does not say which edition"):
        verify(_token(private))


# ------------------------------------------------------------- resolving
def _write_licence(root: Path, token: str) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "data" / "licence.key").write_text(token)


def test_no_licence_means_the_free_edition(tmp_path, licensed) -> None:
    from app.core.licensing import resolve

    resolution = resolve(tmp_path)
    assert resolution.edition.code == "personal"
    assert resolution.reason == "unlicensed"


def test_a_licence_grants_its_edition(tmp_path, licensed, keys) -> None:
    from app.core.licensing import resolve

    private, _public = keys
    _write_licence(tmp_path, _token(private, edition="hospital"))

    resolution = resolve(tmp_path)
    assert resolution.edition.code == "hospital"
    assert resolution.reason == "licensed"
    assert resolution.warning is None


def test_an_expired_licence_keeps_working_for_a_grace_period(tmp_path, licensed, keys) -> None:
    """Bricking a hospital's records on an anniversary is a hazard, not a business model."""

    from app.core.licensing import GRACE_DAYS, resolve

    private, _public = keys
    expired = datetime.now(UTC) - timedelta(days=5)
    _write_licence(tmp_path, _token(private, edition="hospital", exp=int(expired.timestamp())))

    resolution = resolve(tmp_path)
    assert resolution.edition.code == "hospital", "still a hospital during grace"
    assert resolution.reason == "grace"
    assert str(GRACE_DAYS) in resolution.warning


def test_a_long_expired_licence_falls_back_to_free(tmp_path, licensed, keys) -> None:
    from app.core.licensing import GRACE_DAYS, resolve

    private, _public = keys
    expired = datetime.now(UTC) - timedelta(days=GRACE_DAYS + 5)
    _write_licence(tmp_path, _token(private, edition="hospital", exp=int(expired.timestamp())))

    resolution = resolve(tmp_path)
    assert resolution.edition.code == "personal"
    assert resolution.reason == "expired"


def test_a_forged_licence_falls_back_to_free_and_says_so(tmp_path, licensed, keys) -> None:
    from app.core.licensing import resolve

    _write_licence(tmp_path, "not.a.token")

    resolution = resolve(tmp_path)
    assert resolution.edition.code == "personal"
    assert resolution.reason == "rejected"
    assert "rejected" in resolution.warning.lower()


def test_the_environment_is_an_escape_hatch_not_the_normal_path(tmp_path, licensed, monkeypatch) -> None:
    from app.core.licensing import resolve

    monkeypatch.setenv("HHMS_EDITION", "clinic")
    resolution = resolve(tmp_path)

    assert resolution.edition.code == "clinic"
    assert resolution.reason == "environment"
    assert "not how a sold copy should be configured" in resolution.warning


def test_a_licence_beats_the_environment(tmp_path, licensed, keys, monkeypatch) -> None:
    """What was paid for wins over what somebody typed."""

    from app.core.licensing import resolve

    private, _public = keys
    monkeypatch.setenv("HHMS_EDITION", "enterprise")
    _write_licence(tmp_path, _token(private, edition="clinic"))

    assert resolve(tmp_path).edition.code == "clinic"


# ------------------------------------------------------------- the free tier
def test_the_free_edition_does_not_carry_nabh() -> None:
    """NABH is a paid feature; the free tier has to mean something."""

    from app.core.editions import PERSONAL

    assert "nabh" not in PERSONAL.modules


def test_the_paid_editions_carry_nabh() -> None:
    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL

    for edition in (CLINIC, HOSPITAL, ENTERPRISE):
        assert "nabh" in edition.modules, edition.code


def test_a_free_installation_cannot_enable_nabh(tmp_path, licensed, monkeypatch) -> None:
    """The licence decides, and the module gate reads the licence."""

    import asyncio

    from app.core.exceptions import BusinessRuleException
    from app.db.session import get_session_factory
    from app.services import module_state
    from tests._qa_harness import make_client

    monkeypatch.chdir(tmp_path)
    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                return await module_state.enable(db, "nabh")

        with pytest.raises(BusinessRuleException, match="not included"):
            asyncio.run(_go())


# ------------------------------------------------------------- the shipped key
def test_the_build_ships_a_public_key() -> None:
    """Without one, no licence can be verified and every sale is unenforceable."""

    from app.core.licence_keys import RELEASE_PUBLIC_KEY

    assert RELEASE_PUBLIC_KEY.strip().startswith("-----BEGIN PUBLIC KEY-----")


def test_the_development_key_is_marked_as_such() -> None:
    """A build that ships the development key accepts anything signed with it."""

    from app.core.licence_keys import IS_DEVELOPMENT_KEY

    assert IS_DEVELOPMENT_KEY is True, (
        "the release key has been replaced - flip this assertion with it"
    )
