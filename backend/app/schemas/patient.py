"""
HHMS Patient Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class PatientBase(BaseSchema):
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    gender: str = Field(min_length=1, max_length=20)
    date_of_birth: date | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    blood_group: str | None = Field(default=None, max_length=5)
    mobile_number: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    occupation: str | None = Field(default=None, max_length=100)
    marital_status: str | None = Field(default=None, max_length=30)

    @field_validator(
        "first_name",
        "middle_name",
        "last_name",
        "gender",
        "city",
        "state",
        "occupation",
        "marital_status",
        mode="before",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError("Value must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("Value must not be empty.")

        return value


class PatientCreate(PatientBase):
    """Schema for patient registration."""


class PatientUpdate(BaseSchema):
    """Schema for partial patient updates."""

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    gender: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    date_of_birth: date | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    blood_group: str | None = Field(default=None, max_length=5)
    mobile_number: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    occupation: str | None = Field(default=None, max_length=100)
    marital_status: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class PatientRead(PatientBase):
    """Patient returned by the API."""

    id: int
    patient_number: str
    registration_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "PatientBase",
    "PatientCreate",
    "PatientUpdate",
    "PatientRead",
]