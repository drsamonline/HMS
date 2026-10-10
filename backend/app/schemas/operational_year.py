from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

class OperationalYearRead(BaseModel):
    basis: Literal["calendar", "financial"]
    start_month: int = Field(ge=1, le=12)
    start_day: int = Field(ge=1, le=31)
    current_year: int
    label: str

class OperationalYearUpdate(BaseModel):
    basis: Literal["calendar", "financial"]
    start_month: int = Field(default=4, ge=1, le=12)
    start_day: int = Field(default=1, ge=1, le=31)
