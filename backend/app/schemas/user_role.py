"""
User-Role schemas for HHMS.

Defines request and response DTOs for assigning
roles to users.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas.base import BaseSchema


class UserRoleCreate(BaseSchema):
    """
    Request schema for assigning a role to a user.
    """

    user_id: UUID

    role_id: UUID


class UserRoleRead(BaseSchema):
    """
    Response schema representing an active user-role
    assignment.
    """

    id: UUID

    user_id: UUID

    role_id: UUID

    assigned_by: UUID | None


__all__ = [
    "UserRoleCreate",
    "UserRoleRead",
]