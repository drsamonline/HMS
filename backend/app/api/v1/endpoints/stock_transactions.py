"""
HHMS Stock Transaction API Endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.stock_transaction import (
    StockTransactionCreate,
    StockTransactionRead,
)
from app.services.stock_transaction import (
    stock_transaction_service,
)


router = APIRouter(
    prefix="/stock-transactions",
    tags=["Stock Transactions"],
)


@router.post(
    "",
    response_model=StockTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_transaction(
    transaction_in: StockTransactionCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> StockTransactionRead:
    return await stock_transaction_service.create(
        db,
        transaction_in,
    )


@router.get(
    "/{transaction_id}",
    response_model=StockTransactionRead,
)
async def get_stock_transaction(
    transaction_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> StockTransactionRead:
    return await stock_transaction_service.get(
        db,
        transaction_id,
    )


@router.get(
    "/inventory/{inventory_item_id}",
    response_model=list[StockTransactionRead],
)
async def list_stock_transactions(
    inventory_item_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> list[StockTransactionRead]:
    return await (
        stock_transaction_service.list_by_inventory_item(
            db,
            inventory_item_id=inventory_item_id,
            skip=skip,
            limit=limit,
        )
    )


__all__ = ["router"]