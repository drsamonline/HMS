"""HHMS Clinical Progress Note service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.admission import Admission
from app.models.progress_note import ProgressNote
from app.repositories.progress_note import progress_note_repository
from app.schemas.progress_note import ProgressNoteCreate, ProgressNoteUpdate


class ProgressNoteService:
    async def get(self, db: AsyncSession, object_id: int) -> ProgressNote:
        item = await progress_note_repository.get_by_id(db, object_id)
        if item is None:
            raise ResourceNotFoundException("Clinical Progress Note not found.")
        return item

    async def list(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[ProgressNote]:
        admission = await db.get(Admission, admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")
        return await progress_note_repository.list_by_admission(db, admission_id, skip, limit)

    async def create(self, db: AsyncSession, data: ProgressNoteCreate) -> ProgressNote:
        admission = await db.get(Admission, data.admission_id)
        if admission is None:
            raise ResourceNotFoundException("Admission not found.")

        now = datetime.now(timezone.utc)
        item = ProgressNote(**data.model_dump(), created_at=now, updated_at=now)
        try:
            item = await progress_note_repository.add(db, item)
            await db.commit()
            await db.refresh(item)
            return item
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Unable to create clinical progress note.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create clinical progress note.") from exc

    async def update(self, db: AsyncSession, object_id: int, data: ProgressNoteUpdate) -> ProgressNote:
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
            raise DatabaseException("Unable to update clinical progress note.") from exc


progressNote_service = ProgressNoteService()

__all__ = ["ProgressNoteService", "progressNote_service"]
