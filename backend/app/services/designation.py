"""HHMS Designation master service."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.crud.designation import designation_crud
from app.models.designation import Designation
from app.schemas.designation import DesignationCreate, DesignationUpdate

class DesignationService:
    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 200) -> list[Designation]:
        result = await db.execute(select(Designation).order_by(Designation.name).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, designation_id: UUID) -> Designation:
        record = await designation_crud.get(db, designation_id)
        if record is None:
            raise ResourceNotFoundException("Designation not found.")
        return record

    async def create(self, db: AsyncSession, data: DesignationCreate) -> Designation:
        if await designation_crud.exists_code(db, code=data.code):
            raise DuplicateResourceException("Designation code already exists.")
        if await designation_crud.exists_name(db, name=data.name):
            raise DuplicateResourceException("Designation name already exists.")
        try:
            record = await designation_crud.create(db, obj_in=data)
            await db.commit(); await db.refresh(record)
            return record
        except IntegrityError as exc:
            await db.rollback(); raise DuplicateResourceException("Designation code or name already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to create designation.") from exc

    async def update(self, db: AsyncSession, designation_id: UUID, data: DesignationUpdate) -> Designation:
        record = await self.get(db, designation_id)
        values = data.model_dump(exclude_unset=True)
        if "code" in values:
            existing = await designation_crud.get_by_code(db, code=values["code"])
            if existing is not None and existing.id != record.id:
                raise DuplicateResourceException("Designation code already exists.")
        if "name" in values:
            existing = await designation_crud.get_by_name(db, name=values["name"])
            if existing is not None and existing.id != record.id:
                raise DuplicateResourceException("Designation name already exists.")
        try:
            record = await designation_crud.update(db, db_obj=record, obj_in=values)
            await db.commit(); await db.refresh(record)
            return record
        except IntegrityError as exc:
            await db.rollback(); raise DuplicateResourceException("Designation code or name already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to update designation.") from exc

designation_service = DesignationService()
__all__ = ["DesignationService", "designation_service"]
