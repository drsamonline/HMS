"""
HHMS Billing Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

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
from app.models.patient import Patient
from app.models.payment import Payment
from app.models.visit import Visit
from app.repositories.billing import (
    InvoiceRepository,
    PaymentRepository,
    invoice_repository,
    payment_repository,
)
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceUpdate,
    PaymentCreate,
)


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

        invoice = Invoice(
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            admission_id=data.admission_id,
            invoice_number="PENDING",
            invoice_date=data.invoice_date,
            total_amount=data.total_amount,
            payment_status="unpaid",
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

            invoice.invoice_number = (
                f"INV-{invoice.id:06d}"
            )

            await self.invoice_repo.update(
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
        invoice = await self.get_invoice(
            db,
            data.invoice_id,
        )

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

        payment = Payment(
            invoice_id=invoice.id,
            receipt_number="PENDING",
            payment_datetime=(
                data.payment_datetime
            ),
            payment_method=data.payment_method,
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

            payment.receipt_number = (
                f"RCT-{payment.id:06d}"
            )

            await self.payment_repo.update(
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