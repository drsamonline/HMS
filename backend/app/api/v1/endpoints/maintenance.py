"""Administrative maintenance, archive and lifecycle endpoints."""
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.services.administration import _require_admin
from app.services.maintenance import maintenance_service
from app.services.archive_manager import archive_manager
from app.services.archive_retention import archive_retention_service

router=APIRouter(prefix="/maintenance",tags=["Maintenance"])
def actor_id(user: CurrentUserDependency)->int:return int(str(user["sub"]))

@router.get("/status")
async def status(db: DatabaseSession,user: CurrentUserDependency): await _require_admin(db,actor_id(user)); return await maintenance_service.health()

@router.post("/run")
async def run(db: DatabaseSession,user: CurrentUserDependency): await _require_admin(db,actor_id(user)); return await maintenance_service.run_safe_maintenance()

@router.post("/vacuum")
async def vacuum(db: DatabaseSession,user: CurrentUserDependency): await _require_admin(db,actor_id(user)); return await maintenance_service.vacuum()

@router.get("/archives")
async def archives(db: DatabaseSession,user: CurrentUserDependency): await _require_admin(db,actor_id(user)); return await archive_manager.list_archives(db)

@router.post("/archives/{year}")
async def create_archive(year:int,db:DatabaseSession,user:CurrentUserDependency): await _require_admin(db,actor_id(user)); return await archive_manager.create_year_archive(db,year)

@router.get("/archives/rollover/preview")
async def archive_rollover_preview(db: DatabaseSession,user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    return await archive_manager.rollover_preview(db)

@router.post("/archives/rollover/{year}")
async def archive_rollover(year: int, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    return await archive_manager.rollover_case_year(db, year)

@router.get("/archives/retention/preview")
async def archive_retention_preview(db: DatabaseSession,user: CurrentUserDependency):
    await _require_admin(db,actor_id(user))
    plan = await archive_retention_service.plan(db)
    return {
        "current_year": plan.current_year,
        "online_years": plan.online_years,
        "cold_years": plan.cold_years,
        "promote_to_cold": list(plan.promote_to_cold),
        "retain_online": list(plan.retain_online),
        "retention_review": list(plan.retention_review),
        "invalid_or_future": list(plan.invalid_or_future),
    }

@router.post("/archives/retention/execute")
async def archive_retention_execute(db: DatabaseSession,user: CurrentUserDependency):
    await _require_admin(db,actor_id(user))
    return await archive_retention_service.execute_eligible(db)

@router.get("/archives/{year}/patients/{patient_id}/cases")
async def historical_cases(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_case_records(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/visits")
async def historical_visits(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_visits(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/invoices")
async def historical_invoices(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_invoices(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/payments")
async def historical_payments(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_payments(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/dispenses")
async def historical_dispenses(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_dispenses(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/investigations")
async def historical_investigations(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_investigations(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/admissions")
async def historical_admissions(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_admissions(db,year,patient_id)

@router.get("/archives/{year}/patients/{patient_id}/documents")
async def historical_documents(year:int, patient_id:int, db:DatabaseSession, user:CurrentUserDependency):
    uid = actor_id(user)
    try:
        await _require_admin(db, uid)
    except Exception:
        from app.services.auth import auth_service
        _, roles, permissions = await auth_service.get_current_user_profile(db, user_id=uid)
        normalized = {str(p).strip().lower() for p in permissions}
        if not (normalized & {"reports.read", "report.read", "patients.read", "patient.read"}):
            raise
    return await archive_manager.read_documents(db,year,patient_id)

@router.get("/archives/{year}/download",response_class=FileResponse)
async def download_archive(year:int,db:DatabaseSession,user:CurrentUserDependency)->FileResponse:
    await _require_admin(db,actor_id(user)); rows=await archive_manager.list_archives(db); row=next((x for x in rows if x.archive_year==year),None)
    if row is None: raise ValueError("Archive year not found")
    path=archive_manager.archive_path(row); return FileResponse(path=path,filename=path.name,media_type="application/octet-stream")

__all__=["router"]
