"""
HHMS Medicine Service.

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
from app.models.medicine import Medicine
from app.repositories.medicine import (
    MedicineRepository,
    medicine_repository,
)
from app.schemas.medicine import (
    MedicineCreate,
    MedicineUpdate,
)


class MedicineService:
    """Business operations for the medicine master."""

    def __init__(
        self,
        repository: MedicineRepository | None = None,
    ) -> None:
        self.repository = (
            repository or medicine_repository
        )

    async def get(
        self,
        db: AsyncSession,
        medicine_id: int,
    ) -> Medicine:
        medicine = await self.repository.get_by_id(
            db,
            medicine_id,
        )

        if medicine is None:
            raise ResourceNotFoundException(
                "Medicine not found."
            )

        return medicine

    async def list(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Medicine]:
        return await self.repository.search(
            db,
            search=search,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: MedicineCreate,
    ) -> Medicine:
        medicine = Medicine(
            **data.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        try:
            db.add(medicine)
            await db.commit()
            await db.refresh(medicine)

            return medicine

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Medicine code or medicine name already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create medicine."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        medicine_id: int,
        data: MedicineUpdate,
    ) -> Medicine:
        medicine = await self.get(
            db,
            medicine_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(
                medicine,
                field,
                value,
            )

        medicine.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            await db.commit()
            await db.refresh(medicine)

            return medicine

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Medicine name already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update medicine."
            ) from exc


medicine_service = MedicineService()


__all__ = [
    "MedicineService",
    "medicine_service",
]