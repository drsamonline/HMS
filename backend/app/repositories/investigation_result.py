"""
HHMS Investigation Result Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation_result import (
    InvestigationResult,
)
from app.repositories.base import RepositoryBase


class InvestigationResultRepository(
    RepositoryBase[InvestigationResult],
):
    """Persistence operations for investigation results."""

    def __init__(self) -> None:
        super().__init__(
            InvestigationResult,
        )

    async def get_by_id(
        self,
        db: AsyncSession,
        result_id: int,
    ) -> InvestigationResult | None:
        return await db.get(
            InvestigationResult,
            result_id,
        )

    async def get_by_investigation(
        self,
        db: AsyncSession,
        investigation_id: int,
    ) -> InvestigationResult | None:
        result = await db.execute(
            select(
                InvestigationResult
            ).where(
                InvestigationResult.investigation_id
                == investigation_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_all(
        self,
        db: AsyncSession,
        *,
        investigation_id: int | None = None,
        report_status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InvestigationResult]:
        statement = select(
            InvestigationResult
        )

        if investigation_id is not None:
            statement = statement.where(
                InvestigationResult.investigation_id
                == investigation_id,
            )

        if report_status is not None:
            statement = statement.where(
                InvestigationResult.report_status
                == report_status,
            )

        result = await db.execute(
            statement
            .order_by(
                InvestigationResult.result_datetime.desc(),
                InvestigationResult.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


investigation_result_repository = (
    InvestigationResultRepository()
)


__all__ = [
    "InvestigationResultRepository",
    "investigation_result_repository",
]