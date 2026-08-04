"""
Generic asynchronous CRUD base class for HHMS.

Provides reusable database operations for SQLAlchemy ORM models.
Business logic must remain in the service layer.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(
    Generic[
        ModelType,
        CreateSchemaType,
        UpdateSchemaType,
    ]
):
    """
    Generic CRUD implementation.

    This class provides common database operations for ORM
    entities. Entity-specific CRUD classes should inherit
    from this class and implement only custom queries.
    """

    def __init__(
        self,
        model: type[ModelType],
    ) -> None:
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        object_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve a single object by primary key.
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
        Retrieve multiple objects.
        """
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """
        Create a new database object.
        """
        db_obj = self.model(
            **obj_in.model_dump()
        )

        db.add(db_obj)

        await db.flush()
        await db.refresh(db_obj)

        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update an existing database object.
        """

        update_data: dict[str, Any]

        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(
                exclude_unset=True,
            )
        else:
            update_data = obj_in

        for field, value in update_data.items():
            setattr(
                db_obj,
                field,
                value,
            )

        await db.flush()
        await db.refresh(db_obj)

        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
    ) -> None:
        """
        Delete an existing database object.
        """

        await db.delete(db_obj)

        await db.flush()