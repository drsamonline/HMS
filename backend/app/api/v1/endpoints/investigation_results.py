"""
HHMS Investigation Result API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.investigation_result import (
    InvestigationResultCreate,
    InvestigationResultRead,
    InvestigationResultUpdate,
)
from app.services.investigation_result import (
    investigation_result_service,
)


router = APIRouter(
    prefix="/investigation-results",
    tags=["Laboratory Results"],
)


@router.get(
    "",
    response_model=list[InvestigationResultRead],
)
async def list_investigation_results(
    db: DatabaseSession,
    _: CurrentUserDependency,
    investigation_id: int | None = Query(
        default=None,
        gt=0,
    ),
    report_status: str | None = Query(
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
) -> list[InvestigationResultRead]:
    return await investigation_result_service.list(
        db,
        investigation_id=investigation_id,
        report_status=report_status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=InvestigationResultRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_investigation_result(
    result_in: InvestigationResultCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationResultRead:
    return await investigation_result_service.create(
        db,
        result_in,
    )


@router.get(
    "/investigation/{investigation_id}",
    response_model=InvestigationResultRead,
)
async def get_result_by_investigation(
    investigation_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationResultRead:
    return await (
        investigation_result_service
        .get_by_investigation(
            db,
            investigation_id,
        )
    )


@router.get(
    "/{result_id}",
    response_model=InvestigationResultRead,
)
async def get_investigation_result(
    result_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationResultRead:
    return await investigation_result_service.get(
        db,
        result_id,
    )


@router.put(
    "/{result_id}",
    response_model=InvestigationResultRead,
)
async def update_investigation_result(
    result_id: int,
    result_in: InvestigationResultUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationResultRead:
    return await investigation_result_service.update(
        db,
        result_id,
        result_in,
    )


@router.delete(
    "/{result_id}",
    response_model=InvestigationResultRead,
)
async def delete_investigation_result(
    result_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvestigationResultRead:
    return await investigation_result_service.delete(
        db,
        result_id,
    )


__all__ = [
    "router",
]