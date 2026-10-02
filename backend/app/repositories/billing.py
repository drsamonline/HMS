"""
HHMS Billing Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.repositories.base import RepositoryBase


class InvoiceRepository(
    RepositoryBase[Invoice],
):
    """Persistence operations for invoices."""

    def __init__(self) -> None:
        super().__init__(Invoice)

    async def get_by_id(
        self,
        db: AsyncSession,
        invoice_id: int,
    ) -> Invoice | None:
        return await db.get(
            Invoice,
            invoice_id,
        )

    async def get_by_number(
        self,
        db: AsyncSession,
        invoice_number: str,
    ) -> Invoice | None:
        result = await db.execute(
            select(Invoice).where(
                Invoice.invoice_number
                == invoice_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_all(
        self,
        db: AsyncSession,
        *,
        patient_id: int | None = None,
        payment_status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        statement = select(Invoice)

        if patient_id is not None:
            statement = statement.where(
                Invoice.patient_id == patient_id,
            )

        if payment_status is not None:
            statement = statement.where(
                Invoice.payment_status
                == payment_status,
            )

        result = await db.execute(
            statement
            .order_by(
                Invoice.invoice_date.desc(),
                Invoice.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


class PaymentRepository(
    RepositoryBase[Payment],
):
    """Persistence operations for payments."""

    def __init__(self) -> None:
        super().__init__(Payment)

    async def get_by_id(
        self,
        db: AsyncSession,
        payment_id: int,
    ) -> Payment | None:
        return await db.get(
            Payment,
            payment_id,
        )

    async def get_by_receipt_number(
        self,
        db: AsyncSession,
        receipt_number: str,
    ) -> Payment | None:
        result = await db.execute(
            select(Payment).where(
                Payment.receipt_number
                == receipt_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_invoice(
        self,
        db: AsyncSession,
        invoice_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(
                Payment.invoice_id == invoice_id,
            )
            .order_by(
                Payment.payment_datetime.desc(),
                Payment.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )

    async def list_recent(
        self,
        db: AsyncSession,
        *,
        since: datetime,
        limit: int = 200,
    ) -> list[Payment]:
        """Payments recorded at or after ``since``, newest first.

        Batch 83 — receipt-number continuity feed: the service layer joins
        in invoice/patient identity and drops orphaned rows.
        """
        result = await db.execute(
            select(Payment)
            .where(
                Payment.payment_datetime >= since,
            )
            .order_by(
                Payment.payment_datetime.desc(),
                Payment.id.desc(),
            )
            .limit(limit)
        )

        return list(result.scalars().all())

    async def total_paid(
        self,
        db: AsyncSession,
        invoice_id: int,
    ) -> Decimal:
        result = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        Payment.amount_paid
                    ),
                    0,
                )
            ).where(
                Payment.invoice_id == invoice_id,
            )
        )

        value = result.scalar_one()

        return Decimal(str(value))


invoice_repository = InvoiceRepository()

payment_repository = PaymentRepository()


__all__ = [
    "InvoiceRepository",
    "PaymentRepository",
    "invoice_repository",
    "payment_repository",
]