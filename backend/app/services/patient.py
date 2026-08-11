"""
HHMS Patient Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.patient import Patient
from app.repositories.patient import (
    PatientRepository,
    patient_repository,
)
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    """Business workflows for patient management."""

    def __init__(
        self,
        repository: PatientRepository | None = None,
    ) -> None:
        self.repository = repository or patient_repository

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        patient_id: int,
    ) -> Patient:
        patient = await self.repository.get_by_id(
            db,
            patient_id,
        )

        if patient is None:
            raise ResourceNotFoundException(
                "Patient not found."
            )

        return patient

    async def list(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Patient]:
        return await self.repository.search(
            db,
            search=search,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        patient_in: PatientCreate,
    ) -> Patient:
        patient = Patient(
            **patient_in.model_dump(),
            patient_number="PENDING",
        )

        try:
            patient = await self.repository.add(
                db,
                patient,
            )

            patient.patient_number = f"PAT-{patient.id:06d}"

            await self.repository.update(
                db,
                patient,
            )

            await db.commit()
            return patient

        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException(
                "Unable to create patient because a duplicate record exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException(
                "Unable to create patient."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        patient_id: int,
        patient_in: PatientUpdate,
    ) -> Patient:
        patient = await self.get_by_id(
            db,
            patient_id=patient_id,
        )

        update_data = patient_in.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return patient

        try:
            for field, value in update_data.items():
                setattr(patient, field, value)

            patient = await self.repository.update(
                db,
                patient,
            )

            await db.commit()
            return patient

        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException(
                "Unable to update patient."
            ) from exc

    async def deactivate(
        self,
        db: AsyncSession,
        *,
        patient_id: int,
    ) -> Patient:
        patient = await self.get_by_id(
            db,
            patient_id=patient_id,
        )

        patient.is_active = False

        try:
            patient = await self.repository.update(
                db,
                patient,
            )

            await db.commit()
            return patient

        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException(
                "Unable to deactivate patient."
            ) from exc


patient_service = PatientService()

__all__ = [
    "PatientService",
    "patient_service",
]