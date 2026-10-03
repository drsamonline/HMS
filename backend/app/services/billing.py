"""
HHMS Billing Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.admission import Admission
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.patient import Patient
from app.models.payment import Payment
from app.models.visit import Visit
from app.repositories.invoice_item import invoice_item_repository
from app.repositories.billing import (
    InvoiceRepository,
    PaymentRepository,
    invoice_repository,
    payment_repository,
)
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceItemCreate,
    InvoiceUpdate,
    PaymentCreate,
)

from app.services.number_sequence import number_sequence_service
from app.services.operational_year import operational_year_service


class BillingService:
    """Business operations for invoices and payments."""

    def __init__(
        self,
        invoice_repo: InvoiceRepository | None = None,
        payment_repo: PaymentRepository | None = None,
    ) -> None:
        self.invoice_repo = (
            invoice_repo or invoice_repository
        )
        self.payment_repo = (
            payment_repo or payment_repository
        )

    async def get_invoice(
        self,
        db: AsyncSession,
        invoice_id: int,
    ) -> Invoice:
        invoice = await self.invoice_repo.get_by_id(
            db,
            invoice_id,
        )

        if invoice is None:
            raise ResourceNotFoundException(
                "Invoice not found."
            )

        return invoice

    async def list_invoices(
        self,
        db: AsyncSession,
        *,
        patient_id: int | None = None,
        payment_status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        return await self.invoice_repo.list_all(
            db,
            patient_id=patient_id,
            payment_status=payment_status,
            skip=skip,
            limit=limit,
        )

    async def list_outstanding_invoices(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
    ) -> tuple[list[Invoice], Decimal]:
        """Oldest-first unpaid/partial invoices with the aggregate balance.

        Batch 82 — outstanding-billing continuity feed. Cancelling an
        invoice clears its remaining liability (see ``update_invoice``),
        so paid/cancelled rows are excluded and the balance is derived
        from live payments rather than the stored status alone.
        """
        statement = (
            select(Invoice)
            .where(
                Invoice.payment_status.in_(("unpaid", "partial")),
            )
            .order_by(
                Invoice.invoice_date.asc(),
                Invoice.id.asc(),
            )
        )
        result = await db.execute(statement)
        candidates = list(result.scalars().all())

        if not candidates:
            return [], Decimal("0")

        invoice_ids = [invoice.id for invoice in candidates]
        totals_result = await db.execute(
            select(
                Payment.invoice_id,
                func.coalesce(func.sum(Payment.amount_paid), 0),
            )
            .where(Payment.invoice_id.in_(invoice_ids))
            .group_by(Payment.invoice_id)
        )
        paid_by_invoice = {
            row[0]: Decimal(str(row[1])) for row in totals_result
        }

        outstanding: list[Invoice] = []
        total_balance = Decimal("0")
        for invoice in candidates:
            balance = max(
                invoice.total_amount - paid_by_invoice.get(invoice.id, Decimal("0")),
                Decimal("0"),
            )
            # Derived balance wins over a stale stored status.
            if balance <= 0:
                continue
            outstanding.append(invoice)
            total_balance += balance
            if len(outstanding) >= limit:
                break

        return outstanding, total_balance

    async def create_invoice(
        self,
        db: AsyncSession,
        data: InvoiceCreate,
        generated_by: int,
    ) -> Invoice:
        patient = await db.get(
            Patient,
            data.patient_id,
        )

        if patient is None:
            raise ResourceNotFoundException(
                "Patient not found."
            )

        if (
            data.visit_id is None
            and data.admission_id is None
        ):
            raise BusinessRuleException(
                "Invoice must be linked to a visit "
                "or admission."
            )

        if (
            data.visit_id is not None
            and data.admission_id is not None
        ):
            raise BusinessRuleException(
                "Invoice cannot be linked to both "
                "a visit and admission."
            )

        if data.visit_id is not None:
            visit = await db.get(
                Visit,
                data.visit_id,
            )

            if visit is None:
                raise ResourceNotFoundException(
                    "Visit not found."
                )

            if visit.patient_id != data.patient_id:
                raise BusinessRuleException(
                    "Selected visit does not belong "
                    "to the selected patient."
                )

        if data.admission_id is not None:
            admission = await db.get(
                Admission,
                data.admission_id,
            )

            if admission is None:
                raise ResourceNotFoundException(
                    "Admission not found."
                )

            if (
                admission.patient_id
                != data.patient_id
            ):
                raise BusinessRuleException(
                    "Selected admission does not belong "
                    "to the selected patient."
                )

        now = datetime.now(timezone.utc)

        # Derive the annual lifecycle fields from the invoice date so every
        # invoice carries its operational-year identity from creation onward.
        invoice_dt = data.invoice_date
        invoice_local_date = (
            invoice_dt.astimezone(timezone.utc).date()
            if invoice_dt.tzinfo is not None
            else invoice_dt.date()
        )
        op_cfg = await operational_year_service.get_config(db)
        invoice_year = operational_year_service.current_year(invoice_local_date, op_cfg)
        current_year = operational_year_service.current_year(date.today(), op_cfg)

        invoice = Invoice(
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            admission_id=data.admission_id,
            invoice_number=await number_sequence_service.next_number(db, "invoice_number"),
            invoice_date=data.invoice_date,
            total_amount=data.total_amount,
            payment_status="unpaid",
            invoice_year=invoice_year,
            storage_tier="live",
            is_current_year=invoice_year == current_year,
            generated_by=generated_by,
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            invoice = await self.invoice_repo.add(
                db,
                invoice,
            )

            await db.commit()

            return invoice

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create invoice."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create invoice."
            ) from exc

    async def update_invoice(
        self,
        db: AsyncSession,
        *,
        invoice_id: int,
        data: InvoiceUpdate,
    ) -> Invoice:
        invoice = await self.get_invoice(
            db,
            invoice_id,
        )

        if invoice.payment_status == "paid":
            raise BusinessRuleException(
                "A fully paid invoice cannot be modified."
            )

        values = data.model_dump(
            exclude_unset=True,
        )

        values.pop("payment_status", None)

        if "total_amount" in values:
            total_paid = (
                await self.payment_repo.total_paid(
                    db,
                    invoice_id,
                )
            )

            if values["total_amount"] < total_paid:
                raise BusinessRuleException(
                    "Invoice total cannot be less "
                    "than the amount already paid."
                )

        for field, value in values.items():
            setattr(
                invoice,
                field,
                value,
            )

        invoice.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            invoice = await self.invoice_repo.update(
                db,
                invoice,
            )

            await db.commit()

            return invoice

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update invoice."
            ) from exc

    async def get_payment(
        self,
        db: AsyncSession,
        payment_id: int,
    ) -> Payment:
        payment = await self.payment_repo.get_by_id(
            db,
            payment_id,
        )

        if payment is None:
            raise ResourceNotFoundException(
                "Payment not found."
            )

        return payment

    async def list_payments(
        self,
        db: AsyncSession,
        invoice_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        invoice = await self.get_invoice(
            db,
            invoice_id,
        )

        return await self.payment_repo.list_by_invoice(
            db,
            invoice.id,
            skip=skip,
            limit=limit,
        )

    async def create_payment(
        self,
        db: AsyncSession,
        data: PaymentCreate,
        received_by: int,
    ) -> Payment:
        invoice_result = await db.execute(
            select(Invoice)
            .where(Invoice.id == data.invoice_id)
            .with_for_update()
        )
        invoice = invoice_result.scalar_one_or_none()
        if invoice is None:
            raise ResourceNotFoundException("Invoice not found.")

        if invoice.payment_status == "cancelled":
            raise BusinessRuleException(
                "Payment cannot be recorded against "
                "a cancelled invoice."
            )

        if invoice.payment_status == "paid":
            raise BusinessRuleException(
                "Invoice is already fully paid."
            )

        total_paid = (
            await self.payment_repo.total_paid(
                db,
                invoice.id,
            )
        )

        balance = (
            invoice.total_amount - total_paid
        )

        if data.amount_paid > balance:
            raise BusinessRuleException(
                "Payment amount cannot exceed "
                "the outstanding invoice balance."
            )

        now = datetime.now(timezone.utc)

        # Derive the annual lifecycle fields from the payment timestamp so
        # every payment carries its operational-year identity from creation.
        payment_dt = data.payment_datetime
        payment_local_date = (
            payment_dt.astimezone(timezone.utc).date()
            if payment_dt.tzinfo is not None
            else payment_dt.date()
        )
        op_cfg = await operational_year_service.get_config(db)
        payment_year = operational_year_service.current_year(payment_local_date, op_cfg)
        current_year = operational_year_service.current_year(date.today(), op_cfg)

        payment = Payment(
            invoice_id=invoice.id,
            receipt_number=await number_sequence_service.next_number(db, "receipt_number"),
            payment_datetime=(
                data.payment_datetime
            ),
            payment_method=data.payment_method,
            payment_year=payment_year,
            storage_tier="live",
            is_current_year=payment_year == current_year,
            amount_paid=data.amount_paid,
            received_by=received_by,
            transaction_reference=(
                data.transaction_reference
            ),
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            payment = await self.payment_repo.add(
                db,
                payment,
            )

            new_total_paid = (
                total_paid + data.amount_paid
            )

            if new_total_paid >= invoice.total_amount:
                invoice.payment_status = "paid"

            else:
                invoice.payment_status = "partial"

            invoice.updated_at = now

            await self.invoice_repo.update(
                db,
                invoice,
            )

            await db.commit()

            return payment

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create payment."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create payment."
            ) from exc


    async def list_invoice_items(self, db: AsyncSession, invoice_id: int) -> list[InvoiceItem]:
        await self.get_invoice(db, invoice_id)
        return await invoice_item_repository.list_by_invoice(db, invoice_id)

    async def _recalculate_invoice_total(self, db: AsyncSession, invoice: Invoice) -> None:
        result = await db.execute(
            select(func.coalesce(func.sum(InvoiceItem.line_total), 0)).where(
                InvoiceItem.invoice_id == invoice.id
            )
        )
        invoice.total_amount = Decimal(str(result.scalar_one()))
        invoice.updated_at = datetime.now(timezone.utc)

    async def add_invoice_item(self, db: AsyncSession, invoice_id: int, data: InvoiceItemCreate) -> InvoiceItem:
        invoice_result = await db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .with_for_update()
        )
        invoice = invoice_result.scalar_one_or_none()
        if invoice is None:
            raise ResourceNotFoundException("Invoice not found.")
        if invoice.payment_status == "cancelled":
            raise BusinessRuleException("A cancelled invoice cannot be modified.")
        if invoice.payment_status == "paid":
            raise BusinessRuleException("A fully paid invoice cannot be modified.")
        now = datetime.now(timezone.utc)
        quantity = Decimal(data.quantity)
        unit_price = Decimal(data.unit_price)
        item = InvoiceItem(
            invoice_id=invoice.id,
            item_type=data.item_type,
            description=data.description,
            quantity=quantity,
            unit_price=unit_price,
            line_total=(quantity * unit_price).quantize(Decimal("0.01")),
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )
        try:
            db.add(item)
            await db.flush()
            await self._recalculate_invoice_total(db, invoice)
            total_paid = await self.payment_repo.total_paid(db, invoice.id)
            invoice.payment_status = (
                "paid" if total_paid >= invoice.total_amount
                else "partial" if total_paid > 0
                else "unpaid"
            )
            await db.commit()
            await db.refresh(item)
            return item
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to add invoice item.") from exc

    async def delete_invoice_item(self, db: AsyncSession, item_id: int) -> None:
        item = await db.get(InvoiceItem, item_id)
        if item is None:
            raise ResourceNotFoundException("Invoice item not found.")
        invoice_result = await db.execute(
            select(Invoice)
            .where(Invoice.id == item.invoice_id)
            .with_for_update()
        )
        invoice = invoice_result.scalar_one_or_none()
        if invoice is None:
            raise ResourceNotFoundException("Invoice not found.")
        if invoice.payment_status == "cancelled":
            raise BusinessRuleException("A cancelled invoice cannot be modified.")
        if invoice.payment_status == "paid":
            raise BusinessRuleException("A fully paid invoice cannot be modified.")
        total_paid = await self.payment_repo.total_paid(db, invoice.id)
        prospective_total = invoice.total_amount - item.line_total
        if prospective_total < total_paid:
            raise BusinessRuleException(
                "Invoice item cannot be removed because the remaining total "
                "would be less than the amount already paid."
            )
        try:
            await db.delete(item)
            await db.flush()
            await self._recalculate_invoice_total(db, invoice)
            invoice.payment_status = (
                "paid" if total_paid >= invoice.total_amount
                else "partial" if total_paid > 0
                else "unpaid"
            )
            await db.commit()
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to delete invoice item.") from exc

    async def invoice_summary(
        self,
        db: AsyncSession,
        invoice_id: int,
    ) -> tuple[Invoice, Decimal, Decimal]:
        invoice = await self.get_invoice(
            db,
            invoice_id,
        )

        total_paid = (
            await self.payment_repo.total_paid(
                db,
                invoice_id,
            )
        )

        balance = max(
            invoice.total_amount - total_paid,
            Decimal("0"),
        )

        return (
            invoice,
            total_paid,
            balance,
        )


billing_service = BillingService()


__all__ = [
    "BillingService",
    "billing_service",
]