"""
HHMS Bed Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bed import Bed
from app.repositories.base import RepositoryBase


class BedRepository(RepositoryBase[Bed]):
    """Persistence operations for inpatient beds."""

    def __init__(self) -> None:
        super().__init__(Bed)

    async def get_by_id(
        self,
        db: AsyncSession,
        bed_id: int,
    ) -> Bed | None:
        return await db.get(
            Bed,
            bed_id,
        )

    async def get_by_number(
        self,
        db: AsyncSession,
        bed_number: str,
    ) -> Bed | None:
        result = await db.execute(
            select(Bed).where(
                Bed.bed_number == bed_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_beds(
        self,
        db: AsyncSession,
        *,
        ward: str | None = None,
        occupancy_status: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Bed]:
        statement = select(Bed)

        if ward is not None:
            statement = statement.where(
                Bed.ward == ward,
            )

        if occupancy_status is not None:
            statement = statement.where(
                Bed.occupancy_status
                == occupancy_status,
            )

        if active_only:
            statement = statement.where(
                Bed.is_active.is_(True),
            )

        result = await db.execute(
            statement
            .order_by(
                Bed.ward.asc().nullslast(),
                Bed.room_number.asc().nullslast(),
                Bed.bed_number.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


bed_repository = BedRepository()


__all__ = [
    "BedRepository",
    "bed_repository",
]