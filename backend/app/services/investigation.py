"""
HHMS Investigation Service.

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
from app.models.investigation import Investigation
from app.models.patient import Patient
from app.models.visit import Visit
from app.repositories.investigation import (
    InvestigationRepository,
    investigation_repository,
)
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
)


class InvestigationService:
    """Business workflows for laboratory investigations."""

    def __init__(
        self,
        repository: InvestigationRepository | None = None,
    ) -> None:
        self.repository = (
            repository or investigation_repository
        )

    async def get(
        self,
        db: AsyncSession,
        investigation_id: int,
    ) -> Investigation:
        investigation = (
            await self.repository.get_by_id(
                db,
                investigation_id,
            )
        )

        if investigation is None:
            raise ResourceNotFoundException(
                "Investigation not found."
            )

        return investigation

    async def list(
        self,
        db: AsyncSession,
        *,
        patient_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Investigation]:
        return await self.repository.list_all(
            db,
            patient_id=patient_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def _validate_encounter(
        self,
        db: AsyncSession,
        data: InvestigationCreate,
    ) -> None:
        if (
            data.visit_id is None
            and data.admission_id is None
        ):
            raise BusinessRuleException(
                "An investigation must be associated "
                "with a visit or admission."
            )

        if (
            data.visit_id is not None
            and data.admission_id is not None
        ):
            raise BusinessRuleException(
                "An investigation cannot be associated "
                "with both a visit and an admission."
            )

        patient = await db.get(
            Patient,
            data.patient_id,
        )

        if patient is None:
            raise ResourceNotFoundException(
                "Patient not found."
            )

        if data.visit_id is not None:
            visit = await db.get(
                Visit,
                data.visit_id,
            )

            if visit is None:
                raise ResourceNotFoundException(
                    "Visit not found."
                )

            if visit.patient_id != data.patient_id:
                raise BusinessRuleException(
                    "The selected visit does not belong "
                    "to the selected patient."
                )

        if data.admission_id is not None:
            admission = await db.get(
                Admission,
                data.admission_id,
            )

            if admission is None:
                raise ResourceNotFoundException(
                    "Admission not found."
                )

            if (
                admission.patient_id
                != data.patient_id
            ):
                raise BusinessRuleException(
                    "The selected admission does not belong "
                    "to the selected patient."
                )

    async def create(
        self,
        db: AsyncSession,
        data: InvestigationCreate,
    ) -> Investigation:
        await self._validate_encounter(
            db,
            data,
        )

        now = datetime.now(timezone.utc)

        investigation = Investigation(
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            admission_id=data.admission_id,
            investigation_number="PENDING",
            investigation_name=(
                data.investigation_name
            ),
            requested_by=data.requested_by,
            requested_datetime=(
                data.requested_datetime
            ),
            investigation_status=(
                data.investigation_status
            ),
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            investigation = await self.repository.add(
                db,
                investigation,
            )

            investigation.investigation_number = (
                f"LAB-{investigation.id:06d}"
            )

            await self.repository.update(
                db,
                investigation,
            )

            await db.commit()

            return investigation

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create investigation."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create investigation."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        investigation_id: int,
        data: InvestigationUpdate,
    ) -> Investigation:
        investigation = await self.get(
            db,
            investigation_id,
        )

        if (
            investigation.investigation_status
            == "cancelled"
        ):
            raise BusinessRuleException(
                "A cancelled investigation cannot be modified."
            )

        values = data.model_dump(
            exclude_unset=True,
        )

        if not values:
            return investigation

        if (
            values.get("investigation_status")
            == "cancelled"
        ):
            if (
                investigation.investigation_status
                == "completed"
            ):
                raise BusinessRuleException(
                    "A completed investigation cannot "
                    "be cancelled."
                )

        for field, value in values.items():
            setattr(
                investigation,
                field,
                value,
            )

        investigation.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            await db.commit()
            await db.refresh(investigation)

            return investigation

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update investigation."
            ) from exc

    async def cancel(
        self,
        db: AsyncSession,
        investigation_id: int,
    ) -> Investigation:
        return await self.update(
            db,
            investigation_id,
            InvestigationUpdate(
                investigation_status="cancelled",
            ),
        )


investigation_service = InvestigationService()


__all__ = [
    "InvestigationService",
    "investigation_service",
]