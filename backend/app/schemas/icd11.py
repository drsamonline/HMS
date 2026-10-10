"""HHMS ICD-11 lookup schemas."""

from app.schemas.base import BaseSchema


class ICD11SearchResult(BaseSchema):
    code: str | None = None
    title: str
    uri: str | None = None
    release: str


__all__ = ["ICD11SearchResult"]
