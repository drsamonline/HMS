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


class InvoiceReceiptGapItem(BaseSchema):
    """One invoice whose receipt numbering has a continuity defect.

    ``gap_type`` is one of ``missing`` (no receipts recorded against the
    invoice), ``duplicate`` (the same receipt number appears more than once)
    or ``sequence_break`` (a numeric receipt series skips at least one
    number between its first and last receipt for this invoice).
    """

    invoice_id: int
    invoice_number: str
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    gap_type: str
    expected_count: int
    actual_count: int
    missing_count: int
    first_receipt_number: str | None = None
    last_receipt_number: str | None = None
    duplicate_receipt_numbers: list[str] = []


class InvoiceReceiptContinuityResponse(BaseSchema):
    """Invoice-to-receipt continuity audit with headline aggregates."""

    as_of: datetime
    invoices_checked: int
    invoices_with_receipts: int
    invoices_missing_receipts: int
    duplicate_receipt_count: int
    sequence_break_count: int
    issues: list[InvoiceReceiptGapItem]


class ReceiptSeriesGap(BaseSchema):
    """Numbering-continuity state of one receipt-number series.

    Batch 88 — whole-receipt-book audit. A *series* is every receipt sharing
    the same non-digit prefix (e.g. ``R`` in ``R000123``). ``expected_count``
    spans first..last numeric value inclusive, so per-series reconciliation
    always holds: ``expected_count == actual_count + gap_count``.
    """

    prefix: str
    first_number: int
    last_number: int
    expected_count: int
    actual_count: int
    gap_count: int
    missing_numbers: list[int]
    duplicate_numbers: list[str]


class ReceiptNumberingContinuityResponse(BaseSchema):
    """Whole-book receipt numbering continuity audit with aggregates."""

    as_of: datetime
    receipts_checked: int
    series_count: int
    clean_series_count: int
    total_gap_count: int
    series: list[ReceiptSeriesGap]


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
    "InvoiceReceiptGapItem",
    "InvoiceReceiptContinuityResponse",
    "ReceiptSeriesGap",
    "ReceiptNumberingContinuityResponse",
]
