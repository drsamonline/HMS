"""
The registrations the *institution* holds, as distinct from the ones a practitioner holds.

A doctor's registration number lets that doctor practise. The clinic's clinical
establishment registration lets the premises operate. They are issued by different
bodies, they expire on different dates, and an inspector asks for both.

Keeping them apart matters: a hospital with twelve doctors has one BMW authorisation
and one clinical establishment certificate, not twelve of each. Folding them into the
user record would have meant twelve copies of the same number and no way to answer
"is our BMW authorisation current".

Which registrations apply depends on where the clinic is and what it does. The
Clinical Establishments Act, 2010 has been adopted by some states and not others, and
several states run their own law; the Bio-Medical Waste Rules, 2016 apply to anyone
generating such waste whatever the quantity. So the register records what the hospital
holds rather than demanding a fixed list, and the readiness report says which of the
applicable ones are missing or expiring.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


#: The kinds a hospital or clinic may need. Not all apply to every establishment - the
#: register records what is held, and the readiness report names the gaps.
REGISTRATION_KINDS: tuple[tuple[str, str, str], ...] = (
    (
        "clinical_establishment",
        "Clinical establishment registration",
        "District registering authority, under the Clinical Establishments Act, 2010 "
        "where the state has adopted it, or the state's own equivalent law. Required "
        "wherever that law applies, including single-doctor clinics.",
    ),
    (
        "biomedical_waste",
        "Bio-medical waste authorisation",
        "State Pollution Control Board or Committee, in Form II under the Bio-Medical "
        "Waste Management Rules, 2016. Required of anyone generating such waste, "
        "whatever the quantity.",
    ),
    (
        "shop_establishment",
        "Shop and establishment registration",
        "State labour department or the local municipal body, where that law applies.",
    ),
    (
        "trade_licence",
        "Trade licence",
        "Local municipal body, in the cities that require one.",
    ),
    (
        "pollution_consent",
        "Pollution consent (water and air)",
        "State Pollution Control Board, for establishments above the thresholds in the "
        "Water and Air Acts. Not every clinic needs one.",
    ),
    (
        "fire_safety",
        "Fire safety certificate",
        "Local fire authority, where the premises are above the size that requires one.",
    ),
    (
        "lift_licence",
        "Lift licence",
        "State electrical or lift inspectorate, where a lift is installed.",
    ),
    (
        "generator_consent",
        "Generator consent",
        "State Pollution Control Board, where a generator is installed.",
    ),
    (
        "nabh",
        "NABH accreditation",
        "Quality Council of India / NABH. Voluntary - a clinic or hospital may operate "
        "without it, and this software does not require it.",
    ),
    (
        "qci",
        "QCI accreditation",
        "Quality Council of India, for colleges and teaching hospitals with attached "
        "facilities. Rarely applicable to a private clinic.",
    ),
)

KIND_CODES = tuple(code for code, _label, _note in REGISTRATION_KINDS)

#: The kinds the law requires of an ordinary practice, and therefore the ones the
#: readiness report asks about by default.
MANDATORY_BY_DEFAULT = ("clinical_establishment", "biomedical_waste")


class InstituteRegistration(Base):
    """One registration held by the institution."""

    __tablename__ = "InstituteRegistration"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    kind: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    number: Mapped[str] = mapped_column(String(80), nullable=False)
    authority: Mapped[str | None] = mapped_column(String(160), nullable=True)

    issued_on: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: Nullable on purpose: some registrations are issued without an expiry, and a date
    #: invented to fill the field would be worse than an empty one.
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    #: True when this installation says the registration applies to it. A clinic with
    #: no lift does not need a lift licence, and the software should not nag about it.
    applies: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


__all__ = [
    "KIND_CODES",
    "MANDATORY_BY_DEFAULT",
    "REGISTRATION_KINDS",
    "InstituteRegistration",
]
