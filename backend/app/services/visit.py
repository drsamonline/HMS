"""
HHMS Visit Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.visit import Visit
from app.repositories.visit import (
    VisitRepository,
    visit_repository,
)
from app.schemas.visit import VisitCreate, VisitUpdate


class VisitService:
    """Business workflows for clinical visits."""

    def __init__(
        self,
        repository: VisitRepository | None = None,
    ) -> None:
        self.repository = repository or visit_repository

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        visit_id: int,
    ) -> Visit:
        visit = await self.repository.get_by_id(
            db,
            visit_id,
        )

        if visit is None:
            raise ResourceNotFoundException(
                "Visit not found."
            )

        return visit

    async def list(
        self,
        db: AsyncSession,
        *,
        patient_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Visit]:
        if patient_id is not None:
            return await self.repository.list_by_patient(
                db,
                patient_id=patient_id,
                skip=skip,
                limit=limit,
            )

        return await self.repository.list_all(
            db,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        visit_in: VisitCreate,
    ) -> Visit:
        visit = Visit(
            **visit_in.model_dump(),
            visit_number="PENDING",
        )

        try:
            visit = await self.repository.add(
                db,
                visit,
            )

            visit.visit_number = (
                f"VIS-{visit.id:06d}"
            )

            await self.repository.update(
                db,
                visit,
            )

            await db.commit()

            return visit

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create visit because a related "
                "record is invalid or a duplicate exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create visit."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        visit_id: int,
        visit_in: VisitUpdate,
    ) -> Visit:
        visit = await self.get_by_id(
            db,
            visit_id=visit_id,
        )

        update_data = visit_in.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return visit

        try:
            for field, value in update_data.items():
                setattr(
                    visit,
                    field,
                    value,
                )

            visit = await self.repository.update(
                db,
                visit,
            )

            await db.commit()

            return visit

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update visit."
            ) from exc


visit_service = VisitService()


__all__ = [
    "VisitService",
    "visit_service",
]