"""Administration DTOs for user, role and permission management."""
from __future__ import annotations
from pydantic import Field
from app.schemas.base import BaseSchema

class AdminUserCreate(BaseSchema):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    mobile_number: str | None = Field(default=None, max_length=20)
    designation: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    role_ids: list[int] = Field(default_factory=list)

class AdminUserUpdate(BaseSchema):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    mobile_number: str | None = Field(default=None, max_length=20)
    designation: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)
    role_ids: list[int] | None = None

class AdminUserRead(BaseSchema):
    id: int
    username: str
    full_name: str
    email: str | None
    mobile_number: str | None
    designation: str | None
    is_active: bool
    role_ids: list[int]
    role_names: list[str]

class AdminRoleCreate(BaseSchema):
    role_name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    permission_ids: list[int] = Field(default_factory=list)

class AdminRoleUpdate(BaseSchema):
    role_name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    permission_ids: list[int] | None = None

class AdminRoleRead(BaseSchema):
    id: int
    role_name: str
    description: str | None
    is_active: bool
    permission_ids: list[int]
    permission_codes: list[str]

__all__ = [
    "AdminUserCreate", "AdminUserUpdate", "AdminUserRead",
    "AdminRoleCreate", "AdminRoleUpdate", "AdminRoleRead",
]
