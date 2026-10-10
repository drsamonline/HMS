"""HHMS Medical Document API endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.medical_document import MedicalDocumentCreate, MedicalDocumentRead, MedicalDocumentUpdate
from app.services.medical_document import medical_document_service

router = APIRouter(prefix="/medical-documents", tags=["Medical Records"])

@router.get("", response_model=list[MedicalDocumentRead])
async def list_medical_documents(
    db: DatabaseSession, _: CurrentUserDependency,
    patient_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200),
) -> list[MedicalDocumentRead]:
    return await medical_document_service.list_by_patient(db, patient_id, skip, limit)

@router.post("", response_model=MedicalDocumentRead, status_code=status.HTTP_201_CREATED)
async def create_medical_document(
    document_in: MedicalDocumentCreate, db: DatabaseSession, current_user: CurrentUserDependency,
) -> MedicalDocumentRead:
    return await medical_document_service.create(db, document_in, current_user.id)

@router.get("/{document_id}", response_model=MedicalDocumentRead)
async def get_medical_document(document_id: int, db: DatabaseSession, _: CurrentUserDependency) -> MedicalDocumentRead:
    return await medical_document_service.get_by_id(db, document_id)

@router.patch("/{document_id}", response_model=MedicalDocumentRead)
async def update_medical_document(
    document_id: int, document_in: MedicalDocumentUpdate, db: DatabaseSession, _: CurrentUserDependency,
) -> MedicalDocumentRead:
    return await medical_document_service.update(db, document_id, document_in)

__all__ = ["router"]
