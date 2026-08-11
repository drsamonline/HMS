"""
HHMS Admission Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.admission import Admission
from app.models.bed import Bed
from app.repositories.admission import (
    AdmissionRepository,
    admission_repository,
)
from app.schemas.admission import (
    AdmissionCreate,
    AdmissionUpdate,
)


class AdmissionService:
    """Business workflows for inpatient admissions."""

    def __init__(
        self,
        repository: AdmissionRepository | None = None,
    ) -> None:
        self.repository = (
            repository or admission_repository
        )

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        admission_id: int,
    ) -> Admission:
        admission = await self.repository.get_by_id(
            db,
            admission_id,
        )

        if admission is None:
            raise ResourceNotFoundException(
                "Admission not found."
            )

        return admission

    async def list(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        patient_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Admission]:
        return await self.repository.list_all(
            db,
            status=status,
            patient_id=patient_id,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        admission_in: AdmissionCreate,
    ) -> Admission:
        bed = await db.get(
            Bed,
            admission_in.bed_id,
        )

        if bed is None:
            raise ResourceNotFoundException(
                "Bed not found."
            )

        if not bed.is_active:
            raise BusinessRuleException(
                "Cannot admit a patient to an inactive bed."
            )

        if bed.occupancy_status.lower() not in {
            "available",
            "vacant",
            "free",
        }:
            raise BusinessRuleException(
                "Selected bed is not available."
            )

        now = datetime.now(timezone.utc)

        admission = Admission(
            patient_id=admission_in.patient_id,
            admission_number="PENDING",
            admission_datetime=(
                admission_in.admission_datetime
            ),
            bed_id=admission_in.bed_id,
            admitted_by=admission_in.admitted_by,
            admission_reason=(
                admission_in.admission_reason
            ),
            admission_status=(
                admission_in.admission_status
            ),
            remarks=admission_in.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            admission = await self.repository.add(
                db,
                admission,
            )

            admission.admission_number = (
                f"ADM-{admission.id:06d}"
            )

            await self.repository.update(
                db,
                admission,
            )

            bed.occupancy_status = "occupied"
            bed.updated_at = now

            await db.commit()

            return admission

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create admission because "
                "a related record is invalid or duplicated."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create admission."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        admission_id: int,
        admission_in: AdmissionUpdate,
    ) -> Admission:
        admission = await self.get_by_id(
            db,
            admission_id=admission_id,
        )

        update_data = admission_in.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return admission

        try:
            for field, value in update_data.items():
                setattr(
                    admission,
                    field,
                    value,
                )

            admission.updated_at = (
                datetime.now(timezone.utc)
            )

            admission = await self.repository.update(
                db,
                admission,
            )

            await db.commit()

            return admission

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update admission."
            ) from exc


admission_service = AdmissionService()


__all__ = [
    "AdmissionService",
    "admission_service",
]