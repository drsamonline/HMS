"""Repository for departmental service activities."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.service_activity import ServiceActivity
from app.repositories.base import RepositoryBase


class ServiceActivityRepository(RepositoryBase[ServiceActivity]):
    def __init__(self) -> None:
        super().__init__(ServiceActivity)

    async def list_recent(
        self, db: AsyncSession, *, patient_id: int | None = None,
        department_id=None, skip: int = 0, limit: int = 100
    ) -> list[ServiceActivity]:
        stmt = select(ServiceActivity)
        if patient_id is not None:
            stmt = stmt.where(ServiceActivity.patient_id == patient_id)
        if department_id is not None:
            stmt = stmt.where(ServiceActivity.department_id == department_id)
        result = await db.execute(
            stmt.order_by(ServiceActivity.activity_datetime.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())


service_activity_repository = ServiceActivityRepository()

__all__ = ["ServiceActivityRepository", "service_activity_repository"]
