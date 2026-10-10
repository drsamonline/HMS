"""
HHMS Bed Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.bed import Bed
from app.repositories.bed import (
    BedRepository,
    bed_repository,
)
from app.schemas.bed import (
    BedCreate,
    BedUpdate,
)


class BedService:
    """Business operations for IPD bed management."""

    def __init__(
        self,
        repository: BedRepository | None = None,
    ) -> None:
        self.repository = (
            repository or bed_repository
        )

    async def get(
        self,
        db: AsyncSession,
        bed_id: int,
    ) -> Bed:
        bed = await self.repository.get_by_id(
            db,
            bed_id,
        )

        if bed is None:
            raise ResourceNotFoundException(
                "Bed not found."
            )

        return bed

    async def list(
        self,
        db: AsyncSession,
        *,
        ward: str | None = None,
        occupancy_status: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Bed]:
        return await self.repository.list_beds(
            db,
            ward=ward,
            occupancy_status=occupancy_status,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: BedCreate,
    ) -> Bed:
        existing = await self.repository.get_by_number(
            db,
            data.bed_number,
        )

        if existing is not None:
            raise DuplicateResourceException(
                "Bed number already exists."
            )

        now = datetime.now(timezone.utc)

        bed = Bed(
            **data.model_dump(),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        try:
            bed = await self.repository.add(
                db,
                bed,
            )

            await db.commit()

            return bed

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Bed number already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create bed."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        bed_id: int,
        data: BedUpdate,
    ) -> Bed:
        bed = await self.get(
            db,
            bed_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        new_status = values.get(
            "occupancy_status",
            bed.occupancy_status,
        )

        new_active = values.get(
            "is_active",
            bed.is_active,
        )

        if (
            new_active is False
            and bed.occupancy_status == "occupied"
        ):
            raise BusinessRuleException(
                "An occupied bed cannot be deactivated."
            )

        if (
            bed.occupancy_status == "occupied"
            and new_status in {
                "available",
                "maintenance",
                "blocked",
            }
        ):
            raise BusinessRuleException(
                "An occupied bed cannot be manually "
                "changed to a non-occupied status."
            )

        for field, value in values.items():
            setattr(
                bed,
                field,
                value,
            )

        bed.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            bed = await self.repository.update(
                db,
                bed,
            )

            await db.commit()

            return bed

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update bed."
            ) from exc


bed_service = BedService()


__all__ = [
    "BedService",
    "bed_service",
]