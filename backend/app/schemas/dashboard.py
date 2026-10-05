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


class WardOccupancySummaryItem(BaseSchema):
    """One ward's occupancy rollup for the ward-clarity dashboard feed.

    Batch 101 — every active bed (occupied, reserved or available) is
    bucketed under its ward name; beds with no ward assigned surface under
    the explicit ``"Unassigned"`` label instead of silently disappearing.
    The split invariant ``occupied_beds + reserved_beds + available_beds ==
    total_beds`` holds on every row by construction, and
    ``active_admissions <= occupied_beds`` because a live admission can
    only attach to a bed marked occupied (reserved beds are pre-admission
    bookings without a linked episode yet).
    """

    ward: str
    total_beds: int
    occupied_beds: int
    reserved_beds: int
    available_beds: int
    active_admissions: int
    longest_stay_days: int | None = None


class WardOccupancySummaryResponse(BaseSchema):
    """Per-ward occupancy rollup plus hospital-wide headline counts.

    Headlines satisfy ``total_occupied + total_reserved + total_available
    == total_beds`` so the ward table always foots against the master bed
    ledger it is derived from.
    """

    as_of: datetime
    items: list[WardOccupancySummaryItem]
    wards_reported: int
    total_beds: int
    total_occupied: int
    total_reserved: int
    total_available: int
    total_active_admissions: int


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


class InvoicePaymentReconciliationItem(BaseSchema):
    """One invoice reconciled against the live Payment ledger.

    Batch 89 — billing reconciliation feed. ``total_paid`` is summed from
    live payments and clamped to ``total_amount``, so the invariant
    ``amount_paid + balance_due == total_amount`` always holds (Batch 68
    atomic-consistency parity). ``receipt_count`` counts the receipts in the
    same single grouped payment pass, and ``is_reconciled`` marks rows whose
    derived status agrees with the stored ``payment_status`` column.
    """

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    stored_payment_status: str
    derived_payment_status: str
    receipt_count: int
    is_reconciled: bool


class InvoicePaymentReconciliationResponse(BaseSchema):
    """Invoice-payment reconciliation ledger with headline aggregates.

    ``paid_invoices + partially_paid_invoices + unpaid_invoices`` always sums
    back to ``invoices_checked`` so printed reconciliation ledgers reconcile
    line-by-line.
    """

    as_of: date
    invoices_checked: int
    paid_invoices: int
    partially_paid_invoices: int
    unpaid_invoices: int
    total_billed: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    items: list[InvoicePaymentReconciliationItem]


class PatientCollectionSummaryItem(BaseSchema):
    """One patient's collection totals rolled up from the Batch 89 ledger.

    Batch 90 — collection summary by patient. Every figure is derived from
    the live Payment ledger via the shared reconciliation aggregation (never
    from stored counters), so printed collection summaries always satisfy
    ``total_collected + outstanding == total_billed`` per patient, with each
    invoice's clamped paid amount contributing exactly once.
    """

    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_count: int
    paid_invoice_count: int
    partial_invoice_count: int
    unpaid_invoice_count: int
    total_billed: Decimal
    total_collected: Decimal
    outstanding: Decimal
    last_payment_date: datetime | None = None


class PatientCollectionSummaryResponse(BaseSchema):
    """Collection summary grouped by patient with headline aggregates.

    ``patients_with_outstanding`` counts patients whose derived outstanding
    balance is positive; the per-patient rows sum back to the headline
    totals so printed collection packets reconcile line-by-line.
    """

    as_of: date
    invoices_checked: int
    patients_checked: int
    patients_with_outstanding: int
    total_billed: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    items: list[PatientCollectionSummaryItem]


class PaymentMethodSummaryItem(BaseSchema):
    """One payment method's collection totals within the scan window.

    Batch 96 — payment-method collection summary. Derived from live
    ``Payment`` rows joined to non-cancelled invoices (stored counters
    never trusted); per-invoice amounts keep the Batch 68 clamp invariant,
    so each receipt's collected contribution is counted exactly once and
    the per-method figures sum back to the headline ``total_collected``.
    ``share_of_total`` is a percentage (0-100) of the scanned-window
    collected total.
    """

    payment_method: str
    receipt_count: int
    invoice_count: int
    gross_received: Decimal
    collected: Decimal
    share_of_total: Decimal


class PaymentMethodSummaryResponse(BaseSchema):
    """Collection summary grouped by payment method with headlines.

    Headline aggregates always satisfy
    ``sum(per-method collected) == total_collected`` so printed payment
    packets reconcile line-by-line for the same scan window.
    """

    as_of: date
    invoices_checked: int
    receipts_scanned: int
    methods_reported: int
    total_collected: Decimal
    items: list[PaymentMethodSummaryItem]


class InvoiceOverpaymentItem(BaseSchema):
    """One invoice whose live payment ledger exceeds the billed amount.

    Batch 97 — overpayment detection feed. ``total_paid_raw`` is summed from
    the live Payment ledger *without* the Batch 68 clamp, so the invariant
    ``overpaid_amount == total_paid_raw - total_amount`` holds on every row
    and ``balance_due`` is always zero for an overpaid invoice. ``amount_paid``
    keeps the clamped value used by the reconciliation ledger (Batch 89) so
    both surfaces agree line-for-line; ``stored_payment_status`` /
    ``derived_payment_status`` / ``receipt_count`` are carried along for
    context.
    """

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    total_paid_raw: Decimal
    overpaid_amount: Decimal
    stored_payment_status: str
    derived_payment_status: str
    receipt_count: int
    is_reconciled: bool


class InvoiceOverpaymentResponse(BaseSchema):
    """Invoice overpayment ledger with headline aggregates.

    Batch 97 — only invoices with ``overpaid_amount > 0`` appear, so
    ``invoices_checked == invoices_overpaid == len(items)`` and
    ``total_paid_raw == total_billed + total_overpaid`` by construction.
    """

    as_of: date
    invoices_checked: int
    invoices_overpaid: int
    total_billed: Decimal
    total_paid_raw: Decimal
    total_overpaid: Decimal
    items: list[InvoiceOverpaymentItem]


class PaymentMethodOverpaymentItem(BaseSchema):
    """One payment method's over-collection split within the scan window.

    Batch 98 — payment-method overpayment breakdown. Reuses the exact
    chronological clamp of the Batch 96 collection summary: ``collected``
    is the amount absorbed by in-window invoice balances (Batch 68 clamp
    parity) and ``overpaid`` is the remainder of ``gross_received`` that
    exceeded those balances, so ``gross_received == collected + overpaid``
    holds on every row. ``share_of_total`` stays a percentage (0-100) of
    the scanned-window *collected* total for line-for-line parity with the
    Batch 96 summary.
    """

    payment_method: str
    receipt_count: int
    invoice_count: int
    gross_received: Decimal
    collected: Decimal
    share_of_total: Decimal
    overpaid: Decimal


class PaymentMethodOverpaymentResponse(BaseSchema):
    """Per-method overpayment breakdown with headline aggregates.

    Batch 98 — headline aggregates always satisfy
    ``total_gross == total_collected + total_overpaid`` and
    ``sum(per-method overpaid) == total_overpaid`` so printed breakdowns
    reconcile line-by-line for the same scan window.
    """

    as_of: date
    invoices_checked: int
    receipts_scanned: int
    methods_reported: int
    methods_with_overpayment: int
    total_gross: Decimal
    total_collected: Decimal
    total_overpaid: Decimal
    items: list[PaymentMethodOverpaymentItem]


class DischargeAuditItem(BaseSchema):
    """One recent discharge reconciled against its admission and bed state.

    Batch 99 — surfaces what the bed-occupancy feed cannot: the ward's
    discharge flow itself. The live workflow marks an admission
    ``discharged`` and frees its bed when the discharge record is created,
    so this audit proves each discharge reconciles line-for-line:
    ``admission_status`` should read ``discharged`` and
    ``bed_occupancy_status`` should read ``available``. Every row carries
    ``is_reconciled`` plus the individual flags, and
    ``hours_since_discharge`` measures how long ago the order was placed so
    stale or drifted rows surface instead of silently disappearing.
    """

    discharge_id: int
    discharge_number: str
    discharge_datetime: datetime
    discharge_status: str
    discharged_by: int
    admission_id: int
    admission_number: str
    admission_status: str
    admission_discharged: bool
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    bed_id: int | None = None
    bed_number: str | None = None
    ward: str | None = None
    bed_occupancy_status: str | None = None
    bed_freed: bool
    hours_since_discharge: int
    is_reconciled: bool


class DischargeAuditResponse(BaseSchema):
    """Discharge audit rows plus headline reconciliation counts."""

    as_of: datetime
    items: list[DischargeAuditItem]
    total_discharges: int
    reconciled_count: int
    drift_count: int


class OPDQueueSummaryItem(BaseSchema):
    """One day's OPD token queue as an operational summary row.

    Batch 99 — one row per ``queue_date`` (newest first). Every figure is
    derived from live ``OPDToken`` rows in a single grouped pass; the
    invariant ``waiting + in_consultation + completed + cancelled ==
    total_tokens`` always holds, so the open backlog
    (``open_token_count``) reconciles line-for-line with the status split.
    """

    queue_date: date
    total_tokens: int
    waiting: int
    in_consultation: int
    completed: int
    cancelled: int
    open_token_count: int


class OPDQueueSummaryResponse(BaseSchema):
    """Queue-day summaries plus aggregate workload figures."""

    as_of: datetime
    items: list[OPDQueueSummaryItem]
    days_reported: int
    total_tokens: int
    total_open: int


class InvoiceSettlementAuditItem(BaseSchema):
    """One invoice reconciled against its live payment ledger.

    Batch 100 — settlement continuity feed. ``total_paid`` is derived from
    the live Payment rows only (stored counters and status columns are
    never trusted), clamped to the invoice total per the Batch 68 rule, so
    every row satisfies ``settled_amount + outstanding_amount ==
    total_amount`` line-for-line. ``is_cleared`` marks invoices whose
    collected amount covers the billed total; everything else is unsettled
    and carries a positive ``outstanding_amount``.
    """

    invoice_id: int
    invoice_number: str
    invoice_date: datetime
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    total_amount: Decimal
    total_paid: Decimal
    settled_amount: Decimal
    outstanding_amount: Decimal
    overpayment_amount: Decimal
    payment_count: int
    refund_count: int
    stored_payment_status: str
    derived_payment_status: str
    status_matches: bool
    is_cleared: bool


class InvoiceSettlementAuditResponse(BaseSchema):
    """Settlement audit rows plus headline cleared/unsettled counts.

    Headline invariant (Batch 100): ``total_collected +
    total_outstanding == total_billed + total_overpaid`` — clamped
    collections plus visible over-collection always reconcile back to the
    billed total, so money never silently disappears on paper or screen.
    """

    as_of: date
    items: list[InvoiceSettlementAuditItem]
    total_invoices: int
    cleared_count: int
    unsettled_count: int
    total_billed: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    total_overpaid: Decimal


class RefundAuditItem(BaseSchema):
    """One negative Payment ledger entry inspected for processing drift.

    Batch 100 — refund processing audit. Negative ``amount_paid`` entries
    are refunds/adjustments against a live invoice. A refund is
    ``processing_complete`` when it links to an existing invoice, carries
    a non-empty remarks note explaining the adjustment, and leaves the
    invoice's net collections non-negative (the service guard from the
    refund posting rules). Drifted rows keep appearing with the individual
    flags false instead of silently disappearing.
    """

    payment_id: int
    receipt_number: str
    payment_datetime: datetime
    payment_method: str
    refund_amount: Decimal
    invoice_id: int | None
    invoice_number: str | None
    invoice_total_amount: Decimal | None
    invoice_net_paid: Decimal | None
    received_by: int
    has_remarks: bool
    invoice_exists: bool
    net_non_negative: bool
    processing_complete: bool


class RefundAuditResponse(BaseSchema):
    """Refund audit rows plus headline processed/drifted counts."""

    as_of: date
    items: list[RefundAuditItem]
    total_refunds: int
    processed_count: int
    drifted_count: int
    total_refunded: Decimal


class InvestigationBillingReconciliationItem(BaseSchema):
    """One open investigation reconciled against live invoice billing.

    ``billed_amount`` is re-derived from ``InvoiceItem`` line totals matched
    to the investigation (never trusted from any stored counter), so every
    row satisfies ``billed_amount == charged_total - credited_total``.
    Unbilled orders surface with ``billed_amount == 0`` and
    ``is_billed_missing`` set instead of disappearing from the ledger.
    """

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
    age_hours: int
    billed_amount: Decimal
    charged_total: Decimal
    credited_total: Decimal
    invoice_item_count: int
    is_billed: bool
    is_billed_missing: bool


class InvestigationBillingReconciliationResponse(BaseSchema):
    """Investigation billing ledger rows plus headline reconciliation totals.

    Headlines satisfy ``pending_count + in_progress_count ==
    total_investigations_checked`` and ``billed_count + billed_missing_count
    == total_investigations_checked``, so the laboratory backlog foots
    line-for-line against the billing side.
    """

    as_of: datetime
    currency_note: str | None = None
    items: list[InvestigationBillingReconciliationItem]
    total_investigations_checked: int
    pending_count: int
    in_progress_count: int
    billed_count: int
    billed_missing_count: int
    total_billed: Decimal


__all__ = [
    "DueFollowUpItem",
    "DueFollowUpsResponse",
    "OutstandingInvoiceItem",
    "OutstandingInvoicesResponse",
    "BedOccupancyItem",
    "BedOccupancyResponse",
    "WardOccupancySummaryItem",
    "WardOccupancySummaryResponse",
    "PendingInvestigationItem",
    "PendingInvestigationsResponse",
    "ReceivablesAgingBucket",
    "ReceivablesAgingItem",
    "ReceivablesAgingResponse",
    "InvoiceReceiptGapItem",
    "InvoiceReceiptContinuityResponse",
    "ReceiptSeriesGap",
    "ReceiptNumberingContinuityResponse",
    "InvoicePaymentReconciliationItem",
    "InvoicePaymentReconciliationResponse",
    "InvoiceOverpaymentItem",
    "InvoiceOverpaymentResponse",
    "PatientCollectionSummaryItem",
    "PatientCollectionSummaryResponse",
    "PaymentMethodSummaryItem",
    "PaymentMethodSummaryResponse",
    "PaymentMethodOverpaymentItem",
    "PaymentMethodOverpaymentResponse",
    "DischargeAuditItem",
    "DischargeAuditResponse",
    "OPDQueueSummaryItem",
    "OPDQueueSummaryResponse",
    "InvoiceSettlementAuditItem",
    "InvoiceSettlementAuditResponse",
    "RefundAuditItem",
    "RefundAuditResponse",
    "InvestigationBillingReconciliationItem",
    "InvestigationBillingReconciliationResponse",
]
