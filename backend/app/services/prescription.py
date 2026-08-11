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
    """Business operations for clinical prescriptions."""

    def __init__(
        self,
        repository: PrescriptionRepository | None = None,
    ) -> None:
        self.repository = (
            repository or prescription_repository
        )

    async def get(
        self,
        db: AsyncSession,
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
        prescription_id: int,
    ) -> list[PrescriptionItem]:
        await self.get(
            db,
            prescription_id,
        )

        return await self.repository.get_items(
            db,
            prescription_id,
        )

    async def create(
        self,
        db: AsyncSession,
        data: PrescriptionCreate,
    ) -> Prescription:
        now = datetime.now(timezone.utc)

        prescription = Prescription(
            visit_id=data.visit_id,
            prescription_number="PENDING",
            diagnosis=data.diagnosis,
            clinical_notes=data.clinical_notes,
            treatment_plan=data.treatment_plan,
            prescribed_by=data.prescribed_by,
            prescription_datetime=data.prescription_datetime,
            created_at=now,
            updated_at=now,
        )

        try:
            db.add(prescription)
            await db.flush()

            prescription.prescription_number = (
                f"RX-{prescription.id:06d}"
            )

            for item_data in data.items:
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_id=item_data.medicine_id,
                    dosage=item_data.dosage,
                    frequency=item_data.frequency,
                    duration_days=item_data.duration_days,
                    instructions=item_data.instructions,
                    quantity=item_data.quantity,
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
                "Prescription could not be created because "
                "a referenced record is invalid or duplicated."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Prescription creation failed."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        prescription_id: int,
        data: PrescriptionUpdate,
    ) -> Prescription:
        prescription = await self.get(
            db,
            prescription_id,
        )

        values = data.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(
                prescription,
                field,
                value,
            )

        prescription.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            await db.flush()
            await db.commit()
            await db.refresh(prescription)

            return prescription

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Prescription update failed."
            ) from exc


prescription_service = PrescriptionService()


__all__ = [
    "PrescriptionService",
    "prescription_service",
]