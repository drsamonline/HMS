from __future__ import annotations
from fastapi import APIRouter, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.goods_receipt import GoodsReceiptCreate, GoodsReceiptRead
from app.services.goods_receipt import goods_receipt_service

router = APIRouter(prefix="/goods-receipts", tags=["Inventory"])

@router.post("", response_model=GoodsReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_goods_receipt(data: GoodsReceiptCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> GoodsReceiptRead:
    try:
        received_by = int(current_user.get("sub"))
    except (TypeError, ValueError) as exc:
        from app.core.exceptions import AuthenticationException
        raise AuthenticationException("Authenticated user identity is invalid.") from exc
    return await goods_receipt_service.create(db, data, received_by)

@router.get("/{receipt_id}", response_model=GoodsReceiptRead)
async def get_goods_receipt(receipt_id: int, db: DatabaseSession, _: CurrentUserDependency) -> GoodsReceiptRead:
    return await goods_receipt_service.get(db, receipt_id)

__all__ = ["router"]
