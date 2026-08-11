"""
HHMS Stock Batch API Endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.stock_batch import (
    StockBatchCreate,
    StockBatchRead,
    StockBatchUpdate,
)
from app.services.stock_batch import stock_batch_service


router = APIRouter(
    prefix="/stock-batches",
    tags=["Stock"],
)


@router.get(
    "/medicine/{medicine_id}",
    response_model=list[StockBatchRead],
)
async def list_medicine_stock(
    medicine_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[StockBatchRead]:
    return await stock_batch_service.list_by_medicine(
        db,
        medicine_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=StockBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_batch(
    batch_in: StockBatchCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> StockBatchRead:
    return await stock_batch_service.create(
        db,
        batch_in,
    )


@router.get(
    "/{stock_batch_id}",
    response_model=StockBatchRead,
)
async def get_stock_batch(
    stock_batch_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> StockBatchRead:
    return await stock_batch_service.get(
        db,
        stock_batch_id,
    )


@router.patch(
    "/{stock_batch_id}",
    response_model=StockBatchRead,
)
async def update_stock_batch(
    stock_batch_id: int,
    batch_in: StockBatchUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> StockBatchRead:
    return await stock_batch_service.update(
        db,
        stock_batch_id,
        batch_in,
    )


__all__ = ["router"]