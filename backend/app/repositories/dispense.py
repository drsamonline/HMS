"""
HHMS Dispensing Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispense_record import DispenseRecord
from app.repositories.base import RepositoryBase


class DispenseRepository(RepositoryBase[DispenseRecord]):
    """Persistence operations for dispensing."""

    def __init__(self) -> None:
        super().__init__(DispenseRecord)

    async def get_by_id(
        self,
        db: AsyncSession,
        dispense_id: int,
    ) -> DispenseRecord | None:
        return await db.get(
            DispenseRecord,
            dispense_id,
        )

    async def list_by_prescription_item(
        self,
        db: AsyncSession,
        prescription_item_id: int,
    ) -> list[DispenseRecord]:
        result = await db.execute(
            select(DispenseRecord)
            .where(
                DispenseRecord.prescription_item_id
                == prescription_item_id
            )
            .order_by(
                DispenseRecord.dispense_date.desc()
            )
        )

        return list(result.scalars().all())


dispense_repository = DispenseRepository()


__all__ = [
    "DispenseRepository",
    "dispense_repository",
]