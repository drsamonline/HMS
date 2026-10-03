"""HHMS reporting and print-data selection service."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, or_, select
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
