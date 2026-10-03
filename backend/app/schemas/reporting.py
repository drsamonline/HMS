"""HHMS reporting and print-selection schemas."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema

ReportSection = Literal[
    "patient",
    "case_record",
    "admission",
    "diagnosis",
    "followups",
    "prescriptions",
    "investigations",
    "ipd_assessment",
    "pain_assessments",
    "nutritional_assessment",
    "diet_charts",
    "progress_notes",
    "discharge",
    "dispensations",
    "billing",
    "payments",
    "medical_documents",
    "mrd",
]

ALL_REPORT_SECTIONS: tuple[str, ...] = (
    "patient",
    "case_record",
    "admission",
    "diagnosis",
    "followups",
    "prescriptions",
    "investigations",
    "ipd_assessment",
    "pain_assessments",
    "nutritional_assessment",
    "diet_charts",
    "progress_notes",
    "discharge",
    "dispensations",
    "billing",
    "payments",
    "medical_documents",
    "mrd",
)

class ClinicalReportRequest(BaseSchema):
    patient_id: int | None = Field(default=None, gt=0)
    case_record_id: int | None = Field(default=None, gt=0)
    admission_id: int | None = Field(default=None, gt=0)
    sections: list[ReportSection] = Field(default_factory=list, max_length=len(ALL_REPORT_SECTIONS))
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ClinicalReportRequest":
        if self.patient_id is None and self.case_record_id is None and self.admission_id is None:
            raise ValueError("patient_id, case_record_id, or admission_id is required.")
        if self.start_datetime and self.end_datetime and self.start_datetime > self.end_datetime:
            raise ValueError("start_datetime must not be later than end_datetime.")
        return self

class ClinicalReportRead(BaseSchema):
    report_type: Literal["clinical"] = "clinical"
    patient_id: int
    case_record_id: int | None = None
    admission_id: int | None = None
    sections: list[str]
    data: dict

class ClinicalReportBatchRequest(BaseSchema):
    start_datetime: datetime
    end_datetime: datetime
    patient_id: int | None = Field(default=None, gt=0)
    case_status: Literal["draft", "active", "closed"] | None = None
    sections: list[ReportSection] = Field(default_factory=list, max_length=len(ALL_REPORT_SECTIONS))
    limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_range(self) -> "ClinicalReportBatchRequest":
        if self.start_datetime > self.end_datetime:
            raise ValueError("start_datetime must not be later than end_datetime.")
        return self

class ClinicalReportBatchItem(BaseSchema):
    case_record_id: int
    patient_id: int
    case_number: str
    case_status: str
    report: ClinicalReportRead

class ClinicalReportBatchRead(BaseSchema):
    report_type: Literal["clinical_batch"] = "clinical_batch"
    start_datetime: datetime
    end_datetime: datetime
    count: int = Field(ge=0)
    truncated: bool = False
    reports: list[ClinicalReportBatchItem]

class ReportCatalogItem(BaseSchema):
    key: str
    label: str
    description: str
    available_for: list[str]

class ReportCatalogRead(BaseSchema):
    report_type: Literal["catalog"] = "catalog"
    sections: list[ReportCatalogItem]


class ReportPrintBlock(BaseSchema):
    section: str
    label: str
    page_group: str
    print_order: int = Field(ge=1)
    page_break_before: bool = False
    available: bool = True

class ReportPrintManifestRequest(ClinicalReportRequest):
    title: str | None = Field(default=None, max_length=200)

class ReportPrintManifestRead(BaseSchema):
    report_type: Literal["print_manifest"] = "print_manifest"
    title: str
    generated_at: datetime
    patient_id: int
    case_record_id: int | None = None
    admission_id: int | None = None
    print_scope: Literal["complete_case", "selected_sections"]
    blocks: list[ReportPrintBlock]

class ReportPrintEnvelope(BaseSchema):
    report_type: Literal["clinical_print"] = "clinical_print"
    title: str
    generated_at: datetime
    patient_id: int
    case_record_id: int | None = None
    admission_id: int | None = None
    selected_sections: list[str]
    available_sections: list[str]
    report: ClinicalReportRead

class ReportPrintEnvelopeRequest(ClinicalReportRequest):
    title: str | None = Field(default=None, max_length=200)


class InvoicePrintRequest(BaseSchema):
    invoice_id: int = Field(gt=0)
    title: str | None = Field(default=None, max_length=200)


class InvoicePrintItemLine(BaseSchema):
    id: int
    item_type: str
    description: str
    quantity: str
    unit_price: str
    line_total: str
    remarks: str | None = None


class InvoicePrintReceiptLine(BaseSchema):
    id: int
    receipt_number: str
    payment_datetime: str
    payment_method: str
    amount_paid: str
    transaction_reference: str | None = None
    remarks: str | None = None


class InvoicePrintData(BaseSchema):
    invoice: dict
    items: list[InvoicePrintItemLine]
    receipts: list[InvoicePrintReceiptLine]
    patient: dict
    total_amount: str
    amount_paid: str
    balance_due: str
    payment_status: str
    generated_at: datetime


class InvoicePrintEnvelope(BaseSchema):
    report_type: Literal["invoice_print"] = "invoice_print"
    title: str
    generated_at: datetime
    invoice_id: int
    invoice_number: str
    patient_id: int
    data: InvoicePrintData


class CollectionSummaryPrintRequest(BaseSchema):
    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class PatientCollectionSummaryPrintLine(BaseSchema):
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_count: int
    paid_invoice_count: int
    partial_invoice_count: int
    unpaid_invoice_count: int
    total_billed: str
    total_collected: str
    outstanding: str
    last_payment_date: str | None = None


class CollectionSummaryPrintData(BaseSchema):
    as_of: date
    invoices_checked: int
    patients_checked: int
    patients_with_outstanding: int
    total_billed: str
    total_collected: str
    total_outstanding: str
    items: list[PatientCollectionSummaryPrintLine]


class CollectionSummaryPrintEnvelope(BaseSchema):
    """Batch 90 — printable per-patient collection summary packet.

    Built from the same live-payment reconciliation scan as the dashboard
    feed (shared aggregation), so printed figures always satisfy
    ``total_collected + total_outstanding == total_billed``.
    """

    report_type: Literal["collection_summary_print"] = "collection_summary_print"
    title: str
    generated_at: datetime
    data: CollectionSummaryPrintData


class ReceivablesAgingPrintRequest(BaseSchema):
    """Batch 91 — print request for the receivables aging ledger."""

    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class ReceivablesAgingBucketPrintLine(BaseSchema):
    """One aging band in the printed ledger; always present even when empty."""

    label: str
    lower_days: int
    upper_days: int | None = None
    invoice_count: int
    total_outstanding: str


class ReceivablesAgingInvoicePrintLine(BaseSchema):
    """One live-derived outstanding invoice placed in an aging bucket."""

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: str
    amount_paid: str
    balance_due: str
    payment_status: str
    days_outstanding: int
    bucket_label: str


class ReceivablesAgingPrintData(BaseSchema):
    as_of: date
    buckets: list[ReceivablesAgingBucketPrintLine]
    items: list[ReceivablesAgingInvoicePrintLine]
    invoice_count: int
    total_outstanding: str


class ReceivablesAgingPrintEnvelope(BaseSchema):
    """Batch 91 — printable receivables aging packet.

    Built through the exact same ``build_receivables_aging_result`` code path
    as the dashboard feed (single grouped Payment pass, Batch 68 clamp
    invariant), so printed bucket totals always reconcile with the screen:
    bucket counts sum to ``invoice_count`` and bucket totals sum to
    ``total_outstanding``.
    """

    report_type: Literal["receivables_aging_print"] = "receivables_aging_print"
    title: str
    generated_at: datetime
    data: ReceivablesAgingPrintData


class InvoiceReceiptContinuityPrintRequest(BaseSchema):
    """Batch 92 — print request for the invoice receipt continuity audit."""

    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class InvoiceReceiptGapPrintLine(BaseSchema):
    """One continuity defect row in the printed audit.

    Mirrors the dashboard ``InvoiceReceiptGapItem`` fields exactly so the
    printed packet is a faithful snapshot of the screen feed; amounts are
    stringified decimals per the print-schema convention.
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


class InvoiceReceiptContinuityPrintData(BaseSchema):
    as_of: datetime
    invoices_checked: int
    invoices_with_receipts: int
    invoices_missing_receipts: int
    duplicate_receipt_count: int
    sequence_break_count: int
    issue_count: int
    issues: list[InvoiceReceiptGapPrintLine]


class InvoiceReceiptContinuityPrintEnvelope(BaseSchema):
    """Batch 92 — printable invoice receipt continuity packet.

    Built through the exact same ``build_invoice_receipt_continuity_result``
    code path as the dashboard feed (single grouped Payment pass, live
    derivation), so headline aggregates on paper always sum back to
    ``invoices_checked`` and match the screen for the same scan window.
    """

    report_type: Literal["invoice_receipt_continuity_print"] = (
        "invoice_receipt_continuity_print"
    )
    title: str
    generated_at: datetime
    data: InvoiceReceiptContinuityPrintData


class ReceiptNumberingContinuityPrintRequest(BaseSchema):
    """Batch 93 — print request for the whole-receipt-book numbering audit."""

    limit: int = Field(default=2000, ge=1, le=5000)
    title: str | None = Field(default=None, max_length=200)


class ReceiptSeriesPrintLine(BaseSchema):
    """One receipt-number series as printed on paper.

    Mirrors ``ReceiptSeriesGap`` from the dashboard feed; per-series
    reconciliation always holds: ``expected_count == actual_count + gap_count``.
    """

    prefix: str
    first_number: int
    last_number: int
    expected_count: int
    actual_count: int
    gap_count: int
    missing_numbers: list[int]
    duplicate_numbers: list[str]


class ReceiptNumberingContinuityPrintData(BaseSchema):
    as_of: datetime
    receipts_checked: int
    series_count: int
    clean_series_count: int
    total_gap_count: int
    series: list[ReceiptSeriesPrintLine]


class ReceiptNumberingContinuityPrintEnvelope(BaseSchema):
    """Batch 93 — printable receipt numbering continuity packet.

    Built through the exact same whole-book scan and series derivation as
    ``GET /dashboard/receipt-numbering-continuity`` (single ordered Payment
    pass, shared ``_receipt_numeric_suffix`` parsing), so printed aggregates
    always satisfy ``clean_series_count <= series_count`` and
    ``expected_count == actual_count + gap_count`` per series, matching the
    screen line-for-line for the same scan window.
    """

    report_type: Literal["receipt_numbering_continuity_print"] = (
        "receipt_numbering_continuity_print"
    )
    title: str
    generated_at: datetime
    data: ReceiptNumberingContinuityPrintData


class InvoicePaymentReconciliationPrintRequest(BaseSchema):
    """Batch 94 — print request for the invoice payment reconciliation ledger."""

    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class InvoicePaymentReconciliationPrintLine(BaseSchema):
    """One reconciled invoice as printed on paper.

    Mirrors ``InvoicePaymentReconciliationItem`` from the dashboard feed;
    amounts are stringified decimals per the print-schema convention and
    the Batch 68 clamp invariant ``amount_paid + balance_due ==
    total_amount`` holds on every printed row.
    """

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: str
    amount_paid: str
    balance_due: str
    stored_payment_status: str
    derived_payment_status: str
    receipt_count: int
    is_reconciled: bool


class InvoicePaymentReconciliationPrintData(BaseSchema):
    as_of: date
    invoices_checked: int
    paid_invoices: int
    partially_paid_invoices: int
    unpaid_invoices: int
    total_billed: str
    total_paid: str
    total_outstanding: str
    items: list[InvoicePaymentReconciliationPrintLine]


class PaymentMethodSummaryPrintRequest(BaseSchema):
    """Batch 96 — print request for the payment-method collection summary."""

    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class PaymentMethodSummaryPrintLine(BaseSchema):
    """One payment method as printed on paper.

    Batch 96 — every figure derives from live ``Payment`` rows joined to
    non-cancelled invoices; ``share_of_total`` is a percentage (0-100) of
    the scanned-window collected total, and per-invoice amounts keep the
    Batch 68 clamp invariant, so ``total_collected`` sums back exactly to
    the sum of the per-method ``collected`` figures.
    """

    payment_method: str
    receipt_count: int
    invoice_count: int
    gross_received: str
    collected: str
    share_of_total: str


class PaymentMethodSummaryPrintData(BaseSchema):
    as_of: date
    invoices_checked: int
    receipts_scanned: int
    methods_reported: int
    total_collected: str
    items: list[PaymentMethodSummaryPrintLine]


class PaymentMethodSummaryPrintEnvelope(BaseSchema):
    """Batch 96 — printable payment-method collection summary packet.

    Built through the shared dashboard scan
    (``build_payment_method_collection_summary``, single grouped Payment
    pass over non-cancelled invoices, stored counters never trusted), so
    printed headline aggregates always satisfy
    ``sum(per-method collected) == total_collected`` and match
    ``GET /dashboard/payment-method-summary`` line-for-line for the same
    scan window.
    """

    report_type: Literal["payment_method_summary_print"] = (
        "payment_method_summary_print"
    )
    title: str
    generated_at: datetime
    data: PaymentMethodSummaryPrintData


class InvoicePaymentReconciliationPrintEnvelope(BaseSchema):
    """Batch 94 — printable invoice payment reconciliation packet.

    Built through the exact same live-payment scan and aggregation as
    ``GET /dashboard/invoice-payment-reconciliation``
    (``build_invoice_payment_reconciliation_ledger``, single grouped Payment
    pass, stored status never trusted), so printed headline aggregates always
    satisfy ``paid_invoices + partially_paid_invoices + unpaid_invoices ==
    invoices_checked`` and ``total_billed == total_paid + total_outstanding``,
    matching the screen line-for-line for the same scan window.
    """

    report_type: Literal["invoice_payment_reconciliation_print"] = (
        "invoice_payment_reconciliation_print"
    )
    title: str
    generated_at: datetime
    data: InvoicePaymentReconciliationPrintData


class InvoiceOverpaymentPrintRequest(BaseSchema):
    """Batch 97 — print request for the invoice overpayment ledger."""

    limit: int = Field(default=200, ge=1, le=500)
    title: str | None = Field(default=None, max_length=200)


class InvoiceOverpaymentPrintLine(BaseSchema):
    """One overpaid invoice as printed on paper.

    Mirrors ``InvoiceOverpaymentItem`` from the dashboard feed; amounts are
    stringified decimals per the print-schema convention. ``total_paid_raw``
    is summed from the live Payment ledger *without* the Batch 68 clamp, so
    the invariant ``overpaid_amount == total_paid_raw - total_amount`` holds
    on every printed row and ``balance_due`` is always zero.
    """

    invoice_id: int
    patient_id: int
    patient_name: str
    patient_number: str | None = None
    invoice_number: str
    invoice_date: datetime
    total_amount: str
    amount_paid: str
    balance_due: str
    total_paid_raw: str
    overpaid_amount: str
    stored_payment_status: str
    derived_payment_status: str
    receipt_count: int
    is_reconciled: bool


class InvoiceOverpaymentPrintData(BaseSchema):
    as_of: date
    invoices_checked: int
    invoices_overpaid: int
    total_billed: str
    total_paid_raw: str
    total_overpaid: str
    items: list[InvoiceOverpaymentPrintLine]


class InvoiceOverpaymentPrintEnvelope(BaseSchema):
    """Batch 97 — printable invoice overpayment ledger packet.

    Built through the exact same live-payment scan as the reconciliation
    ledger (``build_overpayment_ledger``, single grouped Payment pass over
    non-cancelled invoices, stored status never trusted), so printed rows
    satisfy ``overpaid_amount == total_paid_raw - total_amount`` and match
    ``GET /dashboard/invoice-overpayments`` line-for-line for the same scan
    window.
    """

    report_type: Literal["invoice_overpayment_print"] = (
        "invoice_overpayment_print"
    )
    title: str
    generated_at: datetime
    data: InvoiceOverpaymentPrintData


__all__ = [
    "ReportSection",
    "ALL_REPORT_SECTIONS",
    "ClinicalReportRequest",
    "ClinicalReportRead",
    "ClinicalReportBatchRequest",
    "ClinicalReportBatchItem",
    "ClinicalReportBatchRead",
    "ReportCatalogItem",
    "ReportCatalogRead",
    "ReportPrintBlock",
    "ReportPrintManifestRequest",
    "ReportPrintManifestRead",
    "ReportPrintEnvelope",
    "ReportPrintEnvelopeRequest",
    "InvoicePrintRequest",
    "InvoicePrintItemLine",
    "InvoicePrintReceiptLine",
    "InvoicePrintData",
    "InvoicePrintEnvelope",
    "CollectionSummaryPrintRequest",
    "PatientCollectionSummaryPrintLine",
    "CollectionSummaryPrintData",
    "CollectionSummaryPrintEnvelope",
    "ReceivablesAgingPrintRequest",
    "ReceivablesAgingBucketPrintLine",
    "ReceivablesAgingInvoicePrintLine",
    "ReceivablesAgingPrintData",
    "ReceivablesAgingPrintEnvelope",
    "InvoiceReceiptContinuityPrintRequest",
    "InvoiceReceiptGapPrintLine",
    "InvoiceReceiptContinuityPrintData",
    "InvoiceReceiptContinuityPrintEnvelope",
    "ReceiptNumberingContinuityPrintRequest",
    "ReceiptSeriesPrintLine",
    "ReceiptNumberingContinuityPrintData",
    "ReceiptNumberingContinuityPrintEnvelope",
    "InvoicePaymentReconciliationPrintRequest",
    "InvoicePaymentReconciliationPrintLine",
    "InvoicePaymentReconciliationPrintData",
    "InvoicePaymentReconciliationPrintEnvelope",
    "PaymentMethodSummaryPrintRequest",
    "PaymentMethodSummaryPrintLine",
    "PaymentMethodSummaryPrintData",
    "PaymentMethodSummaryPrintEnvelope",
    "InvoiceOverpaymentPrintRequest",
    "InvoiceOverpaymentPrintLine",
    "InvoiceOverpaymentPrintData",
    "InvoiceOverpaymentPrintEnvelope",
]
