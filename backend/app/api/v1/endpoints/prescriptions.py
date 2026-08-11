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