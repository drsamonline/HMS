"""
HHMS Investigation Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.repositories.base import RepositoryBase


class InvestigationRepository(
    RepositoryBase[Investigation],
):
    """Persistence operations for investigations."""

    def __init__(self) -> None:
        super().__init__(Investigation)

    async def get_by_id(
        self,
        db: AsyncSession,
        investigation_id: int,
    ) -> Investigation | None:
        return await db.get(
            Investigation,
            investigation_id,
        )

    async def list_all(
        self,
        db: AsyncSession,
        *,
        patient_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Investigation]:
        statement = select(Investigation)

        if patient_id is not None:
            statement = statement.where(
                Investigation.patient_id == patient_id,
            )

        if status is not None:
            statement = statement.where(
                Investigation.investigation_status
                == status,
            )

        result = await db.execute(
            statement
            .order_by(
                Investigation.requested_datetime.desc(),
                Investigation.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


investigation_repository = InvestigationRepository()


__all__ = [
    "InvestigationRepository",
    "investigation_repository",
]