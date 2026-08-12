"""HHMS Department master service."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.crud.department import department_crud
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    """Business operations for the editable hospital department master."""

    async def list(
        self,
        db: AsyncSession,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Department]:
        query = select(Department).offset(skip).limit(limit)
        if active_only:
            query = query.where(Department.is_active.is_(True))
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, department_id: UUID) -> Department:
        record = await department_crud.get(db, department_id)
        if record is None:
            raise ResourceNotFoundException("Department not found.")
        return record

    async def create(
        self,
        db: AsyncSession,
        data: DepartmentCreate,
    ) -> Department:
        if await department_crud.exists_code(db, code=data.code):
            raise DuplicateResourceException("Department code already exists.")
        if await department_crud.exists_name(db, name=data.name):
            raise DuplicateResourceException("Department name already exists.")
        try:
            record = await department_crud.create(db, obj_in=data)
            await db.commit()
            await db.refresh(record)
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Department code or name already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create department.") from exc

    async def update(
        self,
        db: AsyncSession,
        department_id: UUID,
        data: DepartmentUpdate,
    ) -> Department:
        record = await self.get(db, department_id)
        values = data.model_dump(exclude_unset=True)
        if "code" in values:
            existing = await department_crud.get_by_code(db, code=values["code"])
            if existing is not None and existing.id != record.id:
                raise DuplicateResourceException("Department code already exists.")
        if "name" in values:
            existing = await department_crud.get_by_name(db, name=values["name"])
            if existing is not None and existing.id != record.id:
                raise DuplicateResourceException("Department name already exists.")
        try:
            record = await department_crud.update(db, db_obj=record, obj_in=values)
            await db.commit()
            await db.refresh(record)
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Department code or name already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update department.") from exc


department_service = DepartmentService()

__all__ = ["DepartmentService", "department_service"]
