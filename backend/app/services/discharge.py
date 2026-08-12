"""
HHMS Discharge Service.

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
from app.models.discharge import Discharge
from app.repositories.discharge import (
    DischargeRepository,
    discharge_repository,
)
from app.schemas.discharge import (
    DischargeCreate,
)


class DischargeService:
    """Business workflows for inpatient discharge."""

    def __init__(
        self,
        repository: DischargeRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or discharge_repository
        )

    async def get(
        self,
        db: AsyncSession,
        discharge_id: int,
    ) -> Discharge:
        discharge = (
            await self.repository.get_by_id(
                db,
                discharge_id,
            )
        )

        if discharge is None:
            raise ResourceNotFoundException(
                "Discharge record not found."
            )

        return discharge

    async def get_by_admission(
        self,
        db: AsyncSession,
        admission_id: int,
    ) -> Discharge:
        discharge = (
            await self.repository.get_by_admission(
                db,
                admission_id,
            )
        )

        if discharge is None:
            raise ResourceNotFoundException(
                "Discharge record not found."
            )

        return discharge

    async def list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Discharge]:
        return await self.repository.list_all(
            db,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        data: DischargeCreate,
    ) -> Discharge:
        admission = await db.get(
            Admission,
            data.admission_id,
        )

        if admission is None:
            raise ResourceNotFoundException(
                "Admission not found."
            )

        if (
            admission.admission_status.lower()
            not in {
                "admitted",
                "active",
            }
        ):
            raise BusinessRuleException(
                "Only an active admission can be discharged."
            )

        existing = (
            await self.repository.get_by_admission(
                db,
                data.admission_id,
            )
        )

        if existing is not None:
            raise DuplicateResourceException(
                "This admission already has a "
                "discharge record."
            )

        bed = await db.get(
            Bed,
            admission.bed_id,
        )

        if bed is None:
            raise ResourceNotFoundException(
                "Admission bed not found."
            )

        now = datetime.now(timezone.utc)

        discharge = Discharge(
            admission_id=data.admission_id,
            discharge_number="PENDING",
            discharge_datetime=(
                data.discharge_datetime
            ),
            discharge_summary=(
                data.discharge_summary
            ),
            discharge_status=(
                data.discharge_status
            ),
            discharged_by=data.discharged_by,
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            discharge = await self.repository.add(
                db,
                discharge,
            )

            discharge.discharge_number = (
                f"DIS-{discharge.id:06d}"
            )

            await self.repository.update(
                db,
                discharge,
            )

            admission.admission_status = (
                "discharged"
            )
            admission.updated_at = now

            bed.occupancy_status = "available"
            bed.updated_at = now

            await db.commit()

            return discharge

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create discharge because "
                "the discharge record already exists "
                "or a related record is invalid."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create discharge."
            ) from exc


discharge_service = DischargeService()


__all__ = [
    "DischargeService",
    "discharge_service",
]