"""HHMS clinician dashboard schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app.schemas.base import BaseSchema


class DueFollowUpItem(BaseSchema):
    """One follow-up scheduled to be seen inside the dashboard due window."""

    followup_id: int
    case_record_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    case_number: str | None = None
    next_followup_datetime: datetime
    previous_prescription_id: int | None = None
    decision: str | None = None


class DueFollowUpsResponse(BaseSchema):
    """Due-follow-up list plus the window bounds actually applied."""

    from_datetime: datetime
    to_datetime: datetime
    items: list[DueFollowUpItem]


class OutstandingInvoiceItem(BaseSchema):
    """One unpaid/partial invoice with its derived outstanding balance."""

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    payment_status: str
    days_outstanding: int


class OutstandingInvoicesResponse(BaseSchema):
    """Outstanding-invoice list plus the aggregate receivable figures."""

    as_of: date
    items: list[OutstandingInvoiceItem]
    total_outstanding: Decimal
    invoice_count: int


class BedOccupancyItem(BaseSchema):
    """One occupied/reserved bed reconciled against its active admission."""

    bed_id: int
    bed_number: str
    ward: str | None = None
    room_number: str | None = None
    bed_type: str | None = None
    occupancy_status: str
    has_active_admission: bool
    admission_id: int | None = None
    admission_number: str | None = None
    admission_datetime: datetime | None = None
    admission_status: str | None = None
    patient_id: int | None = None
    patient_name: str | None = None
    patient_number: str | None = None
    length_of_stay_days: int | None = None


class BedOccupancyResponse(BaseSchema):
    """Ward occupancy list plus headline inpatient counts."""

    as_of: datetime
    items: list[BedOccupancyItem]
    occupied_count: int
    total_beds: int


__all__ = [
    "DueFollowUpItem",
    "DueFollowUpsResponse",
    "OutstandingInvoiceItem",
    "OutstandingInvoicesResponse",
    "BedOccupancyItem",
    "BedOccupancyResponse",
]
