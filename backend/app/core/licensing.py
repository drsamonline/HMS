"""
Licensing: how a copy of the software learns what it is allowed to run.

The question this answers is the one that decides whether a free tier means anything.
An edition set by an environment variable is a price list with no lock on it: anyone
who can edit a text file can have the whole product. That is fine for an honour system
and useless for a product whose paid tiers are the revenue.

WHAT THIS IS

A licence is a signed token. The vendor holds a private key and signs a short statement
- which edition, for whom, until when. The software ships the matching public key and
can verify the statement without contacting anybody.

That matters more than it sounds. A hospital LAN frequently has no internet, or a
firewall that would make an activation server unreachable. A licence that needs a
phone-home is a licence that fails in exactly the buildings that buy the software.

WHAT THIS IS NOT

It is not copy protection. Somebody determined enough can patch the check out of a
binary, and no scheme in this file changes that. What it does is make the honest case
honest and the dishonest case deliberate: a clinic running the hospital edition without
a licence is not confused about what it bought.

HOW IT RESOLVES

    a valid licence          its edition, until it expires
    no licence at all        the free edition
    an expired licence       its edition, with a warning, for a grace period -
                             because bricking a hospital's records on an anniversary
                             is not a business model, it is a hazard
    a tampered licence       the free edition, and the reason is logged at error level

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import jwt

from app.core.editions import DEFAULT_EDITION, Edition, edition_for

logger = logging.getLogger("hhms.licensing")

#: The vendor's public key, shipped with the software. Overridden by the environment
#: so a test can verify against a key it generated itself.
PUBLIC_KEY_ENV = "HHMS_LICENCE_PUBLIC_KEY"

#: Where the licence file lives, relative to the application root.
LICENCE_FILE = Path("data") / "licence.key"

#: How long an expired licence keeps working. Thirty days is long enough for a renewal
#: to be chased and short enough that it is not the same as no expiry at all.
GRACE_DAYS = 30

ALGORITHM = "RS256"


@dataclass(frozen=True)
class Licence:
    """A verified licence."""

    edition: Edition
    customer: str
    issued_at: datetime | None
    expires_at: datetime | None
    reference: str | None

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and datetime.now(UTC) > self.expires_at

    @property
    def in_grace(self) -> bool:
        if not self.expired or self.expires_at is None:
            return False
        return (datetime.now(UTC) - self.expires_at).days <= GRACE_DAYS

    def summary(self) -> dict:
        return {
            "edition": self.edition.code,
            "edition_name": self.edition.name,
            "customer": self.customer,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "expired": self.expired,
            "in_grace": self.in_grace,
            "reference": self.reference,
        }


@dataclass(frozen=True)
class Resolution:
    """What the software decided it may run, and why."""

    edition: Edition
    licence: Licence | None
    reason: str
    warning: str | None = None


def _public_key() -> str | None:
    """The key to verify against: the environment's, else the one shipped."""

    override = os.environ.get(PUBLIC_KEY_ENV)
    if override:
        return override

    from app.core.licence_keys import RELEASE_PUBLIC_KEY

    return RELEASE_PUBLIC_KEY or None


def verify(token: str) -> Licence:
    """Verify a signed licence token, or raise.

    Raises ``ValueError`` with a reason a human can act on. The reasons are deliberately
    distinct: an expired licence and a forged one are different conversations.
    """

    key = _public_key()
    if not key:
        raise ValueError(
            "This build has no licence public key, so no licence can be verified. "
            "The release was built without one."
        )

    try:
        # ``verify_exp`` is off deliberately. PyJWT would reject an expired licence
        # before this module can apply its grace period, and the grace period is the
        # difference between a renewal reminder and locking a hospital out of its own
        # records. Expiry is checked in ``Licence.expired`` and acted on in ``resolve``.
        claims = jwt.decode(
            token,
            key,
            algorithms=[ALGORITHM],
            options={"verify_aud": False, "verify_exp": False},
        )
    except jwt.InvalidSignatureError as exc:
        raise ValueError(
            "The licence signature does not match this build's public key. It was "
            "either issued for different software or altered."
        ) from exc
    except jwt.PyJWTError as exc:
        raise ValueError(f"The licence could not be read: {exc}") from exc

    edition_code = claims.get("edition")
    if not edition_code:
        raise ValueError("The licence does not say which edition it grants.")
    if edition_code not in {e.code for e in _all_editions()}:
        raise ValueError(f"The licence grants an edition this software does not have: {edition_code}.")

    def _when(name: str) -> datetime | None:
        value = claims.get(name)
        if not value:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, UTC)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    return Licence(
        edition=edition_for(edition_code),
        customer=str(claims.get("customer") or "unnamed"),
        issued_at=_when("iat"),
        expires_at=_when("exp"),
        reference=claims.get("ref"),
    )


def _all_editions():
    from app.core.editions import EDITIONS

    return EDITIONS.values()


def read_token(root: Path | None = None) -> str | None:
    """The licence token on disk, if there is one."""

    path = (root or Path.cwd()) / LICENCE_FILE
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def resolve(root: Path | None = None) -> Resolution:
    """What this installation may run.

    Order: a licence file, then the environment, then the free edition. The licence wins
    because it is the thing that was paid for; the environment is an escape hatch for a
    deployment that has no licence yet.
    """

    token = read_token(root)
    if token:
        try:
            licence = verify(token)
        except ValueError as exc:
            logger.error("Licence rejected: %s - falling back to the free edition.", exc)
            return Resolution(
                edition=edition_for(DEFAULT_EDITION),
                licence=None,
                reason="rejected",
                warning=f"The licence on this server was rejected: {exc}",
            )

        if licence.expired and not licence.in_grace:
            logger.error(
                "Licence for %s expired on %s - grace period over, falling back to %s.",
                licence.customer,
                licence.expires_at,
                DEFAULT_EDITION,
            )
            return Resolution(
                edition=edition_for(DEFAULT_EDITION),
                licence=licence,
                reason="expired",
                warning=(
                    f"The licence for {licence.customer} expired on "
                    f"{licence.expires_at:%d %B %Y} and the grace period is over. "
                    "The software is running the free edition until it is renewed."
                ),
            )

        if licence.expired:
            logger.warning(
                "Licence for %s expired on %s - running in the %d-day grace period.",
                licence.customer,
                licence.expires_at,
                GRACE_DAYS,
            )
            return Resolution(
                edition=licence.edition,
                licence=licence,
                reason="grace",
                warning=(
                    f"The licence for {licence.customer} expired on "
                    f"{licence.expires_at:%d %B %Y}. The software keeps working for "
                    f"{GRACE_DAYS} days from then while it is renewed."
                ),
            )

        return Resolution(
            edition=licence.edition,
            licence=licence,
            reason="licensed",
        )

    env_edition = os.environ.get("HHMS_EDITION")
    if env_edition:
        return Resolution(
            edition=edition_for(env_edition),
            licence=None,
            reason="environment",
            warning=(
                "This installation's edition is set by the HHMS_EDITION environment "
                "variable rather than by a licence. That is fine for an evaluation and "
                "is not how a sold copy should be configured."
            ),
        )

    return Resolution(
        edition=edition_for(DEFAULT_EDITION),
        licence=None,
        reason="unlicensed",
    )


def current_edition() -> Edition:
    """The edition this process runs, resolved once at first use."""

    return resolve().edition


__all__ = [
    "ALGORITHM",
    "GRACE_DAYS",
    "LICENCE_FILE",
    "PUBLIC_KEY_ENV",
    "Licence",
    "Resolution",
    "current_edition",
    "read_token",
    "resolve",
    "verify",
]
