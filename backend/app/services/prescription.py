"""
HHMS Prescription Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.repositories.prescription import (
    PrescriptionRepository,
    prescription_repository,
)
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
)


class PrescriptionService:
    """Business workflows for prescriptions."""

    def __init__(
        self,
        repository: PrescriptionRepository | None = None,
    ) -> None:
        self.repository = (
            repository or prescription_repository
        )

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        prescription_id: int,
    ) -> Prescription:
        prescription = await self.repository.get_by_id(
            db,
            prescription_id,
        )

        if prescription is None:
            raise ResourceNotFoundException(
                "Prescription not found."
            )

        return prescription

    async def get_items(
        self,
        db: AsyncSession,
        *,
        prescription_id: int,
    ) -> list[PrescriptionItem]:
        await self.get_by_id(
            db,
            prescription_id=prescription_id,
        )

        return await self.repository.get_items(
            db,
            prescription_id=prescription_id,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        prescription_in: PrescriptionCreate,
    ) -> Prescription:
        now = datetime.now(timezone.utc)

        prescription = Prescription(
            visit_id=prescription_in.visit_id,
            prescribed_by=prescription_in.prescribed_by,
            prescription_datetime=(
                prescription_in.prescription_datetime
            ),
            diagnosis=prescription_in.diagnosis,
            clinical_notes=prescription_in.clinical_notes,
            treatment_plan=prescription_in.treatment_plan,
            prescription_number="PENDING",
            created_at=now,
            updated_at=now,
        )

        try:
            prescription = await self.repository.add(
                db,
                prescription,
            )

            prescription.prescription_number = (
                f"RX-{prescription.id:06d}"
            )

            for item_data in prescription_in.items:
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    **item_data.model_dump(),
                    created_at=now,
                    updated_at=now,
                )

                db.add(item)

            await db.flush()
            await db.commit()
            await db.refresh(prescription)

            return prescription

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create prescription because "
                "a related record is invalid or duplicated."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create prescription."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        prescription_id: int,
        prescription_in: PrescriptionUpdate,
    ) -> Prescription:
        prescription = await self.get_by_id(
            db,
            prescription_id=prescription_id,
        )

        update_data = prescription_in.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return prescription

        for field, value in update_data.items():
            setattr(
                prescription,
                field,
                value,
            )

        prescription.updated_at = datetime.now(
            timezone.utc,
        )

        try:
            prescription = await self.repository.update(
                db,
                prescription,
            )

            await db.commit()

            return prescription

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update prescription."
            ) from exc


prescription_service = PrescriptionService()


__all__ = [
    "PrescriptionService",
    "prescription_service",
]