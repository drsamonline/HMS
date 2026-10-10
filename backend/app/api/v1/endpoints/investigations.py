"""
HHMS Investigation API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationRead,
    InvestigationUpdate,
)
from app.services.investigation import (
    investigation_service,
)


router = APIRouter(
    prefix="/investigations",
    tags=["Laboratory Investigations"],
)


@router.get(
    "",
    response_model=list[InvestigationRead],
)
async def list_investigations(
    db: DatabaseSession,
    _: CurrentUserDependency,
    patient_id: int | None = Query(
        default=None,
        gt=0,
    ),
    investigation_status: str | None = Query(
        default=None,
        max_length=20,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[InvestigationRead]:
    return await investigation_service.list(
        db,
        patient_id=patient_id,
        status=investigation_status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_investigation(
    investigation_in: InvestigationCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationRead:
    return await investigation_service.create(
        db,
        investigation_in,
    )


@router.get(
    "/{investigation_id}",
    response_model=InvestigationRead,
)
async def get_investigation(
    investigation_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationRead:
    return await investigation_service.get(
        db,
        investigation_id,
    )


@router.put(
    "/{investigation_id}",
    response_model=InvestigationRead,
)
async def update_investigation(
    investigation_id: int,
    investigation_in: InvestigationUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationRead:
    return await investigation_service.update(
        db,
        investigation_id,
        investigation_in,
    )


@router.delete(
    "/{investigation_id}",
    response_model=InvestigationRead,
)
async def cancel_investigation(
    investigation_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationRead:
    return await investigation_service.cancel(
        db,
        investigation_id,
    )


__all__ = [
    "router",
]