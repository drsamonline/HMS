"""HHMS permission schemas."""
from __future__ import annotations
from pydantic import Field
from app.schemas.base import BaseSchema

class PermissionBase(BaseSchema):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=100)
    module: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

class PermissionCreate(PermissionBase): ...

class PermissionUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    code: str | None = Field(default=None, min_length=2, max_length=100)
    module: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

class PermissionRead(PermissionBase):
    id: int
    is_active: bool

__all__=["PermissionBase","PermissionCreate","PermissionUpdate","PermissionRead"]
