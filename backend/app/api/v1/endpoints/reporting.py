"""HHMS report-data selection endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.reporting import ClinicalReportRead, ClinicalReportRequest
from app.services.reporting import reporting_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/clinical-data", response_model=ClinicalReportRead)
async def build_clinical_report(
    report_in: ClinicalReportRequest,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> ClinicalReportRead:
    return await reporting_service.build_clinical_report(db, report_in)


__all__ = ["router"]
