"""Schemas for PDF rendering and report scheduling (Batch 115/116)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.base import BaseSchema


class PdfRenderRequest(BaseSchema):
    """Wrap any print-envelope payload for server-side PDF rendering."""

    envelope: dict[str, Any]


class ReportScheduleCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=120)
    envelope_type: str = Field(min_length=1, max_length=80)
    request_params: dict[str, Any] = Field(default_factory=dict)
    cadence: Literal["daily", "weekly", "monthly"] = "daily"
    enabled: bool = True


class ReportScheduleUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    envelope_type: str | None = Field(default=None, min_length=1, max_length=80)
    request_params: dict[str, Any] | None = None
    cadence: Literal["daily", "weekly", "monthly"] | None = None
    enabled: bool | None = None


class ReportScheduleRead(BaseSchema):
    id: int
    name: str
    envelope_type: str
    request_params: dict[str, Any]
    cadence: str
    enabled: bool
    created_at: str
    next_run_at: str
    last_run: list[dict[str, Any]] | None = None


class ReportScheduleRunRead(BaseSchema):
    job_id: int
    fired_at: str
    status: Literal["success", "failed"]
    artifact: str | None = None
    bytes: int | None = None
    error: str | None = None


__all__ = [
    "PdfRenderRequest",
    "ReportScheduleCreate",
    "ReportScheduleUpdate",
    "ReportScheduleRead",
    "ReportScheduleRunRead",
]
