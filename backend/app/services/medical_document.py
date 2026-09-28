"""HHMS Medical Document service."""
from __future__ import annotations
from datetime import date, datetime, timezone
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.schemas.medical_document import MedicalDocumentCreate, MedicalDocumentUpdate
from app.repositories.medical_document import MedicalDocumentRepository, medical_document_repository
from app.services.operational_year import operational_year_service

class MedicalDocumentService:
    def __init__(self, repository: MedicalDocumentRepository | None = None) -> None:
        self.repository = repository or medical_document_repository
    async def get_by_id(self, db: AsyncSession, document_id: int) -> MedicalDocument:
        record = await self.repository.get_by_id(db, document_id)
        if record is None:
            raise ResourceNotFoundException("Medical document not found.")
        return record
    async def list_by_patient(self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 100) -> list[MedicalDocument]:
        if await db.get(Patient, patient_id) is None:
            raise ResourceNotFoundException("Patient not found.")
        return await self.repository.list_by_patient(db, patient_id, skip, limit)
    async def create(self, db: AsyncSession, data: MedicalDocumentCreate, uploaded_by: int) -> MedicalDocument:
        if await db.get(Patient, data.patient_id) is None:
            raise ResourceNotFoundException("Patient not found.")
        # Derive the annual lifecycle fields from the document date so every
        # MRD document carries its operational-year identity at creation.
        document_local_date = (
            data.document_date.astimezone(timezone.utc).date()
            if data.document_date.tzinfo is not None
            else data.document_date.date()
        )
        op_cfg = await operational_year_service.get_config(db)
        document_year = operational_year_service.current_year(document_local_date, op_cfg)
        current_year = operational_year_service.current_year(date.today(), op_cfg)
        record = MedicalDocument(
            **data.model_dump(),
            uploaded_by=uploaded_by,
            document_year=document_year,
            storage_tier="live",
            is_current_year=document_year == current_year,
        )
        now = datetime.now(timezone.utc)
        record.created_at = now
        record.updated_at = now
        try:
            db.add(record)
            await db.commit()
            await db.refresh(record)
            return record
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Medical document number already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create medical document.") from exc
    async def update(self, db: AsyncSession, document_id: int, data: MedicalDocumentUpdate) -> MedicalDocument:
        record = await self.get_by_id(db, document_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        try:
            await db.commit()
            await db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to update medical document.") from exc

medical_document_service = MedicalDocumentService()
__all__ = ["MedicalDocumentService", "medical_document_service"]
