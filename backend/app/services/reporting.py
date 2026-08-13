"""HHMS report-data selection service.

This service prepares structured clinical data for preview/printing.
It deliberately does not render PDF or HTML; rendering belongs to the
client print layer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.admission import Admission
from app.models.case_record import CaseRecord
from app.models.diagnosis import Diagnosis
from app.models.diet_chart import DietChart
from app.models.discharge import Discharge
from app.models.followup import FollowUp
from app.models.investigation import Investigation
from app.models.ipd_assessment import IPDAssessment
from app.models.nutritional_assessment import NutritionalAssessment
from app.models.pain_assessment import PainAssessment
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.progress_note import ProgressNote
from app.models.visit import Visit
from app.schemas.reporting import ALL_REPORT_SECTIONS, ClinicalReportRequest


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

    async def build_clinical_report(
        self,
        db: AsyncSession,
        request: ClinicalReportRequest,
    ) -> dict[str, Any]:
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

        if "diagnosis" in sections and case_id is not None:
            rows = await db.execute(
                select(Diagnosis).where(Diagnosis.case_record_id == case_id).order_by(Diagnosis.id)
            )
            data["diagnosis"] = [_dump_row(row) for row in rows.scalars().all()]

        if "followups" in sections and case_id is not None:
            stmt = select(FollowUp).where(FollowUp.case_record_id == case_id).order_by(
                FollowUp.followup_datetime
            )
            stmt = _apply_time_range(stmt, FollowUp.followup_datetime, request)
            rows = await db.execute(stmt)
            data["followups"] = [_dump_row(row) for row in rows.scalars().all()]

        if "prescriptions" in sections and visit_id is not None:
            stmt = select(Prescription).where(Prescription.visit_id == visit_id).order_by(
                Prescription.prescription_datetime
            )
            stmt = _apply_time_range(stmt, Prescription.prescription_datetime, request)
            rows = await db.execute(stmt)
            data["prescriptions"] = [_dump_row(row) for row in rows.scalars().all()]

        if "investigations" in sections:
            stmt = select(Investigation).where(Investigation.patient_id == patient.id).order_by(
                Investigation.investigation_datetime
            )
            if visit_id is not None:
                stmt = stmt.where(
                    (Investigation.visit_id == visit_id)
                    | (Investigation.visit_id.is_(None))
                )
            if admission_id is not None:
                stmt = stmt.where(
                    (Investigation.admission_id == admission_id)
                    | (Investigation.admission_id.is_(None))
                )
            stmt = _apply_time_range(stmt, Investigation.investigation_datetime, request)
            rows = await db.execute(stmt)
            data["investigations"] = [_dump_row(row) for row in rows.scalars().all()]

        if admission_id is not None:
            if "ipd_assessment" in sections:
                rows = await db.execute(
                    select(IPDAssessment)
                    .where(IPDAssessment.admission_id == admission_id)
                    .order_by(IPDAssessment.assessment_datetime)
                )
                data["ipd_assessment"] = [_dump_row(row) for row in rows.scalars().all()]

            if "pain_assessments" in sections:
                stmt = select(PainAssessment).where(
                    PainAssessment.admission_id == admission_id
                ).order_by(PainAssessment.assessment_datetime)
                stmt = _apply_time_range(stmt, PainAssessment.assessment_datetime, request)
                rows = await db.execute(stmt)
                data["pain_assessments"] = [_dump_row(row) for row in rows.scalars().all()]

            if "nutritional_assessment" in sections:
                rows = await db.execute(
                    select(NutritionalAssessment)
                    .where(NutritionalAssessment.admission_id == admission_id)
                    .order_by(NutritionalAssessment.assessment_datetime)
                )
                data["nutritional_assessment"] = [
                    _dump_row(row) for row in rows.scalars().all()
                ]

            if "diet_charts" in sections:
                stmt = select(DietChart).where(
                    DietChart.admission_id == admission_id
                ).order_by(DietChart.chart_date)
                stmt = _apply_time_range(stmt, DietChart.chart_date, request)
                rows = await db.execute(stmt)
                data["diet_charts"] = [_dump_row(row) for row in rows.scalars().all()]

            if "progress_notes" in sections:
                stmt = select(ProgressNote).where(
                    ProgressNote.admission_id == admission_id
                ).order_by(ProgressNote.note_datetime)
                stmt = _apply_time_range(stmt, ProgressNote.note_datetime, request)
                rows = await db.execute(stmt)
                data["progress_notes"] = [_dump_row(row) for row in rows.scalars().all()]

            if "discharge" in sections:
                rows = await db.execute(
                    select(Discharge).where(Discharge.admission_id == admission_id)
                )
                discharge = rows.scalar_one_or_none()
                if discharge is not None:
                    data["discharge"] = _dump_row(discharge)

            if admission is not None:
                data["admission"] = _dump_row(admission)

        return {
            "report_type": "clinical",
            "patient_id": patient.id,
            "case_record_id": case_id,
            "admission_id": admission_id,
            "sections": list(data.keys()),
            "data": data,
        }

    async def _resolve_patient(
        self,
        db: AsyncSession,
        request: ClinicalReportRequest,
    ) -> Patient:
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

    async def _resolve_case(
        self,
        db: AsyncSession,
        request: ClinicalReportRequest,
        patient_id: int,
    ) -> CaseRecord | None:
        if request.case_record_id is not None:
            case = await db.get(CaseRecord, request.case_record_id)
            if case is None or case.patient_id != patient_id:
                raise ResourceNotFoundException("Requested case record not found for patient.")
            return case
        if request.admission_id is not None:
            stmt = select(CaseRecord).where(
                CaseRecord.patient_id == patient_id,
                CaseRecord.admission_id == request.admission_id,
            ).order_by(CaseRecord.id.desc())
        else:
            stmt = select(CaseRecord).where(
                CaseRecord.patient_id == patient_id,
            ).order_by(CaseRecord.id.desc())
        result = await db.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def _resolve_admission(
        self,
        db: AsyncSession,
        request: ClinicalReportRequest,
        patient_id: int,
    ) -> Admission | None:
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
