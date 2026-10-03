"""HHMS Department master API endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department import department_service

router = APIRouter(prefix="/departments", tags=["Administration"])


@router.get("", response_model=list[DepartmentRead])
async def list_departments(
    db: DatabaseSession,
    _: CurrentUserDependency,
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[DepartmentRead]:
    return await department_service.list(
        db, active_only=active_only, skip=skip, limit=limit
    )


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_in: DepartmentCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DepartmentRead:
    return await department_service.create(db, department_in)


@router.get("/{department_id}", response_model=DepartmentRead)
async def get_department(
    department_id: UUID,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DepartmentRead:
    return await department_service.get(db, department_id)


@router.patch("/{department_id}", response_model=DepartmentRead)
async def update_department(
    department_id: UUID,
    department_in: DepartmentUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DepartmentRead:
    return await department_service.update(db, department_id, department_in)


__all__ = ["router"]
