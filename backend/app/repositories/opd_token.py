"""
HHMS OPD Token Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opd_token import OPDToken
from app.repositories.base import RepositoryBase


class OPDTokenRepository(RepositoryBase[OPDToken]):
    """Persistence operations for OPD tokens."""

    def __init__(self) -> None:
        super().__init__(OPDToken)

    async def get_by_id(
        self,
        db: AsyncSession,
        token_id: int,
    ) -> OPDToken | None:
        return await db.get(
            OPDToken,
            token_id,
        )

    async def get_next_token_number(
        self,
        db: AsyncSession,
        *,
        queue_date: date,
    ) -> int:
        result = await db.execute(
            select(
                func.coalesce(
                    func.max(OPDToken.token_number),
                    0,
                ) + 1
            ).where(
                OPDToken.queue_date == queue_date,
            )
        )

        return int(result.scalar_one())

    async def get_by_visit(
        self,
        db: AsyncSession,
        *,
        visit_id: int,
    ) -> OPDToken | None:
        result = await db.execute(
            select(OPDToken).where(
                OPDToken.visit_id == visit_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_date(
        self,
        db: AsyncSession,
        *,
        queue_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OPDToken]:
        result = await db.execute(
            select(OPDToken)
            .where(
                OPDToken.queue_date == queue_date,
            )
            .order_by(OPDToken.token_number.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


opd_token_repository = OPDTokenRepository()


__all__ = [
    "OPDTokenRepository",
    "opd_token_repository",
]