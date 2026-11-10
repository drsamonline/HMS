"""What this installation is licensed to run.

A customer asking "what do I have?" should not have to read the licence file or the
module list and work it out. This answers it, and names the modules the edition does
not include, so an upgrade conversation starts from the same facts on both sides.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.editions import EDITIONS, current_edition
from app.modules.registry import MODULES

router = APIRouter(prefix="/edition", tags=["Edition"])


@router.get("")
async def edition() -> dict:
    """The edition, its licence, and what it excludes."""

    running = current_edition()
    included = [module.code for module in MODULES if module.code in running.modules]
    excluded = [
        {"code": module.code, "name": module.name}
        for module in MODULES
        if module.code not in running.modules
    ]

    return {
        "code": running.code,
        "name": running.name,
        "licence": running.licence,
        "summary": running.summary,
        "modules": included,
        "features": list(running.features),
        "not_included": excluded,
        "upgrades": [
            {
                "code": other.code,
                "name": other.name,
                "summary": other.summary,
                "adds": [
                    code for code in other.modules if code not in running.modules
                ],
            }
            for other in EDITIONS.values()
            if other.code != running.code
            and set(other.modules) > set(running.modules)
        ],
    }


__all__ = ["router"]
