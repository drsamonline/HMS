"""HHMS ICD-11 lookup API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies.auth import CurrentUserDependency
from app.schemas.icd11 import ICD11SearchResult
from app.services.icd11 import icd11_service

router = APIRouter(prefix="/icd11", tags=["ICD-11"])


@router.get("/search", response_model=list[ICD11SearchResult])
async def search_icd11(
    _: CurrentUserDependency,
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=10, ge=1, le=25),
) -> list[ICD11SearchResult]:
    return await icd11_service.search(q, limit)


__all__ = ["router"]
