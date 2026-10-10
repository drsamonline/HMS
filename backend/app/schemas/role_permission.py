"""
Role-Permission schemas for HHMS.

Defines request and response DTOs for assigning
permissions to roles.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas.base import BaseSchema


class RolePermissionCreate(BaseSchema):
    """
    Request schema for assigning a permission to a role.
    """

    role_id: UUID

    permission_id: UUID


class RolePermissionRead(BaseSchema):
    """
    Response schema representing an active role-permission
    assignment.
    """

    id: UUID

    role_id: UUID

    permission_id: UUID

    assigned_by: UUID | None


__all__ = [
    "RolePermissionCreate",
    "RolePermissionRead",
]