"""Schemas for the configurable department-service master."""
from __future__ import annotations

from uuid import UUID
from pydantic import Field
from app.schemas.base import BaseSchema


class DepartmentServiceCreate(BaseSchema):
    department_id: UUID
    parent_service_id: UUID | None = None
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    service_type: str = Field(default="service", min_length=1, max_length=30)
    supports_gender_breakdown: bool = True
    supports_new_old: bool = True
    supports_fulfillment_mode: bool = False


class DepartmentServiceUpdate(BaseSchema):
    parent_service_id: UUID | None = None
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    service_type: str | None = Field(default=None, min_length=1, max_length=30)
    supports_gender_breakdown: bool | None = None
    supports_new_old: bool | None = None
    supports_fulfillment_mode: bool | None = None
    is_active: bool | None = None


class DepartmentServiceRead(DepartmentServiceCreate):
    id: UUID
    is_active: bool


__all__ = [
    "DepartmentServiceCreate",
    "DepartmentServiceUpdate",
    "DepartmentServiceRead",
]
