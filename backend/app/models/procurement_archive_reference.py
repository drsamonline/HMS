"""Permanent live-database references for physically archived procurement & inventory records."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PurchaseOrderArchiveReference(Base):
    """Retains purchase-order identity after the record leaves the live database."""

    __tablename__ = "PurchaseOrderArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_purchase_order_id",
            name="uq_purchase_order_archive_ref_original_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_purchase_order_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_purchase_order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_no: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    order_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


class GoodsReceiptArchiveReference(Base):
    """Retains goods-receipt identity after the record leaves the live database."""

    __tablename__ = "GoodsReceiptArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_goods_receipt_id",
            name="uq_goods_receipt_archive_ref_original_receipt",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_goods_receipt_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_goods_receipt_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    goods_receipt_no: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    receipt_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


class StockTransactionArchiveReference(Base):
    """Retains stock-ledger transaction identity after the row leaves the live database."""

    __tablename__ = "StockTransactionArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_stock_transaction_id",
            name="uq_stock_transaction_archive_ref_original_transaction",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_stock_transaction_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_stock_transaction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    inventory_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    transaction_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


class StockCardArchiveReference(Base):
    """Retains stock-card ledger identity after the row leaves the live database."""

    __tablename__ = "StockCardArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_stock_card_id",
            name="uq_stock_card_archive_ref_original_card",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_stock_card_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_stock_card_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    transaction_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


__all__ = [
    "PurchaseOrderArchiveReference",
    "GoodsReceiptArchiveReference",
    "StockTransactionArchiveReference",
    "StockCardArchiveReference",
]
