"""Business service for the generic departmental activity ledger."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import BusinessRuleException, DatabaseException, ResourceNotFoundException
from app.models.patient import Patient
from app.models.department import Department
from app.models.department_service import DepartmentService
from app.models.service_activity import ServiceActivity
from app.repositories.service_activity import ServiceActivityRepository, service_activity_repository
from app.schemas.service_activity import ServiceActivityCreate


class ServiceActivityManager:
    def __init__(self, repository: ServiceActivityRepository | None = None) -> None:
        self.repository = repository or service_activity_repository

    async def create(self, db: AsyncSession, data: ServiceActivityCreate) -> ServiceActivity:
        if await db.get(Patient, data.patient_id) is None:
            raise ResourceNotFoundException("Patient not found.")
        if await db.get(Department, data.department_id) is None:
            raise ResourceNotFoundException("Department not found.")
        service = await db.get(DepartmentService, data.service_id)
        if service is None:
            raise ResourceNotFoundException("Department service not found.")
        if service.department_id != data.department_id:
            raise BusinessRuleException("Service belongs to another department.")
        record = ServiceActivity(**data.model_dump())
        now = datetime.now(timezone.utc)
        record.created_at = now
        record.updated_at = now
        try:
            await self.repository.add(db, record)
            await db.commit()
            return record
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create service activity.") from exc

    async def list(
        self, db: AsyncSession, *, patient_id: int | None = None,
        department_id=None, skip: int = 0, limit: int = 100
    ) -> list[ServiceActivity]:
        return await self.repository.list_recent(
            db, patient_id=patient_id, department_id=department_id,
            skip=skip, limit=limit
        )


service_activity_manager = ServiceActivityManager()

__all__ = ["ServiceActivityManager", "service_activity_manager"]
