"""HHMS Medical Document repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medical_document import MedicalDocument
from app.repositories.base import RepositoryBase

class MedicalDocumentRepository(RepositoryBase[MedicalDocument]):
    def __init__(self) -> None:
        super().__init__(MedicalDocument)
    async def get_by_id(self, db: AsyncSession, document_id: int) -> MedicalDocument | None:
        return await db.get(MedicalDocument, document_id)
    async def list_by_patient(self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 100) -> list[MedicalDocument]:
        result = await db.execute(
            select(MedicalDocument)
            .where(MedicalDocument.patient_id == patient_id)
            .order_by(MedicalDocument.document_date.desc(), MedicalDocument.id.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

medical_document_repository = MedicalDocumentRepository()
__all__ = ["MedicalDocumentRepository", "medical_document_repository"]
