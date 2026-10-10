from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.repositories.base import RepositoryBase

class GoodsReceiptRepository(RepositoryBase[GoodsReceipt]):
    def __init__(self) -> None:
        super().__init__(GoodsReceipt)
    async def get_by_id(self, db: AsyncSession, receipt_id: int) -> GoodsReceipt | None:
        return await db.get(GoodsReceipt, receipt_id)
    async def get_by_receipt_no(self, db: AsyncSession, receipt_no: str) -> GoodsReceipt | None:
        return await db.scalar(select(GoodsReceipt).where(GoodsReceipt.receipt_no == receipt_no))
    async def list_items(self, db: AsyncSession, receipt_id: int) -> list[GoodsReceiptItem]:
        result = await db.execute(select(GoodsReceiptItem).where(GoodsReceiptItem.goods_receipt_id == receipt_id).order_by(GoodsReceiptItem.id))
        return list(result.scalars().all())

goods_receipt_repository = GoodsReceiptRepository()
