"""The indicator endpoint.

One call returns every declared number for a period, with its definition attached.
A dashboard renders that; it does not compute anything, which is how two screens
stop showing two different occupancies for the same day.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.indicators import BY_CODE, GROUPS
from app.dependencies.database import DatabaseSession
from app.dependencies.permissions import require
from app.services import indicators

router = APIRouter(prefix="/indicators", tags=["Indicators"])


class IndicatorRead(BaseModel):
    code: str
    name: str
    numerator: str
    denominator: str
    unit: str
    standard: str | None
    group: str
    value: float | None
    available: bool


def _period(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    """Parse a period, defaulting to the last thirty days."""

    def parse(value: str | None, default: datetime) -> datetime:
        if not value:
            return default
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail=f"{value} is not an ISO date."
            ) from exc
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    return parse(start, now - timedelta(days=30)), parse(end, now)


@router.get(
    "",
    response_model=list[IndicatorRead],
    dependencies=[Depends(require("reporting.read"))],
)
async def list_indicators(
    db: DatabaseSession,
    start: str | None = Query(default=None, description="ISO date, inclusive"),
    end: str | None = Query(default=None, description="ISO date, exclusive"),
) -> list[IndicatorRead]:
    """Every declared indicator for the period."""

    from_date, to_date = _period(start, end)
    rows = await indicators.compute_all(db, from_date, to_date)
    return [IndicatorRead(**row) for row in rows]


@router.get(
    "/catalogue",
    response_model=list[dict],
    dependencies=[Depends(require("reporting.read"))],
)
async def indicator_catalogue() -> list[dict]:
    """What is declared, without computing anything."""

    return [
        {
            "code": indicator.code,
            "name": indicator.name,
            "numerator": indicator.numerator,
            "denominator": indicator.denominator,
            "unit": indicator.unit,
            "standard": indicator.standard,
            "group": indicator.group,
            "group_label": dict(GROUPS).get(indicator.group, indicator.group),
        }
        for indicator in BY_CODE.values()
    ]


class SeriesPoint(BaseModel):
    start: str
    end: str
    value: float | None
    available: bool


@router.get(
    "/{code}/series",
    response_model=list[SeriesPoint],
    dependencies=[Depends(require("reporting.read"))],
)
async def indicator_series(
    code: str,
    db: DatabaseSession,
    months: int = Query(default=6, ge=1, le=24),
    end: str | None = Query(default=None),
) -> list[SeriesPoint]:
    """One indicator month by month, for a trend line."""

    if code not in BY_CODE:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {code}")
    _from, to_date = _period(None, end)
    return [SeriesPoint(**point) for point in await indicators.series(db, code, to_date, months)]


@router.get(
    "/{code}",
    response_model=IndicatorRead,
    dependencies=[Depends(require("reporting.read"))],
)
async def get_indicator(
    code: str,
    db: DatabaseSession,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> IndicatorRead:
    if code not in BY_CODE:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {code}")
    from_date, to_date = _period(start, end)
    return IndicatorRead(**await indicators.compute(db, code, from_date, to_date))


__all__ = ["router"]
