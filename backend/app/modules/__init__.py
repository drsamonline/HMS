"""HHMS module registry package."""

from app.modules.registry import MODULES, BY_CODE, ModuleSpec, depends_on, resolve

__all__ = ["MODULES", "BY_CODE", "ModuleSpec", "depends_on", "resolve"]
