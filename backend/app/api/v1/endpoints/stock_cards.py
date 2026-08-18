"""Pharmacy stock-card API."""
from __future__ import annotations
from decimal import Decimal
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.stock_card import StockCardCreate, StockCardRead
from app.services.stock_card import stock_card_service
from app.core.exceptions import AuthenticationException

router = APIRouter(prefix="/stock-cards", tags=["Pharmacy Stock"])


def _current_user_id(user: dict) -> int:
    try:
        uid = int(user.get("sub"))
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("Authenticated user identity is invalid.") from exc
    if uid <= 0:
        raise AuthenticationException("Authenticated user identity is invalid.")
    return uid


class StockAdjustmentRequest(BaseModel):
    quantity_delta: Decimal = Field(ne=0)
    reference_type: str | None = Field(default=None, max_length=40)
    reference_id: int | None = Field(default=None, gt=0)
    remarks: str | None = None


@router.get("/batch/{stock_batch_id}", response_model=list[StockCardRead])
async def list_batch_stock_cards(stock_batch_id: int, db: DatabaseSession, _: CurrentUserDependency, skip: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=500)):
    return await stock_card_service.list_by_batch(db, stock_batch_id, skip=skip, limit=limit)


@router.post("/batch/{stock_batch_id}", response_model=StockCardRead, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(stock_batch_id: int, data: StockCardCreate, db: DatabaseSession, user: CurrentUserDependency):
    return await stock_card_service.create(db, stock_batch_id, data, _current_user_id(user))


@router.post("/batch/{stock_batch_id}/adjustment", response_model=StockCardRead, status_code=status.HTTP_201_CREATED)
async def adjust_stock(stock_batch_id: int, data: StockAdjustmentRequest, db: DatabaseSession, user: CurrentUserDependency):
    return await stock_card_service.create_adjustment(db, stock_batch_id, data.quantity_delta, created_by=_current_user_id(user), reference_type=data.reference_type, reference_id=data.reference_id, remarks=data.remarks)


__all__ = ["router"]
