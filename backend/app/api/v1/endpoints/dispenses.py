"""
HHMS Dispensing API Endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.exceptions import AuthenticationException
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.dispense import (
    DispenseCreate,
    DispenseRead,
)
from app.services.dispense import dispense_service

router = APIRouter(
    prefix="/dispenses",
    tags=["Pharmacy Dispensing"],
)


def _current_user_id(current_user: dict) -> int:
    subject = current_user.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException(
            "Authenticated user identity is invalid."
        ) from exc

    if user_id <= 0:
        raise AuthenticationException(
            "Authenticated user identity is invalid."
        )
    return user_id


@router.post(
    "",
    response_model=DispenseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_dispense(
    dispense_in: DispenseCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> DispenseRead:
    return await dispense_service.create(
        db,
        dispense_in,
        performed_by=_current_user_id(current_user),
    )


@router.get(
    "/{dispense_id}",
    response_model=DispenseRead,
)
async def get_dispense(
    dispense_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DispenseRead:
    return await dispense_service.get(
        db,
        dispense_id,
    )


@router.get(
    "/prescription-item/{prescription_item_id}",
    response_model=list[DispenseRead],
)
async def list_item_dispenses(
    prescription_item_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> list[DispenseRead]:
    return await dispense_service.list_by_prescription_item(
        db,
        prescription_item_id,
    )


__all__ = ["router"]
