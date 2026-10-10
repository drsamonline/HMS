"""Backup API schemas."""
from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

class BackupCreate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)

class BackupRead(BaseSchema):
    name: str
    size_bytes: int
    modified_at: datetime

class BackupRestoreResult(BaseSchema):
    restored: str
    database: str
    restored_at: datetime

__all__ = ["BackupCreate", "BackupRead", "BackupRestoreResult"]
