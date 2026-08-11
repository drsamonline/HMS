"""
HHMS Generic Repository
=======================

Provides reusable asynchronous database-access operations for
SQLAlchemy ORM entities.

Repositories are responsible only for persistence and ORM
interaction. Business rules, validation workflows, transactions,
and orchestration belong to the Service Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


ModelType = TypeVar(
    "ModelType",
    bound=Base,
)


class RepositoryBase(
    Generic[ModelType],
):
    """
    Generic asynchronous repository.

    Provides common persistence operations for HHMS ORM entities.
    """

    def __init__(
        self,
        model: type[ModelType],
    ) -> None:
        """
        Initialize the repository.

        Parameters
        ----------
        model : type[ModelType]
            SQLAlchemy ORM model managed by this repository.
        """

        self.model = model

    async def get(
        self,
        db: AsyncSession,
        object_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve an entity by primary key.
        """

        return await db.get(
            self.model,
            object_id,
        )

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Retrieve multiple entities.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        skip : int
            Number of records to skip.

        limit : int
            Maximum number of records to return.

        Raises
        ------
        ValueError
            If pagination values are invalid.
        """

        if skip < 0:
            raise ValueError(
                "skip must be greater than or equal to zero."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )

    async def add(
        self,
        db: AsyncSession,
        entity: ModelType,
    ) -> ModelType:
        """
        Add an ORM entity to the current transaction.

        The transaction is flushed but not committed.
        """

        db.add(entity)

        await db.flush()
        await db.refresh(entity)

        return entity

    async def update(
        self,
        db: AsyncSession,
        entity: ModelType,
    ) -> ModelType:
        """
        Flush changes made to an existing ORM entity.

        The transaction is not committed.
        """

        await db.flush()
        await db.refresh(entity)

        return entity

    async def delete(
        self,
        db: AsyncSession,
        entity: ModelType,
    ) -> None:
        """
        Delete an ORM entity.

        The transaction is flushed but not committed.
        """

        await db.delete(entity)
        await db.flush()


__all__ = [
    "RepositoryBase",
]