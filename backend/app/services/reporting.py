"""HHMS reporting and print-data selection service."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.admission import Admission
from app.models.case_record import CaseRecord
from app.models.diagnosis import Diagnosis
from app.models.diet_chart import DietChart
from app.models.discharge import Discharge
from app.models.dispense_record import DispenseRecord
from app.models.followup import FollowUp
from app.models.investigation import Investigation
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment
from app.models.medical_document import MedicalDocument
from app.models.medicine import Medicine
from app.models.patient_file import PatientFile
from app.models.archive_record import ArchiveRecord
from app.models.ipd_assessment import IPDAssessment
from app.models.nutritional_assessment import NutritionalAssessment
from app.models.pain_assessment import PainAssessment
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.progress_note import ProgressNote
from app.models.stock_batch import StockBatch
from app.models.user import User
from app.models.visit import Visit
from app.schemas.reporting import (
    ALL_REPORT_SECTIONS,
    ClinicalReportBatchItem,
    ClinicalReportBatchRead,
    ClinicalReportBatchRequest,
    ClinicalReportRead,
    ClinicalReportRequest,
    CollectionSummaryPrintData,
    CollectionSummaryPrintEnvelope,
    CollectionSummaryPrintRequest,
    InvoicePrintData,
    InvoicePrintEnvelope,
    InvoicePrintItemLine,
    InvoicePrintReceiptLine,
    InvoicePrintRequest,
    InvoiceReceiptContinuityPrintData,
    InvoiceReceiptContinuityPrintEnvelope,
    InvoiceReceiptContinuityPrintRequest,
    InvoiceReceiptGapPrintLine,
    PatientCollectionSummaryPrintLine,
    InvoicePaymentReconciliationPrintData,
    InvoicePaymentReconciliationPrintEnvelope,
    InvoicePaymentReconciliationPrintLine,
    InvoicePaymentReconciliationPrintRequest,
    InvoiceOverpaymentPrintData,
    InvoiceOverpaymentPrintEnvelope,
    InvoiceOverpaymentPrintLine,
    InvoiceOverpaymentPrintRequest,
    InvoiceSettlementAuditPrintData,
    InvoiceSettlementAuditPrintEnvelope,
    InvoiceSettlementAuditPrintLine,
    InvoiceSettlementAuditPrintRequest,
    RefundAuditPrintData,
    RefundAuditPrintEnvelope,
    RefundAuditPrintLine,
    RefundAuditPrintRequest,
    DischargeAuditPrintData,
    DischargeAuditPrintEnvelope,
    DischargeAuditPrintLine,
    DischargeAuditPrintRequest,
    OPDQueueSummaryPrintData,
    OPDQueueSummaryPrintEnvelope,
    OPDQueueSummaryPrintLine,
    OPDQueueSummaryPrintRequest,
    WardOccupancyPrintData,
    WardOccupancyPrintEnvelope,
    WardOccupancyPrintLine,
    WardOccupancyPrintRequest,
    InvestigationBillingReconciliationPrintData,
    InvestigationBillingReconciliationPrintEnvelope,
    InvestigationBillingReconciliationPrintLine,
    InvestigationBillingReconciliationPrintRequest,
    PaymentMethodSummaryPrintData,
    PaymentMethodSummaryPrintEnvelope,
    PaymentMethodSummaryPrintLine,
    PaymentMethodSummaryPrintRequest,
    PaymentMethodOverpaymentPrintData,
    PaymentMethodOverpaymentPrintEnvelope,
    PaymentMethodOverpaymentPrintLine,
    PaymentMethodOverpaymentPrintRequest,
    InvoiceSettlementAuditPrintData,
    InvoiceSettlementAuditPrintEnvelope,
    InvoiceSettlementAuditPrintLine,
    InvoiceSettlementAuditPrintRequest,
    RefundAuditPrintData,
    RefundAuditPrintEnvelope,
    RefundAuditPrintLine,
    RefundAuditPrintRequest,
    ReceiptNumberingContinuityPrintData,
    ReceiptNumberingContinuityPrintEnvelope,
    ReceiptNumberingContinuityPrintRequest,
    ReceiptSeriesPrintLine,
    ReceivablesAgingBucketPrintLine,
    ReceivablesAgingInvoicePrintLine,
    ReceivablesAgingPrintData,
    ReceivablesAgingPrintEnvelope,
    ReceivablesAgingPrintRequest,
    ReportCatalogItem,
    ReportCatalogRead,
    ReportPrintEnvelope,
    ReportPrintBlock,
    ReportPrintManifestRead,
    ReportPrintManifestRequest,
    ReportPrintEnvelopeRequest,
)

_PRINT_BLOCK_META: dict[str, tuple[str, str, int, bool]] = {
    "patient": ("Patient", "patient", 1, False),
    "case_record": ("Homoeopathic Case Record", "case", 2, True),
    "admission": ("Admission", "ipd", 3, True),
    "diagnosis": ("Diagnosis / ICD-11", "case", 4, True),
    "followups": ("Follow-ups", "followup", 5, True),
    "prescriptions": ("Prescriptions", "prescription", 6, True),
    "investigations": ("Investigations", "investigation", 7, True),
    "ipd_assessment": ("IPD Assessment", "ipd", 8, True),
    "pain_assessments": ("Pain Assessments", "ipd", 9, True),
    "nutritional_assessment": ("Nutritional Assessment", "ipd", 10, True),
    "diet_charts": ("Diet Charts", "ipd", 11, True),
    "progress_notes": ("Progress Notes", "ipd", 12, True),
    "discharge": ("Discharge Summary", "ipd", 13, True),
    "dispensations": ("Pharmacy Dispensations", "pharmacy", 14, True),
    "billing": ("Billing / Invoices", "billing", 15, True),
    "payments": ("Payments / Receipts", "billing", 16, True),
    "medical_documents": ("Medical Documents", "documents", 17, True),
    "mrd": ("MRD Patient File / Archive", "mrd", 18, True),
}

_REPORT_CATALOG = [
    ReportCatalogItem(key="patient", label="Patient", description="Patient demographics and registration information.", available_for=["clinical", "case", "ipd"]),
    ReportCatalogItem(key="case_record", label="Homoeopathic Case Record", description="Complete homoeopathic case history and assessment fields.", available_for=["clinical", "case"]),
    ReportCatalogItem(key="admission", label="Admission", description="IPD admission episode details.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="diagnosis", label="Diagnosis / ICD-11", description="Diagnoses linked to the selected case record.", available_for=["clinical", "case"]),
    ReportCatalogItem(key="followups", label="Follow-ups", description="Follow-up records within the requested time range.", available_for=["clinical", "case"]),
    ReportCatalogItem(key="prescriptions", label="Prescriptions", description="Prescriptions linked to the selected visit.", available_for=["clinical", "case"]),
    ReportCatalogItem(key="investigations", label="Investigations", description="Investigation requests associated with the patient/context.", available_for=["clinical", "case", "ipd"]),
    ReportCatalogItem(key="ipd_assessment", label="IPD Assessment", description="IPD admission assessments.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="pain_assessments", label="Pain Assessments", description="IPD pain assessment records.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="nutritional_assessment", label="Nutritional Assessment", description="IPD nutritional assessment records.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="diet_charts", label="Diet Charts", description="IPD diet chart records.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="progress_notes", label="Progress Notes", description="IPD progress notes.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="discharge", label="Discharge Summary", description="IPD discharge summary.", available_for=["clinical", "ipd"]),
    ReportCatalogItem(key="dispensations", label="Pharmacy Dispensations", description="Medicines dispensed against prescriptions in the selected clinical context.", available_for=["clinical", "case"]),
    ReportCatalogItem(key="billing", label="Billing / Invoices", description="Patient invoices linked to the selected clinical context.", available_for=["clinical", "case", "ipd", "billing"]),
    ReportCatalogItem(key="payments", label="Payments / Receipts", description="Payments and receipts linked to patient invoices.", available_for=["clinical", "case", "ipd", "billing"]),
    ReportCatalogItem(key="medical_documents", label="Medical Documents", description="Medical documents registered for the patient/context.", available_for=["clinical", "case", "ipd", "mrd"]),
    ReportCatalogItem(key="mrd", label="MRD Patient File / Archive", description="Patient file index and archive records.", available_for=["clinical", "case", "ipd", "mrd"]),
]

def _dump_row(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    mapper = obj.__mapper__
    result: dict[str, Any] = {}
    for column in mapper.columns:
        value = getattr(obj, column.key)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        result[column.key] = value
    return result

def _apply_time_range(stmt: Select[Any], column: Any, request: ClinicalReportRequest) -> Select[Any]:
    if request.start_datetime is not None:
        stmt = stmt.where(column >= request.start_datetime)
    if request.end_datetime is not None:
        stmt = stmt.where(column <= request.end_datetime)
    return stmt

class ReportingService:
    """Prepare structured report data from existing clinical records."""

    def catalog(self) -> ReportCatalogRead:
        return ReportCatalogRead(sections=_REPORT_CATALOG)

    async def build_print_manifest(
        self, db: AsyncSession, request: ReportPrintManifestRequest
    ) -> ReportPrintManifestRead:
        patient = await self._resolve_patient(db, request)
        case_record = await self._resolve_case(db, request, patient.id)
        admission = await self._resolve_admission(db, request, patient.id)
        selected = list(dict.fromkeys(request.sections)) or list(ALL_REPORT_SECTIONS)
        blocks: list[ReportPrintBlock] = []
        for key in selected:
            meta = _PRINT_BLOCK_META.get(key)
            if meta is None:
                continue
            label, group, order, page_break = meta
            blocks.append(
                ReportPrintBlock(
                    section=key,
                    label=label,
                    page_group=group,
                    print_order=order,
                    page_break_before=page_break,
                    available=True,
                )
            )
        blocks.sort(key=lambda block: block.print_order)
        return ReportPrintManifestRead(
            title=request.title or "HHMS Clinical Report",
            generated_at=datetime.utcnow(),
            patient_id=patient.id,
            case_record_id=case_record.id if case_record else None,
            admission_id=admission.id if admission else None,
            print_scope="complete_case" if not request.sections else "selected_sections",
            blocks=blocks,
        )

    async def build_clinical_report(self, db: AsyncSession, request: ClinicalReportRequest) -> ClinicalReportRead:
        patient = await self._resolve_patient(db, request)
        case_record = await self._resolve_case(db, request, patient.id)
        admission = await self._resolve_admission(db, request, patient.id)

        sections = list(dict.fromkeys(request.sections)) or list(ALL_REPORT_SECTIONS)
        data: dict[str, Any] = {}
        if "patient" in sections:
            data["patient"] = _dump_row(patient)
        if "case_record" in sections and case_record is not None:
            data["case_record"] = _dump_row(case_record)

        case_id = case_record.id if case_record is not None else None
        visit_id = case_record.visit_id if case_record is not None else None
        admission_id = admission.id if admission is not None else None

        if "admission" in sections and admission is not None:
            data["admission"] = _dump_row(admission)

        if "diagnosis" in sections and case_id is not None:
            rows = await db.execute(select(Diagnosis).where(Diagnosis.case_record_id == case_id).order_by(Diagnosis.id))
            data["diagnosis"] = [_dump_row(row) for row in rows.scalars().all()]
        if "followups" in sections and case_id is not None:
            stmt = _apply_time_range(select(FollowUp).where(FollowUp.case_record_id == case_id).order_by(FollowUp.followup_datetime), FollowUp.followup_datetime, request)
            rows = await db.execute(stmt)
            data["followups"] = [_dump_row(row) for row in rows.scalars().all()]
        if "prescriptions" in sections and visit_id is not None:
            stmt = _apply_time_range(select(Prescription).where(Prescription.visit_id == visit_id).order_by(Prescription.prescription_datetime), Prescription.prescription_datetime, request)
            rows = await db.execute(stmt)
            data["prescriptions"] = [_dump_row(row) for row in rows.scalars().all()]
        if "investigations" in sections:
            stmt = select(Investigation).where(Investigation.patient_id == patient.id).order_by(Investigation.investigation_datetime)
            if visit_id is not None:
                stmt = stmt.where((Investigation.visit_id == visit_id) | (Investigation.visit_id.is_(None)))
            if admission_id is not None:
                stmt = stmt.where((Investigation.admission_id == admission_id) | (Investigation.admission_id.is_(None)))
            stmt = _apply_time_range(stmt, Investigation.investigation_datetime, request)
            rows = await db.execute(stmt)
            data["investigations"] = [_dump_row(row) for row in rows.scalars().all()]

        if "dispensations" in sections:
            # Scope: all encounters of the selected case (plus any visit directly
            # linked back to the case), or all patient visits when no case context.
            visit_scope_stmt = select(Visit.id).where(Visit.patient_id == patient.id)
            if case_id is not None:
                visit_scope_stmt = visit_scope_stmt.where(or_(Visit.case_record_id == case_id, Visit.id == visit_id))
            case_visit_ids = list((await db.execute(visit_scope_stmt)).scalars().all())
            item_stmt = select(PrescriptionItem.id).join(
                Prescription, PrescriptionItem.prescription_id == Prescription.id
            ).where(Prescription.visit_id.in_(case_visit_ids))
            dispense_stmt = _apply_time_range(
                select(DispenseRecord)
                .where(DispenseRecord.prescription_item_id.in_(item_stmt))
                .order_by(DispenseRecord.dispense_date),
                DispenseRecord.dispense_date,
                request,
            )
            dispense_rows = await db.execute(dispense_stmt)
            dispensations = list(dispense_rows.scalars().all())
            enriched: list[dict[str, Any]] = []
            if dispensations:
                medicine_ids = {row.medicine_id for row in dispensations}
                batch_ids = {row.stock_batch_id for row in dispensations}
                user_ids = {row.dispensed_by for row in dispensations}
                medicine_map = {
                    row.id: row.medicine_name
                    for row in (await db.execute(select(Medicine.id, Medicine.medicine_name).where(Medicine.id.in_(medicine_ids)))).all()
                }
                batch_map = {
                    row.id: row.batch_no
                    for row in (await db.execute(select(StockBatch.id, StockBatch.batch_no).where(StockBatch.id.in_(batch_ids)))).all()
                }
                user_map = {
                    row.id: row.full_name
                    for row in (await db.execute(select(User.id, User.full_name).where(User.id.in_(user_ids)))).all()
                }
                for row in dispensations:
                    payload = _dump_row(row)
                    payload["quantity_dispensed"] = str(payload.get("quantity_dispensed"))
                    payload["medicine_name"] = medicine_map.get(row.medicine_id)
                    payload["stock_batch_no"] = batch_map.get(row.stock_batch_id)
                    payload["dispensed_by_name"] = user_map.get(row.dispensed_by)
                    enriched.append(payload)
            data["dispensations"] = enriched

        if "billing" in sections or "payments" in sections:
            invoice_stmt = select(Invoice).where(Invoice.patient_id == patient.id).order_by(Invoice.invoice_date)
            context_filters = []
            if visit_id is not None:
                context_filters.append(Invoice.visit_id == visit_id)
            if admission_id is not None:
                context_filters.append(Invoice.admission_id == admission_id)
            if context_filters:
                invoice_stmt = invoice_stmt.where(or_(*context_filters))
            invoice_stmt = _apply_time_range(invoice_stmt, Invoice.invoice_date, request)
            invoice_rows = await db.execute(invoice_stmt)
            invoices = list(invoice_rows.scalars().all())
            if "billing" in sections:
                data["billing"] = [_dump_row(row) for row in invoices]
            if "payments" in sections:
                invoice_ids = [row.id for row in invoices]
                if invoice_ids:
                    payment_rows = await db.execute(select(Payment).where(Payment.invoice_id.in_(invoice_ids)).order_by(Payment.payment_datetime))
                    data["payments"] = [_dump_row(row) for row in payment_rows.scalars().all()]
                else:
                    data["payments"] = []

        if "medical_documents" in sections:
            document_stmt = select(MedicalDocument).where(MedicalDocument.patient_id == patient.id).order_by(MedicalDocument.document_date)
            context_filters = []
            if visit_id is not None:
                context_filters.append(MedicalDocument.visit_id == visit_id)
            if admission_id is not None:
                context_filters.append(MedicalDocument.admission_id == admission_id)
            if context_filters:
                document_stmt = document_stmt.where(or_(*context_filters))
            document_stmt = _apply_time_range(document_stmt, MedicalDocument.document_date, request)
            rows = await db.execute(document_stmt)
            data["medical_documents"] = [_dump_row(row) for row in rows.scalars().all()]

        if "mrd" in sections:
            file_rows = await db.execute(select(PatientFile).where(PatientFile.patient_id == patient.id).order_by(PatientFile.id))
            files = list(file_rows.scalars().all())
            mrd_payload = {"patient_files": [_dump_row(row) for row in files], "archives": []}
            file_ids = [row.id for row in files]
            if file_ids:
                archive_rows = await db.execute(select(ArchiveRecord).where(ArchiveRecord.patient_file_id.in_(file_ids)).order_by(ArchiveRecord.archive_date, ArchiveRecord.id))
                mrd_payload["archives"] = [_dump_row(row) for row in archive_rows.scalars().all()]
            data["mrd"] = mrd_payload

        if admission_id is not None:
            if "ipd_assessment" in sections:
                rows = await db.execute(select(IPDAssessment).where(IPDAssessment.admission_id == admission_id).order_by(IPDAssessment.assessment_datetime))
                data["ipd_assessment"] = [_dump_row(row) for row in rows.scalars().all()]
            if "pain_assessments" in sections:
                stmt = _apply_time_range(select(PainAssessment).where(PainAssessment.admission_id == admission_id).order_by(PainAssessment.assessment_datetime), PainAssessment.assessment_datetime, request)
                rows = await db.execute(stmt)
                data["pain_assessments"] = [_dump_row(row) for row in rows.scalars().all()]
            if "nutritional_assessment" in sections:
                rows = await db.execute(select(NutritionalAssessment).where(NutritionalAssessment.admission_id == admission_id).order_by(NutritionalAssessment.assessment_datetime))
                data["nutritional_assessment"] = [_dump_row(row) for row in rows.scalars().all()]
            if "diet_charts" in sections:
                stmt = _apply_time_range(select(DietChart).where(DietChart.admission_id == admission_id).order_by(DietChart.chart_date), DietChart.chart_date, request)
                rows = await db.execute(stmt)
                data["diet_charts"] = [_dump_row(row) for row in rows.scalars().all()]
            if "progress_notes" in sections:
                stmt = _apply_time_range(select(ProgressNote).where(ProgressNote.admission_id == admission_id).order_by(ProgressNote.note_datetime), ProgressNote.note_datetime, request)
                rows = await db.execute(stmt)
                data["progress_notes"] = [_dump_row(row) for row in rows.scalars().all()]
            if "discharge" in sections:
                rows = await db.execute(select(Discharge).where(Discharge.admission_id == admission_id))
                discharge = rows.scalar_one_or_none()
                if discharge is not None:
                    data["discharge"] = _dump_row(discharge)

        return ClinicalReportRead(
            report_type="clinical",
            patient_id=patient.id,
            case_record_id=case_id,
            admission_id=admission_id,
            sections=list(data.keys()),
            data=data,
        )

    async def build_print_envelope(
        self, db: AsyncSession, request: ReportPrintEnvelopeRequest
    ) -> ReportPrintEnvelope:
        report = await self.build_clinical_report(db, request)
        title = request.title or "HHMS Clinical Report"
        return ReportPrintEnvelope(
            title=title,
            generated_at=datetime.utcnow(),
            patient_id=report.patient_id,
            case_record_id=report.case_record_id,
            admission_id=report.admission_id,
            selected_sections=report.sections,
            available_sections=list(ALL_REPORT_SECTIONS),
            report=report,
        )

    async def build_invoice_print_envelope(
        self, db: AsyncSession, request: InvoicePrintRequest
    ) -> InvoicePrintEnvelope:
        """Assemble a complete, self-contained printable invoice packet.

        Batch 85 — final reporting/printing integration for the billing
        domain: the envelope carries the invoice header, its line items and
        all live receipts, with balances derived from payments (never the
        stored status alone) so the printed document always reconciles:
        ``total_amount == amount_paid + balance_due``.
        """
        invoice = await db.get(Invoice, request.invoice_id)
        if invoice is None:
            raise ResourceNotFoundException("Invoice not found.")
        patient = await db.get(Patient, invoice.patient_id)
        if patient is None:
            raise ResourceNotFoundException("Patient for invoice not found.")

        item_rows = await db.execute(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id).order_by(InvoiceItem.id)
        )
        items = [
            InvoicePrintItemLine(
                id=row.id,
                item_type=row.item_type,
                description=row.description,
                quantity=str(row.quantity),
                unit_price=str(row.unit_price),
                line_total=str(row.line_total),
                remarks=row.remarks,
            )
            for row in item_rows.scalars().all()
        ]

        receipt_rows = await db.execute(
            select(Payment).where(Payment.invoice_id == invoice.id).order_by(Payment.payment_datetime, Payment.id)
        )
        receipts = [
            InvoicePrintReceiptLine(
                id=row.id,
                receipt_number=row.receipt_number,
                payment_datetime=row.payment_datetime.isoformat(),
                payment_method=row.payment_method,
                amount_paid=str(row.amount_paid),
                transaction_reference=row.transaction_reference,
                remarks=row.remarks,
            )
            for row in receipt_rows.scalars().all()
        ]

        # Derived reconciliation (Batch 68 semantics): payments are the
        # source of truth; clamp both sides so one bad row never produces
        # a negative figure on the printed document.
        paid_total = sum((Decimal(str(row.amount_paid)) for row in receipts), Decimal("0"))
        total_amount = Decimal(invoice.total_amount)
        amount_paid = min(paid_total, total_amount)
        balance_due = max(total_amount - amount_paid, Decimal("0"))
        payment_status = invoice.payment_status

        generated_at = datetime.utcnow()
        invoice_payload = _dump_row(invoice)
        for key in ("total_amount",):
            if key in invoice_payload:
                invoice_payload[key] = str(invoice_payload[key])
        return InvoicePrintEnvelope(
            title=request.title or f"HHMS Invoice {invoice.invoice_number}",
            generated_at=generated_at,
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            patient_id=patient.id,
            data=InvoicePrintData(
                invoice=invoice_payload,
                items=items,
                receipts=receipts,
                patient=_dump_row(patient),
                total_amount=str(total_amount),
                amount_paid=str(amount_paid),
                balance_due=str(balance_due),
                payment_status=payment_status,
                generated_at=generated_at,
            ),
        )

    async def build_collection_summary_print_envelope(
        self, db: AsyncSession, request: CollectionSummaryPrintRequest
    ) -> CollectionSummaryPrintEnvelope:
        """Assemble a printable per-patient collection summary packet.

        Batch 90 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared reconciliation scan and aggregation
        (single grouped Payment pass, live-payment clamping, stored counters
        never trusted), so the printed packet always satisfies
        ``total_collected + total_outstanding == total_billed`` and matches
        the on-screen collection summary line-for-line.
        """
        from app.api.v1.endpoints.dashboard import (
            _build_reconciliation_rows,
            build_collection_summary_by_patient,
        )

        rows = await _build_reconciliation_rows(db, request.limit)
        summary = build_collection_summary_by_patient(rows)

        items = [
            PatientCollectionSummaryPrintLine(
                patient_id=item["patient_id"],
                patient_name=item["patient_name"],
                patient_number=item["patient_number"],
                invoice_count=item["invoice_count"],
                paid_invoice_count=item["paid_invoice_count"],
                partial_invoice_count=item["partial_invoice_count"],
                unpaid_invoice_count=item["unpaid_invoice_count"],
                total_billed=str(item["total_billed"]),
                total_collected=str(item["total_collected"]),
                outstanding=str(item["outstanding"]),
                last_payment_date=(
                    item["last_payment_date"].isoformat()
                    if item["last_payment_date"] is not None
                    else None
                ),
            )
            for item in summary["items"]
        ]

        generated_at = datetime.utcnow()
        return CollectionSummaryPrintEnvelope(
            title=request.title or "HHMS Collection Summary by Patient",
            generated_at=generated_at,
            data=CollectionSummaryPrintData(
                as_of=summary["as_of"],
                invoices_checked=summary["invoices_checked"],
                patients_checked=summary["patients_checked"],
                patients_with_outstanding=summary["patients_with_outstanding"],
                total_billed=str(summary["total_billed"]),
                total_collected=str(summary["total_collected"]),
                total_outstanding=str(summary["total_outstanding"]),
                items=items,
            ),
        )

    async def build_receivables_aging_print_envelope(
        self, db: AsyncSession, request: ReceivablesAgingPrintRequest
    ) -> ReceivablesAgingPrintEnvelope:
        """Assemble a printable receivables aging packet.

        Batch 91 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared aging derivation
        (``build_receivables_aging_result`` over the Batch 82 live-payment
        outstanding feed), so the printed ledger always satisfies
        ``amount_paid + balance_due == total_amount`` per row and bucket
        counts/totals sum back to the headline aggregates exactly as on
        screen.
        """
        from app.api.v1.endpoints.dashboard import build_receivables_aging_result
        from app.services.billing import billing_service

        invoices, _service_total = await billing_service.list_outstanding_invoices(
            db, limit=request.limit
        )

        as_of = date.today()
        patient_ids = {invoice.patient_id for invoice in invoices}
        patients: dict[int, Patient] = {}
        if patient_ids:
            result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
            patients = {p.id: p for p in result.scalars()}

        # Live-payment derivation identical to the Batch 82/86 feeds
        # (single grouped pass, stored counters never trusted).
        paid_by_invoice: dict[int, Decimal] = {}
        if invoices:
            invoice_ids = [invoice.id for invoice in invoices]
            totals_result = await db.execute(
                select(
                    Payment.invoice_id,
                    func.coalesce(func.sum(Payment.amount_paid), 0),
                )
                .where(Payment.invoice_id.in_(invoice_ids))
                .group_by(Payment.invoice_id)
            )
            paid_by_invoice = {row[0]: Decimal(str(row[1])) for row in totals_result}

        aging = build_receivables_aging_result(
            invoices, patients, paid_by_invoice, as_of
        )

        return ReceivablesAgingPrintEnvelope(
            title=request.title or "HHMS Receivables Aging Ledger",
            generated_at=datetime.utcnow(),
            data=ReceivablesAgingPrintData(
                as_of=aging["as_of"],
                buckets=[
                    ReceivablesAgingBucketPrintLine(
                        label=bucket["label"],
                        lower_days=bucket["lower_days"],
                        upper_days=bucket["upper_days"],
                        invoice_count=bucket["invoice_count"],
                        total_outstanding=str(bucket["total_outstanding"]),
                    )
                    for bucket in aging["buckets"]
                ],
                items=[
                    ReceivablesAgingInvoicePrintLine(
                        invoice_id=item["invoice_id"],
                        patient_id=item["patient_id"],
                        patient_name=item["patient_name"],
                        patient_number=item["patient_number"],
                        invoice_number=item["invoice_number"],
                        invoice_date=item["invoice_date"],
                        total_amount=str(item["total_amount"]),
                        amount_paid=str(item["amount_paid"]),
                        balance_due=str(item["balance_due"]),
                        payment_status=str(item["payment_status"]),
                        days_outstanding=item["days_outstanding"],
                        bucket_label=item["bucket_label"],
                    )
                    for item in aging["items"]
                ],
                invoice_count=aging["invoice_count"],
                total_outstanding=str(aging["total_outstanding"]),
            ),
        )

    async def build_invoice_receipt_continuity_print_envelope(
        self, db: AsyncSession, request: InvoiceReceiptContinuityPrintRequest
    ) -> InvoiceReceiptContinuityPrintEnvelope:
        """Assemble a printable invoice receipt continuity packet.

        Batch 92 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared scan (``_load_continuity_scan_inputs``,
        single grouped Payment pass, no N+1) and the extracted
        ``build_invoice_receipt_continuity_result`` derivation, so the
        printed audit's headline aggregates always sum back to
        ``invoices_checked`` exactly as on screen for the same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            _load_continuity_scan_inputs,
            build_invoice_receipt_continuity_result,
        )

        invoices, patients, receipts_by_invoice, paid_by_invoice = (
            await _load_continuity_scan_inputs(db, request.limit)
        )
        audit = build_invoice_receipt_continuity_result(
            invoices,
            patients,
            receipts_by_invoice,
            paid_by_invoice,
            datetime.utcnow(),
        )

        return InvoiceReceiptContinuityPrintEnvelope(
            title=request.title or "HHMS Invoice Receipt Continuity Report",
            generated_at=datetime.utcnow(),
            data=InvoiceReceiptContinuityPrintData(
                as_of=audit["as_of"],
                invoices_checked=audit["invoices_checked"],
                invoices_with_receipts=audit["invoices_with_receipts"],
                invoices_missing_receipts=audit["invoices_missing_receipts"],
                duplicate_receipt_count=audit["duplicate_receipt_count"],
                sequence_break_count=audit["sequence_break_count"],
                issue_count=len(audit["issues"]),
                issues=[
                    InvoiceReceiptGapPrintLine(**issue) for issue in audit["issues"]
                ],
            ),
        )

    async def build_receipt_numbering_continuity_print_envelope(
        self, db: AsyncSession, request: ReceiptNumberingContinuityPrintRequest
    ) -> ReceiptNumberingContinuityPrintEnvelope:
        """Assemble a printable whole-receipt-book numbering audit packet.

        Batch 93 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared scan and series derivation
        (``build_receipt_numbering_continuity_result``, single ordered
        Payment pass, shared ``_receipt_numeric_suffix`` parsing), so the
        printed audit always satisfies per-series reconciliation
        ``expected_count == actual_count + gap_count`` and matches
        ``GET /dashboard/receipt-numbering-continuity`` line-for-line for
        the same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            build_receipt_numbering_continuity_result,
        )

        audit = await build_receipt_numbering_continuity_result(db, request.limit)

        return ReceiptNumberingContinuityPrintEnvelope(
            title=request.title or "HHMS Receipt Numbering Continuity Audit",
            generated_at=datetime.utcnow(),
            data=ReceiptNumberingContinuityPrintData(
                as_of=audit["as_of"],
                receipts_checked=audit["receipts_checked"],
                series_count=audit["series_count"],
                clean_series_count=audit["clean_series_count"],
                total_gap_count=audit["total_gap_count"],
                series=[
                    ReceiptSeriesPrintLine(**item) for item in audit["series"]
                ],
            ),
        )

    async def build_invoice_payment_reconciliation_print_envelope(
        self, db: AsyncSession, request: InvoicePaymentReconciliationPrintRequest
    ) -> InvoicePaymentReconciliationPrintEnvelope:
        """Assemble a printable invoice payment reconciliation packet.

        Batch 94 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared live-payment scan and aggregation
        (``build_invoice_payment_reconciliation_ledger``, single grouped
        Payment pass, Batch 68 clamp invariant), so the printed ledger
        always satisfies ``paid_invoices + partially_paid_invoices +
        unpaid_invoices == invoices_checked`` and ``total_billed ==
        total_paid + total_outstanding``, matching
        ``GET /dashboard/invoice-payment-reconciliation`` line-for-line for
        the same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            build_invoice_payment_reconciliation_ledger,
        )

        ledger = await build_invoice_payment_reconciliation_ledger(
            db, request.limit
        )

        return InvoicePaymentReconciliationPrintEnvelope(
            title=request.title or "HHMS Invoice Payment Reconciliation Ledger",
            generated_at=datetime.utcnow(),
            data=InvoicePaymentReconciliationPrintData(
                as_of=ledger["as_of"],
                invoices_checked=ledger["invoices_checked"],
                paid_invoices=ledger["paid_invoices"],
                partially_paid_invoices=ledger["partially_paid_invoices"],
                unpaid_invoices=ledger["unpaid_invoices"],
                total_billed=str(ledger["total_billed"]),
                total_paid=str(ledger["total_paid"]),
                total_outstanding=str(ledger["total_outstanding"]),
                items=[
                    InvoicePaymentReconciliationPrintLine(
                        **{
                            key: (str(value) if isinstance(value, Decimal) else value)
                            for key, value in item.items()
                        }
                    )
                    for item in ledger["items"]
                ],
            ),
        )

    async def build_payment_method_summary_print_envelope(
        self, db: AsyncSession, request: PaymentMethodSummaryPrintRequest
    ) -> PaymentMethodSummaryPrintEnvelope:
        """Assemble a printable payment-method collection summary packet.

        Batch 96 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared live-payment scan and per-method
        aggregation (``build_payment_method_summary_result``, single pass
        over the Payment ledger joined to non-cancelled invoices, stored
        counters never trusted, Batch 68 clamp parity), so the printed
        summary always satisfies ``sum(per-method collected) ==
        total_collected`` and matches
        ``GET /dashboard/payment-method-summary`` line-for-line for the
        same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            build_payment_method_summary_result,
        )

        summary = await build_payment_method_summary_result(db, request.limit)

        return PaymentMethodSummaryPrintEnvelope(
            title=request.title or "HHMS Payment Method Collection Summary",
            generated_at=datetime.utcnow(),
            data=PaymentMethodSummaryPrintData(
                as_of=summary["as_of"],
                invoices_checked=summary["invoices_checked"],
                receipts_scanned=summary["receipts_scanned"],
                methods_reported=summary["methods_reported"],
                total_collected=str(summary["total_collected"]),
                items=[
                    PaymentMethodSummaryPrintLine(
                        payment_method=item["payment_method"],
                        receipt_count=item["receipt_count"],
                        invoice_count=item["invoice_count"],
                        gross_received=str(item["gross_received"]),
                        collected=str(item["collected"]),
                        share_of_total=str(item["share_of_total"]),
                    )
                    for item in summary["items"]
                ],
            ),
        )

    async def build_invoice_overpayment_print_envelope(
        self, db: AsyncSession, request: InvoiceOverpaymentPrintRequest
    ) -> InvoiceOverpaymentPrintEnvelope:
        """Assemble a printable invoice overpayment ledger packet.

        Batch 97 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared live-payment scan
        (``build_overpayment_ledger``, built on the same
        ``_build_reconciliation_rows`` row builder as the Batch 89/94
        reconciliation ledger, stored counters never trusted), so printed
        rows always satisfy ``overpaid_amount == total_paid_raw -
        total_amount`` and match ``GET /dashboard/invoice-overpayments``
        line-for-line for the same scan window.
        """
        from app.api.v1.endpoints.dashboard import build_overpayment_ledger

        ledger = await build_overpayment_ledger(db, request.limit)

        return InvoiceOverpaymentPrintEnvelope(
            title=request.title or "HHMS Invoice Overpayment Ledger",
            generated_at=datetime.utcnow(),
            data=InvoiceOverpaymentPrintData(
                as_of=ledger["as_of"],
                invoices_checked=ledger["invoices_checked"],
                invoices_overpaid=ledger["invoices_overpaid"],
                total_billed=str(ledger["total_billed"]),
                total_paid_raw=str(ledger["total_paid_raw"]),
                total_overpaid=str(ledger["total_overpaid"]),
                items=[
                    InvoiceOverpaymentPrintLine(
                        **{
                            key: (str(value) if isinstance(value, Decimal) else value)
                            for key, value in item.items()
                        }
                    )
                    for item in ledger["items"]
                ],
            ),
        )

    async def build_payment_method_overpayment_print_envelope(
        self, db: AsyncSession, request: PaymentMethodOverpaymentPrintRequest
    ) -> PaymentMethodOverpaymentPrintEnvelope:
        """Assemble a printable payment-method overpayment breakdown packet.

        Batch 98 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared live-payment scan and per-method
        overpayment rollup (``build_payment_method_overpayment_result``,
        one Payment pass over non-cancelled invoices with the Batch 68
        clamp of the Batch 96 collection summary reused verbatim), so
        printed rows always satisfy ``gross_received == collected +
        overpaid``, headlines satisfy ``total_gross == total_collected +
        total_overpaid`` and match
        ``GET /dashboard/payment-method-overpayments`` line-for-line for
        the same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            build_payment_method_overpayment_result,
        )

        breakdown = await build_payment_method_overpayment_result(db, request.limit)

        return PaymentMethodOverpaymentPrintEnvelope(
            title=request.title or "HHMS Payment Method Overpayment Breakdown",
            generated_at=datetime.utcnow(),
            data=PaymentMethodOverpaymentPrintData(
                as_of=breakdown["as_of"],
                invoices_checked=breakdown["invoices_checked"],
                receipts_scanned=breakdown["receipts_scanned"],
                methods_reported=breakdown["methods_reported"],
                methods_with_overpayment=breakdown["methods_with_overpayment"],
                total_gross=str(breakdown["total_gross"]),
                total_collected=str(breakdown["total_collected"]),
                total_overpaid=str(breakdown["total_overpaid"]),
                items=[
                    PaymentMethodOverpaymentPrintLine(
                        **{
                            key: (str(value) if isinstance(value, Decimal) else value)
                            for key, value in item.items()
                        }
                    )
                    for item in breakdown["items"]
                ],
            ),
        )

    async def build_invoice_settlement_audit_print_envelope(
        self, db: AsyncSession, request: InvoiceSettlementAuditPrintRequest
    ) -> InvoiceSettlementAuditPrintEnvelope:
        """Assemble a printable cleared/unsettled settlement audit packet.

        Batch 100 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared reconciliation scan
        (``build_invoice_settlement_audit_scan``, built on the
        same ``_build_reconciliation_rows`` row builder as the Batch 94
        reconciliation ledger, stored counters/status never trusted), so
        printed rows always satisfy ``settled_amount + outstanding_amount
        == total_amount`` and match
        ``GET /dashboard/invoice-settlement-audit`` line-for-line for the
        same scan window.
        """
        from app.api.v1.endpoints.dashboard import (
            build_invoice_settlement_audit_scan,
        )

        audit = await build_invoice_settlement_audit_scan(
            db, request.limit
        )

        return InvoiceSettlementAuditPrintEnvelope(
            title=request.title or "HHMS Invoice Settlement Audit",
            generated_at=datetime.utcnow(),
            data=InvoiceSettlementAuditPrintData(
                as_of=audit["as_of"],
                items=[
                    InvoiceSettlementAuditPrintLine(
                        **{
                            key: (
                                str(value) if isinstance(value, Decimal) else value
                            )
                            for key, value in item.items()
                            if key
                            in InvoiceSettlementAuditPrintLine.model_fields
                        }
                    )
                    for item in audit["items"]
                ],
                total_invoices=audit["total_invoices"],
                cleared_count=audit["cleared_count"],
                unsettled_count=audit["unsettled_count"],
                total_billed=str(audit["total_billed"]),
                total_collected=str(audit["total_collected"]),
                total_outstanding=str(audit["total_outstanding"]),
            ),
        )

    async def build_refund_audit_print_envelope(
        self, db: AsyncSession, request: RefundAuditPrintRequest
    ) -> RefundAuditPrintEnvelope:
        """Assemble a printable refund processing audit packet.

        Batch 100 — reporting/printing integration for the billing domain:
        reuses the dashboard's shared negative-Payment scan
        (``build_refund_audit_scan``, one ordered pass over refund
        receipts plus a single grouped net-collections pass, stored
        counters never trusted), so printed rows match
        ``GET /dashboard/refund-audit`` line-for-line and headlines
        satisfy ``processed_count + drifted_count == total_refunds``.
        """
        from app.api.v1.endpoints.dashboard import build_refund_audit_scan

        audit = await build_refund_audit_scan(db, request.limit)

        return RefundAuditPrintEnvelope(
            title=request.title or "HHMS Refund Processing Audit",
            generated_at=datetime.utcnow(),
            data=RefundAuditPrintData(
                as_of=audit["as_of"],
                items=[
                    RefundAuditPrintLine(
                        **{
                            key: (
                                str(value) if isinstance(value, Decimal) else value
                            )
                            for key, value in item.items()
                            if key in RefundAuditPrintLine.model_fields
                        }
                    )
                    for item in audit["items"]
                ],
                total_refunds=audit["total_refunds"],
                processed_count=audit["processed_count"],
                drifted_count=audit["drifted_count"],
                total_refunded=str(audit["total_refunded"]),
            ),
        )

    async def build_ward_occupancy_print_envelope(
        self, db: AsyncSession, request: WardOccupancyPrintRequest
    ) -> WardOccupancyPrintEnvelope:
        """Assemble a printable ward occupancy summary packet.

        Batch 101 — reporting/printing integration for the IPD/ward domain:
        reuses the dashboard's shared bed scan and per-ward rollup
        (``build_ward_occupancy_summary_scan`` +
        ``build_ward_occupancy_summary_result`` verbatim), so every printed
        ward row keeps ``occupied_beds + reserved_beds + available_beds ==
        total_beds`` and the hospital-wide headlines match
        ``GET /dashboard/ward-occupancy-summary`` ward-for-ward.
        """
        from app.api.v1.endpoints.dashboard import (
            build_ward_occupancy_summary_result,
            build_ward_occupancy_summary_scan,
        )

        rows = await build_ward_occupancy_summary_scan(db, request.limit)
        summary = build_ward_occupancy_summary_result(rows, datetime.utcnow())

        return WardOccupancyPrintEnvelope(
            title=request.title or "HHMS Ward Occupancy Summary",
            generated_at=datetime.utcnow(),
            data=WardOccupancyPrintData(
                as_of=summary["as_of"],
                wards_reported=summary["wards_reported"],
                total_beds=summary["total_beds"],
                total_occupied=summary["total_occupied"],
                total_reserved=summary["total_reserved"],
                total_available=summary["total_available"],
                total_active_admissions=summary["total_active_admissions"],
                items=[
                    WardOccupancyPrintLine(**item)
                    for item in summary["items"]
                ],
            ),
        )

    async def build_investigation_billing_reconciliation_print_envelope(
        self,
        db: AsyncSession,
        request: InvestigationBillingReconciliationPrintRequest,
    ) -> InvestigationBillingReconciliationPrintEnvelope:
        """Assemble a printable investigation billing reconciliation packet.

        Batch 102 — reporting/printing integration for the lab/billing
        boundary: reuses the dashboard's shared investigation scan and
        billing rollup (``build_investigation_billing_reconciliation_scan`` +
        ``build_investigation_billing_reconciliation_result`` verbatim), so
        every printed row keeps ``billed_amount == charged_total -
        credited_total`` and the headlines match
        ``GET /dashboard/investigation-billing-reconciliation`` row-for-row.
        Unbilled open investigations stay on the page with
        ``billed_amount == 0`` instead of disappearing.
        """
        from app.api.v1.endpoints.dashboard import (
            build_investigation_billing_reconciliation_result,
            build_investigation_billing_reconciliation_scan,
        )

        rows = await build_investigation_billing_reconciliation_scan(
            db, request.limit
        )
        summary = build_investigation_billing_reconciliation_result(
            rows, datetime.utcnow()
        )
        # The shared scan/rollup also emits visit_id/admission_id for the
        # dashboard feed; the print line intentionally omits them, so drop
        # any keys not part of the print contract before validation.
        printable_keys = (
            InvestigationBillingReconciliationPrintLine.model_fields.keys()
        )
        items = [
            {key: item[key] for key in printable_keys if key in item}
            for item in summary["items"]
        ]

        return InvestigationBillingReconciliationPrintEnvelope(
            title=request.title or "HHMS Investigation Billing Reconciliation",
            generated_at=datetime.utcnow(),
            data=InvestigationBillingReconciliationPrintData(
                as_of=summary["as_of"],
                currency_note=summary["currency_note"],
                total_investigations_checked=summary[
                    "total_investigations_checked"
                ],
                pending_count=summary["pending_count"],
                in_progress_count=summary["in_progress_count"],
                billed_count=summary["billed_count"],
                billed_missing_count=summary["billed_missing_count"],
                total_billed=summary["total_billed"],
                items=[
                    InvestigationBillingReconciliationPrintLine(**item)
                    for item in items
                ],
            ),
        )

    async def build_case_batch(self, db: AsyncSession, request: ClinicalReportBatchRequest) -> ClinicalReportBatchRead:
        stmt = select(CaseRecord).where(
            CaseRecord.created_at >= request.start_datetime,
            CaseRecord.created_at <= request.end_datetime,
        ).order_by(CaseRecord.created_at, CaseRecord.id).limit(request.limit + 1)
        if request.patient_id is not None:
            stmt = stmt.where(CaseRecord.patient_id == request.patient_id)
        if request.case_status is not None:
            stmt = stmt.where(CaseRecord.case_status == request.case_status)
        rows = (await db.execute(stmt)).scalars().all()
        truncated = len(rows) > request.limit
        rows = rows[:request.limit]
        reports: list[ClinicalReportBatchItem] = []
        for case in rows:
            report = await self.build_clinical_report(
                db,
                ClinicalReportRequest(
                    case_record_id=case.id,
                    sections=request.sections,
                    start_datetime=request.start_datetime,
                    end_datetime=request.end_datetime,
                ),
            )
            reports.append(
                ClinicalReportBatchItem(
                    case_record_id=case.id,
                    patient_id=case.patient_id,
                    case_number=case.case_number,
                    case_status=case.case_status,
                    report=report,
                )
            )
        return ClinicalReportBatchRead(
            start_datetime=request.start_datetime,
            end_datetime=request.end_datetime,
            count=len(reports),
            truncated=truncated,
            reports=reports,
        )

    async def _resolve_patient(self, db: AsyncSession, request: ClinicalReportRequest) -> Patient:
        if request.patient_id is not None:
            patient = await db.get(Patient, request.patient_id)
        elif request.case_record_id is not None:
            case = await db.get(CaseRecord, request.case_record_id)
            patient = await db.get(Patient, case.patient_id) if case else None
        else:
            admission = await db.get(Admission, request.admission_id)
            patient = await db.get(Patient, admission.patient_id) if admission else None
        if patient is None:
            raise ResourceNotFoundException("Patient or requested clinical record not found.")
        return patient

    async def _resolve_case(self, db: AsyncSession, request: ClinicalReportRequest, patient_id: int) -> CaseRecord | None:
        if request.case_record_id is not None:
            case = await db.get(CaseRecord, request.case_record_id)
            if case is None or case.patient_id != patient_id:
                raise ResourceNotFoundException("Requested case record not found for patient.")
            return case
        if request.admission_id is not None:
            stmt = select(CaseRecord).where(CaseRecord.patient_id == patient_id, CaseRecord.admission_id == request.admission_id).order_by(CaseRecord.id.desc())
        else:
            stmt = select(CaseRecord).where(CaseRecord.patient_id == patient_id).order_by(CaseRecord.id.desc())
        result = await db.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def _resolve_admission(self, db: AsyncSession, request: ClinicalReportRequest, patient_id: int) -> Admission | None:
        if request.admission_id is not None:
            admission = await db.get(Admission, request.admission_id)
            if admission is None or admission.patient_id != patient_id:
                raise ResourceNotFoundException("Requested admission not found for patient.")
            return admission
        if request.case_record_id is not None:
            case = await db.get(CaseRecord, request.case_record_id)
            if case is not None and case.admission_id is not None:
                return await db.get(Admission, case.admission_id)
        return None

reporting_service = ReportingService()
__all__ = ["ReportingService", "reporting_service"]
