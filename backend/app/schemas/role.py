"""HHMS Role schemas."""
from __future__ import annotations
from pydantic import Field, field_validator
from app.schemas.base import BaseSchema

class RoleBase(BaseSchema):
    role_name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        value=value.strip()
        if not value: raise ValueError("Role name must not be empty.")
        return value

class RoleCreate(RoleBase): ...
class RoleUpdate(BaseSchema):
    role_name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, value: str | None) -> str | None:
        if value is None: return None
        value=value.strip()
        if not value: raise ValueError("Role name must not be empty.")
        return value

class RoleRead(RoleBase):
    id: int
    is_active: bool

__all__=["RoleBase","RoleCreate","RoleUpdate","RoleRead"]
