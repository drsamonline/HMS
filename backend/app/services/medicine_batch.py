"""
HHMS Medicine Batch Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.medicine_batch import MedicineBatch
from app.repositories.medicine_batch import (
    MedicineBatchRepository,
    medicine_batch_repository,
)
from app.schemas.medicine_batch import (
    MedicineBatchCreate,
    MedicineBatchUpdate,
)


class MedicineBatchService:
    """Business operations for pharmacy medicine batches."""

    def __init__(
        self,
        repository: MedicineBatchRepository | None = None,
    ) -> None:
        self.repository = (
            repository or medicine_batch_repository
        )

    async def get(
        self,
        db: AsyncSession,
        batch_id: int,
    ) -> MedicineBatch:
        batch = await self.repository.get_by_id(
            db,
            batch_id,
        )

        if batch is None:
            raise ResourceNotFoundException(
                "Medicine batch not found."
            )

        return batch

    async def list_by_medicine(
        self,
        db: AsyncSession,
        *,
        medicine_id: int,
        active_only: bool = True,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MedicineBatch]:
        return await self.repository.list_by_medicine(
            db,
            medicine_id=medicine_id,
            active_only=active_only,
            available_only=available_only,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: MedicineBatchCreate,
    ) -> MedicineBatch:
        existing = (
            await self.repository.get_by_batch_number(
                db,
                medicine_id=data.medicine_id,
                batch_number=data.batch_number,
            )
        )

        if existing is not None:
            raise DuplicateResourceException(
                "This batch number already exists "
                "for the selected medicine."
            )

        now = datetime.now(timezone.utc)

        batch = MedicineBatch(
            **data.model_dump(),
            created_at=now,
            updated_at=now,
        )

        try:
            batch = await self.repository.add(
                db,
                batch,
            )

            await db.commit()

            return batch

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create medicine batch."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create medicine batch."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        batch_id: int,
        data: MedicineBatchUpdate,
    ) -> MedicineBatch:
        batch = await self.get(
            db,
            batch_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(
                batch,
                field,
                value,
            )

        batch.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            batch = await self.repository.update(
                db,
                batch,
            )

            await db.commit()

            return batch

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update medicine batch."
            ) from exc


medicine_batch_service = MedicineBatchService()


__all__ = [
    "MedicineBatchService",
    "medicine_batch_service",
]