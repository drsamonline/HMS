"""
HHMS Prescription API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.permissions import require
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



def _read_model(prescription, items, name, registration):
    """Build the read model without SQLAlchemy's private state.

    ``__dict__`` carries ``_sa_instance_state``, which Pydantic refuses as an extra
    field. It used to be filtered by luck: the object was expired and the key was
    gone. Resolving the prescriber issues a query, which changes that, so the
    filtering is now explicit.
    """

    data = {
        key: value
        for key, value in prescription.__dict__.items()
        if not key.startswith("_")
    }
    return PrescriptionRead(
        **data,
        items=items,
        prescriber_name=name,
        prescriber_registration=registration,
    )


@router.get(
    "",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(require("prescriptions.read"))],
)
async def list_prescriptions(
    db: DatabaseSession,
    _: CurrentUserDependency,
    visit_id: int | None = None,
) -> list[PrescriptionRead]:
    if visit_id is None:
        return []
    prescriptions = await prescription_service.repository.get_by_visit(db, visit_id)
    prescribers = await prescription_service.prescriber_identities(
        db, {prescription.prescribed_by for prescription in prescriptions}
    )
    result: list[PrescriptionRead] = []
    for prescription in prescriptions:
        items = await prescription_service.get_items(db, prescription.id)
        name, registration = prescribers.get(prescription.prescribed_by, (None, None))
        result.append(_read_model(prescription, items, name, registration))
    return result


@router.post(
    "",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require("prescriptions.write"))],
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

    prescribers = await prescription_service.prescriber_identities(
        db, {prescription.prescribed_by}
    )
    name, registration = prescribers.get(prescription.prescribed_by, (None, None))

    return _read_model(prescription, items, name, registration)


@router.get(
    "/by-case/{case_record_id}",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(require("prescriptions.read"))],
)
async def list_case_prescriptions(
    case_record_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> list[PrescriptionRead]:
    """Case continuity: every prescription across the case's encounters."""
    prescriptions = await prescription_service.get_by_case(db, case_record_id)
    prescribers = await prescription_service.prescriber_identities(
        db, {prescription.prescribed_by for prescription in prescriptions}
    )
    result: list[PrescriptionRead] = []
    for prescription in prescriptions:
        items = await prescription_service.get_items(db, prescription.id)
        name, registration = prescribers.get(prescription.prescribed_by, (None, None))
        result.append(_read_model(prescription, items, name, registration))
    return result


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionRead,
    dependencies=[Depends(require("prescriptions.read"))],
)
async def get_prescription(
    prescription_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PrescriptionRead:
    # The service method is get(); this endpoint has called get_by_id() since it
    # was written, which does not exist - so every read by id raised AttributeError
    # and returned a 500. No test called the route, so nothing noticed.
    prescription = await prescription_service.get(
        db,
        prescription_id,
    )

    items = await prescription_service.get_items(
        db,
        prescription_id=prescription.id,
    )

    prescribers = await prescription_service.prescriber_identities(
        db, {prescription.prescribed_by}
    )
    name, registration = prescribers.get(prescription.prescribed_by, (None, None))

    return _read_model(prescription, items, name, registration)


@router.patch(
    "/{prescription_id}",
    response_model=PrescriptionRead,
    dependencies=[Depends(require("prescriptions.write"))],
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

    prescribers = await prescription_service.prescriber_identities(
        db, {prescription.prescribed_by}
    )
    name, registration = prescribers.get(prescription.prescribed_by, (None, None))

    return _read_model(prescription, items, name, registration)


__all__ = [
    "router",
]