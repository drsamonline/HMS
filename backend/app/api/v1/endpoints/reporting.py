"""HHMS report-data selection endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.reporting import (
    ClinicalReportBatchRead,
    ClinicalReportBatchRequest,
    ClinicalReportRead,
    CollectionSummaryPrintEnvelope,
    CollectionSummaryPrintRequest,
    InvoicePrintEnvelope,
    InvoicePrintRequest,
    InvoicePaymentReconciliationPrintEnvelope,
    InvoicePaymentReconciliationPrintRequest,
    InvoiceReceiptContinuityPrintEnvelope,
    InvoiceReceiptContinuityPrintRequest,
    PaymentMethodSummaryPrintEnvelope,
    PaymentMethodSummaryPrintRequest,
    ReceivablesAgingPrintEnvelope,
    ReceivablesAgingPrintRequest,
    ReceiptNumberingContinuityPrintEnvelope,
    ReceiptNumberingContinuityPrintRequest,
    ReportPrintEnvelope,
    ReportPrintManifestRead,
    ReportPrintManifestRequest,
    ReportPrintEnvelopeRequest,
    ClinicalReportRequest,
    ReportCatalogRead,
)
from app.services.reporting import reporting_service

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/catalog", response_model=ReportCatalogRead)
async def get_report_catalog(_: CurrentUserDependency) -> ReportCatalogRead:
    return reporting_service.catalog()

@router.post("/clinical-data", response_model=ClinicalReportRead)
async def build_clinical_report(
    report_in: ClinicalReportRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ClinicalReportRead:
    return await reporting_service.build_clinical_report(db, report_in)

@router.post("/clinical-data/print-manifest", response_model=ReportPrintManifestRead)
async def build_clinical_print_manifest(
    report_in: ReportPrintManifestRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ReportPrintManifestRead:
    return await reporting_service.build_print_manifest(db, report_in)

@router.post("/clinical-data/print-envelope", response_model=ReportPrintEnvelope)
async def build_clinical_print_envelope(
    report_in: ReportPrintEnvelopeRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ReportPrintEnvelope:
    return await reporting_service.build_print_envelope(db, report_in)

@router.post("/clinical-data/batch", response_model=ClinicalReportBatchRead)
async def build_clinical_report_batch(
    report_in: ClinicalReportBatchRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ClinicalReportBatchRead:
    return await reporting_service.build_case_batch(db, report_in)

@router.post("/invoice-print-envelope", response_model=InvoicePrintEnvelope)
async def build_invoice_print_envelope(
    report_in: InvoicePrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoicePrintEnvelope:
    """Batch 85 — printable invoice packet (header, line items, receipts)."""
    return await reporting_service.build_invoice_print_envelope(db, report_in)


@router.post(
    "/collection-summary-print-envelope",
    response_model=CollectionSummaryPrintEnvelope,
)
async def build_collection_summary_print_envelope(
    report_in: CollectionSummaryPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> CollectionSummaryPrintEnvelope:
    """Batch 90 — printable per-patient collection summary packet.

    Shares the dashboard's live-payment reconciliation scan and aggregation,
    so printed totals always satisfy
    ``total_collected + total_outstanding == total_billed``.
    """
    return await reporting_service.build_collection_summary_print_envelope(
        db, report_in
    )


@router.post(
    "/receivables-aging-print-envelope",
    response_model=ReceivablesAgingPrintEnvelope,
)
async def build_receivables_aging_print_envelope(
    report_in: ReceivablesAgingPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ReceivablesAgingPrintEnvelope:
    """Batch 91 — printable receivables aging packet.

    Shares the dashboard's live-payment aging derivation
    (``build_receivables_aging_result``), so printed bucket counts/totals
    always sum back to the headline aggregates and reconcile line-for-line
    with ``GET /dashboard/receivables-aging``.
    """
    return await reporting_service.build_receivables_aging_print_envelope(
        db, report_in
    )


@router.post(
    "/invoice-receipt-continuity-print-envelope",
    response_model=InvoiceReceiptContinuityPrintEnvelope,
)
async def build_invoice_receipt_continuity_print_envelope(
    report_in: InvoiceReceiptContinuityPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoiceReceiptContinuityPrintEnvelope:
    """Batch 92 — printable invoice receipt continuity packet.

    Shares the dashboard's live scan and audit derivation
    (``build_invoice_receipt_continuity_result``), so printed headline
    aggregates always sum back to ``invoices_checked`` and reconcile
    line-for-line with ``GET /dashboard/invoice-receipt-continuity``.
    """
    return await reporting_service.build_invoice_receipt_continuity_print_envelope(
        db, report_in
    )


@router.post(
    "/receipt-numbering-continuity-print-envelope",
    response_model=ReceiptNumberingContinuityPrintEnvelope,
)
async def build_receipt_numbering_continuity_print_envelope(
    report_in: ReceiptNumberingContinuityPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ReceiptNumberingContinuityPrintEnvelope:
    """Batch 93 — printable whole-receipt-book numbering audit packet.

    Shares the dashboard's whole-book scan and series derivation
    (``build_receipt_numbering_continuity_result``), so printed per-series
    figures always satisfy ``expected_count == actual_count + gap_count``
    and reconcile line-for-line with
    ``GET /dashboard/receipt-numbering-continuity``.
    """
    return await reporting_service.build_receipt_numbering_continuity_print_envelope(
        db, report_in
    )


@router.post(
    "/invoice-payment-reconciliation-print-envelope",
    response_model=InvoicePaymentReconciliationPrintEnvelope,
)
async def build_invoice_payment_reconciliation_print_envelope(
    report_in: InvoicePaymentReconciliationPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoicePaymentReconciliationPrintEnvelope:
    """Batch 94 — printable invoice payment reconciliation packet.

    Shares the dashboard's live-payment scan and aggregation
    (``build_invoice_payment_reconciliation_ledger``), so printed headline
    aggregates always satisfy ``paid_invoices + partially_paid_invoices +
    unpaid_invoices == invoices_checked`` and ``total_billed == total_paid +
    total_outstanding``, reconciling line-for-line with
    ``GET /dashboard/invoice-payment-reconciliation``.
    """
    return await reporting_service.build_invoice_payment_reconciliation_print_envelope(
        db, report_in
    )


@router.post(
    "/payment-method-summary-print-envelope",
    response_model=PaymentMethodSummaryPrintEnvelope,
)
async def build_payment_method_summary_print_envelope(
    report_in: PaymentMethodSummaryPrintRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PaymentMethodSummaryPrintEnvelope:
    """Batch 96 — printable payment-method collection summary packet.

    Shares the dashboard's live-payment scan and per-method aggregation
    (``build_payment_method_summary_result``), so printed figures always
    satisfy ``sum(per-method collected) == total_collected`` and reconcile
    line-for-line with ``GET /dashboard/payment-method-summary`` for the
    same scan window.
    """
    return await reporting_service.build_payment_method_summary_print_envelope(
        db, report_in
    )


__all__ = ["router"]
