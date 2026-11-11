"""
Issuing certificates, and keeping them for as long as the Code of Ethics requires.

Regulation 7(1): a copy of every medical certificate kept for at least three years.
The retention date is computed at issue and stored, so a later settings change
cannot shorten an obligation already made.

Regulation 27: a written case statement with a referral. A referral without one is
refused rather than saved and corrected later - the case statement is the thing the
referring doctor is being asked to provide.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, DuplicateResourceException, ResourceNotFoundException
from app.models.medical_certificate import CERTIFICATE_TYPES, MedicalCertificate
from app.models.patient import Patient
from app.services import audit

#: Regulation 7(1). Stored on the row at issue; this constant is the default.
RETENTION_YEARS = 3


def _add_years(moment: datetime, years: int) -> datetime:
    """Add whole years, clamping 29 February to the 28th."""

    try:
        return moment.replace(year=moment.year + years)
    except ValueError:
        return moment.replace(year=moment.year + years, day=28)


async def issue(
    db: AsyncSession,
    *,
    patient_id: int,
    certificate_type: str,
    certificate_number: str,
    content: str,
    issued_by: int,
    issued_at: datetime | None = None,
    case_statement: str | None = None,
) -> MedicalCertificate:
    """Issue a certificate, dated and given its retention date."""

    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise ResourceNotFoundException("Patient not found.")

    if certificate_type not in CERTIFICATE_TYPES:
        raise BusinessRuleException(
            f"Certificate type must be one of: {', '.join(CERTIFICATE_TYPES)}."
        )
    if not content.strip():
        raise BusinessRuleException("A certificate needs its text; an empty one certifies nothing.")

    # Regulation 27. Enforced here because this is the only moment the referring
    # doctor still has the case in front of them.
    if certificate_type == "referral" and not (case_statement or "").strip():
        raise BusinessRuleException(
            "A referral needs a written case statement. The NCH Code of Ethics "
            "requires one with every referral."
        )

    existing = (
        await db.execute(
            select(MedicalCertificate).where(
                MedicalCertificate.certificate_number == certificate_number
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise DuplicateResourceException("That certificate number has already been issued.")

    issued = issued_at or datetime.now(UTC)
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=UTC)

    certificate = MedicalCertificate(
        patient_id=patient_id,
        certificate_type=certificate_type,
        certificate_number=certificate_number,
        issued_at=issued,
        issued_by=issued_by,
        content=content.strip(),
        case_statement=case_statement.strip() if case_statement else None,
        retention_until=_add_years(issued, RETENTION_YEARS),
    )
    db.add(certificate)
    await db.flush()

    await audit.record(
        db,
        activity="certificate.issue",
        entity_name="MedicalCertificate",
        entity_id=certificate.id,
        after={
            "certificate_number": certificate_number,
            "type": certificate_type,
            "retention_until": certificate.retention_until.isoformat(),
        },
    )
    return certificate


async def list_certificates(
    db: AsyncSession, *, patient_id: int | None = None, limit: int = 100
) -> list[MedicalCertificate]:
    query = (
        select(MedicalCertificate)
        .order_by(MedicalCertificate.issued_at.desc())
        .limit(limit)
    )
    if patient_id is not None:
        query = query.where(MedicalCertificate.patient_id == patient_id)
    return list((await db.execute(query)).scalars().all())


async def retention_report(db: AsyncSession) -> dict:
    """What the register holds, and what is past its retention date.

    Past retention does not mean delete: three years is a floor, not a ceiling. The
    report says what may be archived, never what may be removed.
    """

    now = datetime.now(UTC)
    total = (
        await db.execute(select(func.count()).select_from(MedicalCertificate))
    ).scalar_one()
    expired = (
        await db.execute(
            select(func.count())
            .select_from(MedicalCertificate)
            .where(MedicalCertificate.retention_until < now)
        )
    ).scalar_one()
    referrals_without_statement = (
        await db.execute(
            select(func.count())
            .select_from(MedicalCertificate)
            .where(
                MedicalCertificate.certificate_type == "referral",
                (MedicalCertificate.case_statement.is_(None))
                | (func.trim(MedicalCertificate.case_statement) == ""),
            )
        )
    ).scalar_one()

    return {
        "total": total,
        "past_retention": expired,
        "referrals_without_statement": referrals_without_statement,
    }


__all__ = ["RETENTION_YEARS", "issue", "list_certificates", "retention_report"]
