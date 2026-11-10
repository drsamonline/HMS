"""The help a screen needs, where the screen is.

Public in the sense that matters: it needs a login like every other screen, because a
menu of screens a stranger cannot open is not useful to them. It needs no permission,
because a person who cannot read the help for a screen they can open is being asked to
work blind.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import help

router = APIRouter(prefix="/help", tags=["Help"])


@router.get("")
async def list_topics() -> dict:
    """Which screens have help, and what each topic is called."""

    topics = help.available()
    return {"topics": [{"view": view, "title": title} for view, title in topics.items()]}


@router.get("/{view}")
async def get_topic(view: str) -> dict:
    """One screen's help."""

    found = help.topic(view)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No help for {view}.")
    return found


__all__ = ["router"]
