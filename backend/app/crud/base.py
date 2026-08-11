"""
HHMS Generic Asynchronous CRUD
==============================

Provides reusable asynchronous database operations for SQLAlchemy
ORM models.

Entity-specific validation, password handling, authorization,
business rules, and custom queries belong to their respective
CRUD/service layers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


ModelType = TypeVar(
    "ModelType",
    bound=Base,
)

CreateSchemaType = TypeVar(
    "CreateSchemaType",
    bound=BaseModel,
)

UpdateSchemaType = TypeVar(
    "UpdateSchemaType",
    bound=BaseModel,
)


class CRUDBase(
    Generic[
        ModelType,
        CreateSchemaType,
        UpdateSchemaType,
    ]
):
    """
    Generic asynchronous CRUD implementation.

    This class provides common database operations for HHMS ORM
    entities. Entity-specific CRUD classes should inherit from
    this class and implement only entity-specific operations.
    """

    def __init__(
        self,
        model: type[ModelType],
    ) -> None:
        """
        Initialize the CRUD handler.

        Parameters
        ----------
        model : type[ModelType]
            SQLAlchemy ORM model managed by this CRUD instance.
        """

        self.model = model

    async def get(
        self,
        db: AsyncSession,
        object_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve a single object by primary key.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        object_id : UUID
            Primary-key value.

        Returns
        -------
        ModelType | None
            Matching ORM object, or None when not found.
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

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        skip : int
            Number of records to skip.

        limit : int
            Maximum number of records to return.

        Returns
        -------
        list[ModelType]
            Matching ORM objects.

        Raises
        ------
        ValueError
            If skip is negative or limit is not positive.
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

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """
        Create a new database object.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        obj_in : CreateSchemaType
            Validated creation schema.

        Returns
        -------
        ModelType
            Newly created ORM object.

        Notes
        -----
        This method flushes and refreshes the object but does not
        commit the transaction. Transaction ownership remains with
        the calling service or request layer.
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

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        db_obj : ModelType
            Existing ORM object.

        obj_in : UpdateSchemaType | dict[str, Any]
            Validated update schema or explicit update mapping.

        Returns
        -------
        ModelType
            Updated ORM object.

        Notes
        -----
        Entity-specific transformations such as password hashing
        must occur before this generic method is called.
        """

        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(
                exclude_unset=True,
            )
        else:
            update_data = dict(obj_in)

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

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        db_obj : ModelType
            ORM object to delete.

        Notes
        -----
        The transaction is flushed but not committed. Transaction
        ownership remains with the calling service or request layer.
        """

        await db.delete(db_obj)
        await db.flush()


__all__ = [
    "CRUDBase",
]