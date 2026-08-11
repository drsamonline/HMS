"""
HHMS Dispensing Service.
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
from app.models.dispense_record import DispenseRecord
from app.repositories.dispense import (
    DispenseRepository,
    dispense_repository,
)
from app.schemas.dispense import DispenseCreate


class DispenseService:
    """Business operations for pharmacy dispensing."""

    def __init__(
        self,
        repository: DispenseRepository | None = None,
    ) -> None:
        self.repository = (
            repository or dispense_repository
        )

    async def get(
        self,
        db: AsyncSession,
        dispense_id: int,
    ) -> DispenseRecord:
        record = await self.repository.get_by_id(
            db,
            dispense_id,
        )

        if record is None:
            raise ResourceNotFoundException(
                "Dispense record not found."
            )

        return record

    async def list_by_prescription_item(
        self,
        db: AsyncSession,
        prescription_item_id: int,
    ) -> list[DispenseRecord]:
        return await self.repository.list_by_prescription_item(
            db,
            prescription_item_id,
        )

    async def create(
        self,
        db: AsyncSession,
        data: DispenseCreate,
    ) -> DispenseRecord:
        now = datetime.now(timezone.utc)

        record = DispenseRecord(
            **data.model_dump(),
            dispense_date=now,
            created_at=now,
            updated_at=now,
        )

        try:
            db.add(record)
            await db.commit()
            await db.refresh(record)

            return record

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Dispensing failed because a referenced "
                "record is invalid or duplicated."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create dispense record."
            ) from exc


dispense_service = DispenseService()


__all__ = [
    "DispenseService",
    "dispense_service",
]