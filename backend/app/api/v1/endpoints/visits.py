"""
HHMS Visit API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.visit import (
    VisitCreate,
    VisitRead,
    VisitUpdate,
)
from app.services.visit import visit_service


router = APIRouter(
    prefix="/visits",
    tags=["Visits"],
)


@router.get(
    "",
    response_model=list[VisitRead],
)
async def list_visits(
    db: DatabaseSession,
    _: CurrentUserDependency,
    patient_id: int | None = Query(
        default=None,
        gt=0,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
) -> list[VisitRead]:
    return await visit_service.list(
        db,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=VisitRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_visit(
    visit_in: VisitCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> VisitRead:
    return await visit_service.create(
        db,
        visit_in=visit_in,
    )


@router.get(
    "/{visit_id}",
    response_model=VisitRead,
)
async def get_visit(
    visit_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> VisitRead:
    return await visit_service.get_by_id(
        db,
        visit_id=visit_id,
    )


@router.patch(
    "/{visit_id}",
    response_model=VisitRead,
)
async def update_visit(
    visit_id: int,
    visit_in: VisitUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> VisitRead:
    return await visit_service.update(
        db,
        visit_id=visit_id,
        visit_in=visit_in,
    )


__all__ = [
    "router",
]