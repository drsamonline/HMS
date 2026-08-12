"""
HHMS Investigation Result Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema


ReportStatus = Literal[
    "draft",
    "verified",
    "released",
]


class InvestigationResultCreate(BaseSchema):
    investigation_id: int = Field(gt=0)

    result_text: str | None = None

    interpretation: str | None = None

    result_datetime: datetime

    verified_by: int | None = Field(
        default=None,
        gt=0,
    )

    verification_datetime: datetime | None = None

    report_status: ReportStatus = "draft"

    remarks: str | None = None

    @model_validator(mode="after")
    def validate_verification(
        self,
    ) -> "InvestigationResultCreate":
        if self.report_status in {
            "verified",
            "released",
        }:
            if self.verified_by is None:
                raise ValueError(
                    "verified_by is required for a "
                    "verified or released report."
                )

            if self.verification_datetime is None:
                raise ValueError(
                    "verification_datetime is required "
                    "for a verified or released report."
                )

        return self


class InvestigationResultUpdate(BaseSchema):
    result_text: str | None = None

    interpretation: str | None = None

    result_datetime: datetime | None = None

    verified_by: int | None = Field(
        default=None,
        gt=0,
    )

    verification_datetime: datetime | None = None

    report_status: ReportStatus | None = None

    remarks: str | None = None


class InvestigationResultRead(BaseSchema):
    id: int
    investigation_id: int
    result_text: str | None
    interpretation: str | None
    result_datetime: datetime
    verified_by: int | None
    verification_datetime: datetime | None
    report_status: str
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "ReportStatus",
    "InvestigationResultCreate",
    "InvestigationResultUpdate",
    "InvestigationResultRead",
]