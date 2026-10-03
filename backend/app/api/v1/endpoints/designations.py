"""HHMS Designation master API endpoints."""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.designation import DesignationCreate, DesignationRead, DesignationUpdate
from app.services.designation import designation_service

router = APIRouter(prefix="/designations", tags=["Administration"])

@router.get("", response_model=list[DesignationRead])
async def list_designations(db: DatabaseSession, _: CurrentUserDependency, skip: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)) -> list[DesignationRead]:
    return await designation_service.list(db, skip=skip, limit=limit)

@router.post("", response_model=DesignationRead, status_code=status.HTTP_201_CREATED)
async def create_designation(designation_in: DesignationCreate, db: DatabaseSession, _: CurrentUserDependency) -> DesignationRead:
    return await designation_service.create(db, designation_in)

@router.get("/{designation_id}", response_model=DesignationRead)
async def get_designation(designation_id: UUID, db: DatabaseSession, _: CurrentUserDependency) -> DesignationRead:
    return await designation_service.get(db, designation_id)

@router.patch("/{designation_id}", response_model=DesignationRead)
async def update_designation(designation_id: UUID, designation_in: DesignationUpdate, db: DatabaseSession, _: CurrentUserDependency) -> DesignationRead:
    return await designation_service.update(db, designation_id, designation_in)

__all__ = ["router"]
