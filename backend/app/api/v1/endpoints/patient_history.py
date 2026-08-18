"""Unified patient history access endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.core.exceptions import AuthorizationException
from app.services.auth import auth_service
from app.services.patient_history import patient_history_service

router = APIRouter(prefix="/patients", tags=["Patient History"])

_ALLOWED = {
    "patients.read", "patient.read", "patients.view", "patient.view",
    "clinical.read", "case_records.read", "case_record.read", "clinical.case.read",
    "reports.read", "report.read", "printing.read", "reports.print",
    "mrd.read", "patient_files.read", "archive.read",
}

async def _require_history_access(db, user_id: int) -> None:
    _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=user_id)
    if any(str(role).strip().lower() in {"admin", "administrator", "hospital administrator", "super administrator"} for role in roles):
        return
    normalized = {str(permission).strip().lower() for permission in permissions}
    if not normalized.intersection(_ALLOWED):
        raise AuthorizationException("You do not have permission to access patient history.")


@router.get("/{patient_id}/history")
async def get_patient_history(
    patient_id: int,
    db: DatabaseSession,
    user: CurrentUserDependency,
    year: list[int] = Query(default=[]),
):
    await _require_history_access(db, int(str(user["sub"])))
    return await patient_history_service.unified(db, patient_id, year)


@router.get("/{patient_id}/history/archives")
async def get_patient_history_archives(
    patient_id: int,
    db: DatabaseSession,
    user: CurrentUserDependency,
):
    await _require_history_access(db, int(str(user["sub"])))
    return {"patient_id": patient_id, "archives": await patient_history_service.available_archives(db)}


__all__ = ["router"]
