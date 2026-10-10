from __future__ import annotations
from datetime import date
from fastapi import APIRouter
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.operational_year import OperationalYearRead, OperationalYearUpdate
from app.services.operational_year import operational_year_service

router = APIRouter(prefix="/operational-year", tags=["Configuration"])

def _admin(user: CurrentUserDependency) -> int:
    return int(str(user["sub"]))

@router.get("", response_model=OperationalYearRead)
async def get_operational_year(db: DatabaseSession, _: CurrentUserDependency) -> OperationalYearRead:
    cfg = await operational_year_service.get_config(db)
    today = date.today()
    return OperationalYearRead(basis=cfg.basis, start_month=cfg.start_month, start_day=cfg.start_day, current_year=operational_year_service.current_year(today, cfg), label=operational_year_service.label(today, cfg))

@router.put("", response_model=OperationalYearRead)
async def update_operational_year(payload: OperationalYearUpdate, db: DatabaseSession, user: CurrentUserDependency) -> OperationalYearRead:
    _admin(user)
    cfg = await operational_year_service.save_config(db, basis=payload.basis, start_month=payload.start_month, start_day=payload.start_day)
    today = date.today()
    return OperationalYearRead(basis=cfg.basis, start_month=cfg.start_month, start_day=cfg.start_day, current_year=operational_year_service.current_year(today, cfg), label=operational_year_service.label(today, cfg))
