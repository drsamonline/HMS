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
]
