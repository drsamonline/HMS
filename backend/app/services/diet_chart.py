"""HHMS Diet Chart service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.admission import Admission
from app.models.diet_chart import DietChart
from app.repositories.diet_chart import diet_chart_repository
from app.schemas.diet_chart import DietChartCreate, DietChartUpdate


class DietChartService:
    async def get(self, db: AsyncSession, object_id: int) -> DietChart:
        item = await diet_chart_repository.get_by_id(db, object_id)
        if item is None:
            raise ResourceNotFoundException("Diet Chart not found.")
        return item

    async def list(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[DietChart]:
        admission = await db.get(Admission, admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")
        return await diet_chart_repository.list_by_admission(db, admission_id, skip, limit)

    async def create(self, db: AsyncSession, data: DietChartCreate) -> DietChart:
        admission = await db.get(Admission, data.admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")

        now = datetime.now(timezone.utc)
        item = DietChart(**data.model_dump(), created_at=now, updated_at=now)
        try:
            item = await diet_chart_repository.add(db, item)
            await db.commit()
            await db.refresh(item)
            return item
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create diet chart.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create diet chart.") from exc

    async def update(self, db: AsyncSession, object_id: int, data: DietChartUpdate) -> DietChart:
        item = await self.get(db, object_id)
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(item, field, value)
        item.updated_at = datetime.now(timezone.utc)
        try:
            await db.commit()
            await db.refresh(item)
            return item
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update diet chart.") from exc


dietChart_service = DietChartService()

__all__ = ["DietChartService", "dietChart_service"]
