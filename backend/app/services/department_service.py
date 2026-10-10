"""Business service for the configurable department-service master."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.department import Department
from app.models.department_service import DepartmentService
from app.repositories.department_service import DepartmentServiceRepository, department_service_repository
from app.schemas.department_service import DepartmentServiceCreate, DepartmentServiceUpdate


class DepartmentServiceManager:
    def __init__(self, repository: DepartmentServiceRepository | None = None) -> None:
        self.repository = repository or department_service_repository

    async def get(self, db: AsyncSession, service_id: UUID) -> DepartmentService:
        record = await self.repository.get(db, service_id)
        if record is None:
            raise ResourceNotFoundException("Department service not found.")
        return record

    async def list(
        self, db: AsyncSession, department_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[DepartmentService]:
        if await db.get(Department, department_id) is None:
            raise ResourceNotFoundException("Department not found.")
        return await self.repository.list_by_department(db, department_id, skip, limit)

    async def create(
        self, db: AsyncSession, data: DepartmentServiceCreate
    ) -> DepartmentService:
        if await db.get(Department, data.department_id) is None:
            raise ResourceNotFoundException("Department not found.")
        if data.parent_service_id is not None:
            parent = await self.get(db, data.parent_service_id)
            if parent.department_id != data.department_id:
                raise ValueError("Parent service belongs to another department.")
        record = DepartmentService(**data.model_dump())
        try:
            await self.repository.add(db, record)
            await db.commit()
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Department service code is already in use.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create department service.") from exc

    async def update(
        self, db: AsyncSession, service_id: UUID, data: DepartmentServiceUpdate
    ) -> DepartmentService:
        record = await self.get(db, service_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        try:
            await self.repository.update(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update department service.") from exc


department_service_manager = DepartmentServiceManager()

__all__ = ["DepartmentServiceManager", "department_service_manager"]
