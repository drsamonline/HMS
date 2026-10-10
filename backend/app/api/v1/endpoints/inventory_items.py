"""
HHMS Inventory Item API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.inventory_item import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
)
from app.services.inventory_item import (
    inventory_item_service,
)


router = APIRouter(
    prefix="/inventory-items",
    tags=["Inventory"],
)


@router.get(
    "",
    response_model=list[InventoryItemRead],
)
async def list_inventory_items(
    db: DatabaseSession,
    _: CurrentUserDependency,
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    active_only: bool = Query(
        default=True,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[InventoryItemRead]:
    return await inventory_item_service.list(
        db,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=InventoryItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory_item(
    item_in: InventoryItemCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InventoryItemRead:
    return await inventory_item_service.create(
        db,
        item_in,
    )


@router.get(
    "/{item_id}",
    response_model=InventoryItemRead,
)
async def get_inventory_item(
    item_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InventoryItemRead:
    return await inventory_item_service.get(
        db,
        item_id,
    )


@router.patch(
    "/{item_id}",
    response_model=InventoryItemRead,
)
async def update_inventory_item(
    item_id: int,
    item_in: InventoryItemUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InventoryItemRead:
    return await inventory_item_service.update(
        db,
        item_id=item_id,
        data=item_in,
    )


__all__ = [
    "router",
]