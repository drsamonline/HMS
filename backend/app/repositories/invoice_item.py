"""HHMS invoice item repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice_item import InvoiceItem
from app.repositories.base import RepositoryBase

class InvoiceItemRepository(RepositoryBase[InvoiceItem]):
    def __init__(self) -> None:
        super().__init__(InvoiceItem)

    async def list_by_invoice(self, db: AsyncSession, invoice_id: int) -> list[InvoiceItem]:
        result = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id).order_by(InvoiceItem.id.asc()))
        return list(result.scalars().all())

invoice_item_repository = InvoiceItemRepository()
__all__ = ["InvoiceItemRepository", "invoice_item_repository"]
