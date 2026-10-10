"""
HHMS OPD Token API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.opd_token import (
    OPDTokenCreate,
    OPDTokenRead,
    OPDTokenUpdate,
)
from app.services.opd_token import opd_token_service


router = APIRouter(
    prefix="/opd-tokens",
    tags=["OPD Tokens"],
)


@router.get(
    "",
    response_model=list[OPDTokenRead],
)
async def list_opd_tokens(
    db: DatabaseSession,
    _: CurrentUserDependency,
    queue_date: date = Query(...),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[OPDTokenRead]:
    return await opd_token_service.list(
        db,
        queue_date=queue_date,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=OPDTokenRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_opd_token(
    token_in: OPDTokenCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> OPDTokenRead:
    return await opd_token_service.create(
        db,
        token_in=token_in,
    )


@router.put(
    "/{token_id}",
    response_model=OPDTokenRead,
)
async def update_opd_token(
    token_id: int,
    token_in: OPDTokenUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> OPDTokenRead:
    return await opd_token_service.update(
        db,
        token_id=token_id,
        token_in=token_in,
    )


@router.delete(
    "/{token_id}",
    response_model=OPDTokenRead,
)
async def cancel_opd_token(
    token_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> OPDTokenRead:
    return await opd_token_service.cancel(
        db,
        token_id=token_id,
    )


__all__ = [
    "router",
]