"""HHMS Clinical Progress Note repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress_note import ProgressNote
from app.repositories.base import RepositoryBase


class ProgressNoteRepository(RepositoryBase[ProgressNote]):
    def __init__(self) -> None:
        super().__init__(ProgressNote)

    async def get_by_id(self, db: AsyncSession, object_id: int) -> ProgressNote | None:
        return await db.get(ProgressNote, object_id)

    async def list_by_admission(self, db: AsyncSession, admission_id: int, skip: int = 0, limit: int = 100) -> list[ProgressNote]:
        result = await db.execute(
            select(ProgressNote).where(ProgressNote.admission_id == admission_id).order_by(ProgressNote.id.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


progress_note_repository = ProgressNoteRepository()

__all__ = ["ProgressNoteRepository", "progress_note_repository"]
