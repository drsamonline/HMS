"""
HHMS Billing Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


PaymentStatus = Literal[
    "unpaid",
    "partial",
    "paid",
    "cancelled",
]


PaymentMethod = Literal[
    "cash",
    "card",
    "upi",
    "bank_transfer",
    "cheque",
    "other",
]


class InvoiceCreate(BaseSchema):
    patient_id: int = Field(gt=0)

    visit_id: int | None = Field(
        default=None,
        gt=0,
    )

    admission_id: int | None = Field(
        default=None,
        gt=0,
    )

    invoice_date: datetime

    total_amount: Decimal = Field(
        ge=0,
    )

    remarks: str | None = None


class InvoiceUpdate(BaseSchema):
    total_amount: Decimal | None = Field(
        default=None,
        ge=0,
    )

    remarks: str | None = None

    payment_status: PaymentStatus | None = None


class InvoiceRead(BaseSchema):
    id: int
    patient_id: int
    visit_id: int | None
    admission_id: int | None
    invoice_number: str
    invoice_date: datetime
    total_amount: Decimal
    payment_status: str
    invoice_year: int
    storage_tier: str
    is_current_year: bool
    generated_by: int
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class PaymentCreate(BaseSchema):
    invoice_id: int = Field(gt=0)

    payment_datetime: datetime

    payment_method: PaymentMethod

    # Batch 100 — negative amounts record refunds/adjustments against a
    # live invoice. Zero is never meaningful; the service layer guards
    # that refunds cannot exceed the amount collected.
    amount_paid: Decimal = Field(
        ne=0,
    )

    transaction_reference: str | None = Field(
        default=None,
        max_length=100,
    )

    remarks: str | None = None


class PaymentRead(BaseSchema):
    id: int
    invoice_id: int | None
    receipt_number: str
    payment_datetime: datetime
    payment_method: str
    payment_year: int
    storage_tier: str
    is_current_year: bool
    amount_paid: Decimal
    received_by: int
    transaction_reference: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class InvoiceSummary(BaseSchema):
    invoice: InvoiceRead
    total_paid: Decimal
    balance_amount: Decimal


class InvoiceItemCreate(BaseSchema):
    item_type: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    remarks: str | None = None


class InvoiceItemRead(BaseSchema):
    id: int
    invoice_id: int
    item_type: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "PaymentStatus",
    "PaymentMethod",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceRead",
    "PaymentCreate",
    "PaymentRead",
    "InvoiceSummary",
    "InvoiceItemCreate",
    "InvoiceItemRead",
]