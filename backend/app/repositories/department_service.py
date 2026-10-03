"""Repository for the department-service master."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department_service import DepartmentService
from app.repositories.base import RepositoryBase


class DepartmentServiceRepository(RepositoryBase[DepartmentService]):
    def __init__(self) -> None:
        super().__init__(DepartmentService)

    async def list_by_department(
        self, db: AsyncSession, department_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[DepartmentService]:
        result = await db.execute(
            select(DepartmentService)
            .where(DepartmentService.department_id == department_id)
            .order_by(DepartmentService.name)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())


department_service_repository = DepartmentServiceRepository()

__all__ = ["DepartmentServiceRepository", "department_service_repository"]
