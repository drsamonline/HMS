"""
HHMS Prescription API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionRead,
    PrescriptionUpdate,
)
from app.services.prescription import prescription_service


router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"],
)


@router.get(
    "",
    response_model=list[PrescriptionRead],
)
async def list_prescriptions(
    db: DatabaseSession,
    _: CurrentUserDependency,
    visit_id: int | None = None,
) -> list[PrescriptionRead]:
    if visit_id is None:
        return []
    prescriptions = await prescription_service.repository.get_by_visit(db, visit_id)
    result: list[PrescriptionRead] = []
    for prescription in prescriptions:
        items = await prescription_service.get_items(db, prescription.id)
        result.append(
            PrescriptionRead(
                **prescription.__dict__,
                items=items,
            )
        )
    return result


@router.post(
    "",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(
    prescription_in: PrescriptionCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PrescriptionRead:
    prescription = await prescription_service.create(
        db,
        data=prescription_in,
    )

    items = await prescription_service.get_items(
        db,
        prescription_id=prescription.id,
    )

    return PrescriptionRead(
        **prescription.__dict__,
        items=items,
    )


@router.get(
    "/by-case/{case_record_id}",
    response_model=list[PrescriptionRead],
)
async def list_case_prescriptions(
    case_record_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> list[PrescriptionRead]:
    """Case continuity: every prescription across the case's encounters."""
    prescriptions = await prescription_service.get_by_case(db, case_record_id)
    result: list[PrescriptionRead] = []
    for prescription in prescriptions:
        items = await prescription_service.get_items(db, prescription.id)
        result.append(
            PrescriptionRead(
                **prescription.__dict__,
                items=items,
            )
        )
    return result


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionRead,
)
async def get_prescription(
    prescription_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PrescriptionRead:
    prescription = await prescription_service.get_by_id(
        db,
        prescription_id=prescription_id,
    )

    items = await prescription_service.get_items(
        db,
        prescription_id=prescription.id,
    )

    return PrescriptionRead(
        **prescription.__dict__,
        items=items,
    )


@router.patch(
    "/{prescription_id}",
    response_model=PrescriptionRead,
)
async def update_prescription(
    prescription_id: int,
    prescription_in: PrescriptionUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PrescriptionRead:
    prescription = await prescription_service.update(
        db,
        prescription_id=prescription_id,
        prescription_in=prescription_in,
    )

    items = await prescription_service.get_items(
        db,
        prescription_id=prescription.id,
    )

    return PrescriptionRead(
        **prescription.__dict__,
        items=items,
    )


__all__ = [
    "router",
]