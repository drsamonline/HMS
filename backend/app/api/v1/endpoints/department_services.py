"""API endpoints for configurable department services."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.department_service import (
    DepartmentServiceCreate, DepartmentServiceRead, DepartmentServiceUpdate,
)
from app.services.department_service import department_service_manager

router = APIRouter(prefix="/department-services", tags=["Department Services"])


@router.get("", response_model=list[DepartmentServiceRead])
async def list_department_services(
    db: DatabaseSession, _: CurrentUserDependency,
    department_id: UUID, skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> list[DepartmentServiceRead]:
    return await department_service_manager.list(db, department_id, skip, limit)


@router.post("", response_model=DepartmentServiceRead, status_code=status.HTTP_201_CREATED)
async def create_department_service(
    data: DepartmentServiceCreate, db: DatabaseSession, _: CurrentUserDependency,
) -> DepartmentServiceRead:
    return await department_service_manager.create(db, data)


@router.get("/{service_id}", response_model=DepartmentServiceRead)
async def get_department_service(
    service_id: UUID, db: DatabaseSession, _: CurrentUserDependency,
) -> DepartmentServiceRead:
    return await department_service_manager.get(db, service_id)


@router.patch("/{service_id}", response_model=DepartmentServiceRead)
async def update_department_service(
    service_id: UUID, data: DepartmentServiceUpdate,
    db: DatabaseSession, _: CurrentUserDependency,
) -> DepartmentServiceRead:
    return await department_service_manager.update(db, service_id, data)


__all__ = ["router"]
