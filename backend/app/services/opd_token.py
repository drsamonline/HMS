"""
HHMS OPD Token Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.opd_token import OPDToken
from app.repositories.opd_token import (
    OPDTokenRepository,
    opd_token_repository,
)
from app.schemas.opd_token import (
    OPDTokenCreate,
    OPDTokenUpdate,
)


class OPDTokenService:
    """Business workflows for OPD queue management."""

    def __init__(
        self,
        repository: OPDTokenRepository | None = None,
    ) -> None:
        self.repository = repository or opd_token_repository

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        token_id: int,
    ) -> OPDToken:
        token = await self.repository.get_by_id(
            db,
            token_id,
        )

        if token is None:
            raise ResourceNotFoundException(
                "OPD token not found."
            )

        return token

    async def list(
        self,
        db: AsyncSession,
        *,
        queue_date,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OPDToken]:
        return await self.repository.list_by_date(
            db,
            queue_date=queue_date,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        token_in: OPDTokenCreate,
    ) -> OPDToken:
        existing = await self.repository.get_by_visit(
            db,
            visit_id=token_in.visit_id,
        )

        if existing is not None:
            raise DuplicateResourceException(
                "This visit already has an OPD token."
            )

        token_number = (
            await self.repository.get_next_token_number(
                db,
                queue_date=token_in.queue_date,
            )
        )

        token = OPDToken(
            visit_id=token_in.visit_id,
            token_number=token_number,
            queue_date=token_in.queue_date,
            queue_status="waiting",
            generated_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        try:
            token = await self.repository.add(
                db,
                token,
            )

            await db.commit()

            return token

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to generate the OPD token."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create OPD token."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        token_id: int,
        token_in: OPDTokenUpdate,
    ) -> OPDToken:
        token = await self.get_by_id(
            db,
            token_id=token_id,
        )

        if token.queue_status in {
            "completed",
            "cancelled",
        }:
            raise BusinessRuleException(
                "A completed or cancelled OPD token cannot be modified."
            )

        update_data = token_in.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(
                token,
                field,
                value,
            )

        token.updated_at = datetime.now(timezone.utc)

        if token.queue_status == "in_consultation":
            token.called_at = (
                token.called_at
                or datetime.now(timezone.utc)
            )

        if token.queue_status == "completed":
            token.completed_at = (
                token.completed_at
                or datetime.now(timezone.utc)
            )

        try:
            token = await self.repository.update(
                db,
                token,
            )

            await db.commit()

            return token

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update OPD token."
            ) from exc

    async def cancel(
        self,
        db: AsyncSession,
        *,
        token_id: int,
    ) -> OPDToken:
        token = await self.get_by_id(
            db,
            token_id=token_id,
        )

        if token.queue_status == "completed":
            raise BusinessRuleException(
                "A completed OPD token cannot be cancelled."
            )

        token.queue_status = "cancelled"
        token.updated_at = datetime.now(timezone.utc)

        try:
            token = await self.repository.update(
                db,
                token,
            )

            await db.commit()

            return token

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to cancel OPD token."
            ) from exc


opd_token_service = OPDTokenService()


__all__ = [
    "OPDTokenService",
    "opd_token_service",
]