"""
HHMS Stock Transaction API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
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
    tags=["Inventory"],
)


@router.get(
    "/item/{inventory_item_id}",
    response_model=list[StockTransactionRead],
)
async def list_item_transactions(
    inventory_item_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[StockTransactionRead]:
    return await stock_transaction_service.list_by_item(
        db,
        inventory_item_id,
        skip=skip,
        limit=limit,
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


@router.post(
    "",
    response_model=StockTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_transaction(
    transaction_in: StockTransactionCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> StockTransactionRead:
    subject = current_user.get("sub")

    try:
        performed_by = int(subject)
    except (TypeError, ValueError) as exc:
        from app.core.exceptions import (
            AuthenticationException,
        )

        raise AuthenticationException(
            "Authenticated user identity is invalid."
        ) from exc

    return await stock_transaction_service.create(
        db,
        transaction_in,
        performed_by,
    )


__all__ = [
    "router",
]