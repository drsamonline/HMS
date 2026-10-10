"""HHMS Diet Chart repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diet_chart import DietChart
from app.repositories.base import RepositoryBase


class DietChartRepository(RepositoryBase[DietChart]):
    def __init__(self) -> None:
        super().__init__(DietChart)

    async def get_by_id(self, db: AsyncSession, object_id: int) -> DietChart | None:
        return await db.get(DietChart, object_id)

    async def list_by_admission(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[DietChart]:
        result = await db.execute(
            select(DietChart).where(DietChart.admission_id == admission_id).order_by(DietChart.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


diet_chart_repository = DietChartRepository()

__all__ = ["DietChartRepository", "diet_chart_repository"]
