"""HHMS PatientFile repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient_file import PatientFile
from app.repositories.base import RepositoryBase

class PatientFileRepository(RepositoryBase[PatientFile]):
    def __init__(self) -> None:
        super().__init__(PatientFile)

    async def get_by_id(self, db: AsyncSession, patient_file_id: int) -> PatientFile | None:
        return await db.get(PatientFile, patient_file_id)

    async def list_by_patient(
        self, db: AsyncSession, patient_id: int, skip: int = 0, limit: int = 50
    ) -> list[PatientFile]:
        result = await db.execute(
            select(PatientFile)
            .where(PatientFile.patient_id == patient_id)
            .order_by(PatientFile.id.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

patient_file_repository = PatientFileRepository()
__all__ = ["PatientFileRepository", "patient_file_repository"]
