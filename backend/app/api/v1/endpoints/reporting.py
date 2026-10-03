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
    ReceivablesAgingPrintEnvelope,
    ReceivablesAgingPrintRequest,
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


__all__ = ["router"]
