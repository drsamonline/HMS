"""Shared validation for optional department/service classification."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.department import Department
from app.models.department_service import DepartmentService


async def resolve_activity_context(
    db: AsyncSession,
    *,
    department_id: UUID | None,
    service_id: UUID | None,
) -> tuple[UUID | None, UUID | None]:
    """Validate an optional department/service pair and infer the department when possible."""
    if service_id is None:
        if department_id is not None and await db.get(Department, department_id) is None:
            raise ResourceNotFoundException("Department not found.")
        return department_id, None

    service = await db.get(DepartmentService, service_id)
    if service is None:
        raise ResourceNotFoundException("Department service not found.")

    if department_id is not None and service.department_id != department_id:
        raise BusinessRuleException(
            "The selected service does not belong to the selected department."
        )

    return service.department_id, service.id


__all__ = ["resolve_activity_context"]
