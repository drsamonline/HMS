"""The public provenance claim.

Served at a well-known path so it can be read without a login: a claim nobody can
read is not a claim. It reveals nothing the source does not already say, and it means
an unmodified copy announces where it came from.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.provenance import payload

router = APIRouter(prefix="/provenance", tags=["Provenance"])


@router.get("")
async def provenance() -> dict:
    """What this installation is, and who owns it."""

    return payload()


__all__ = ["router"]
