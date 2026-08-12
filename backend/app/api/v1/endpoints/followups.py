"""HHMS Homoeopathic Follow-up API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.followup import FollowUpCreate, FollowUpRead, FollowUpUpdate
from app.services.followup import followup_service

router = APIRouter(prefix="/followups", tags=["Homoeopathic Follow-ups"])


def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])


@router.get("", response_model=list[FollowUpRead])
async def list_followups(
    db: DatabaseSession,
    _: CurrentUserDependency,
    case_record_id: int = Query(gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[FollowUpRead]:
    return await followup_service.list_by_case(db, case_record_id, skip, limit)


@router.post("", response_model=FollowUpRead, status_code=status.HTTP_201_CREATED)
async def create_followup(
    followup_in: FollowUpCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> FollowUpRead:
    return await followup_service.create(db, followup_in, _user_id(current_user))


@router.get("/{followup_id}", response_model=FollowUpRead)
async def get_followup(
    followup_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> FollowUpRead:
    return await followup_service.get_by_id(db, followup_id)


@router.patch("/{followup_id}", response_model=FollowUpRead)
async def update_followup(
    followup_id: int,
    followup_in: FollowUpUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> FollowUpRead:
    return await followup_service.update(db, followup_id, followup_in)


__all__ = ["router"]
