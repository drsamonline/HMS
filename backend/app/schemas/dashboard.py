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


class PendingInvestigationItem(BaseSchema):
    """One live investigation awaiting laboratory results."""

    investigation_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    case_type: str | None = None
    visit_id: int | None = None
    admission_id: int | None = None
    investigation_number: str
    investigation_name: str
    investigation_status: str
    requested_datetime: datetime
    requested_by: int
    age_hours: int


class PendingInvestigationsResponse(BaseSchema):
    """Pending-investigation list plus headline laboratory workload counts."""

    as_of: datetime
    items: list[PendingInvestigationItem]
    pending_count: int
    in_progress_count: int


class ReceivablesAgingBucket(BaseSchema):
    """One age bucket of the outstanding receivables ledger.

    ``lower_days``/``upper_days`` describe the invoice-age window (days from
    ``invoice_date`` to today, inclusive-exclusive); a negative upper bound
    marks the open-ended oldest bucket.
    """

    label: str
    lower_days: int
    upper_days: int | None
    invoice_count: int
    total_outstanding: Decimal


class ReceivablesAgingItem(BaseSchema):
    """One outstanding invoice placed into an aging bucket."""

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
    bucket_label: str


class ReceivablesAgingResponse(BaseSchema):
    """Receivables aging ledger with per-bucket and headline aggregates."""

    as_of: date
    currency_note: str | None = None
    buckets: list[ReceivablesAgingBucket]
    items: list[ReceivablesAgingItem]
    invoice_count: int
    total_outstanding: Decimal


__all__ = [
    "DueFollowUpItem",
    "DueFollowUpsResponse",
    "OutstandingInvoiceItem",
    "OutstandingInvoicesResponse",
    "BedOccupancyItem",
    "BedOccupancyResponse",
    "PendingInvestigationItem",
    "PendingInvestigationsResponse",
    "ReceivablesAgingBucket",
    "ReceivablesAgingItem",
    "ReceivablesAgingResponse",
]
