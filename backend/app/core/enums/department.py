"""
Department type enumerations for HHMS.

Defines the functional classification of hospital departments.
"""

from __future__ import annotations

from enum import StrEnum


class DepartmentType(StrEnum):
    """
    Functional classification of hospital departments.
    """

    CLINICAL = "clinical"
    DIAGNOSTIC = "diagnostic"
    ADMINISTRATIVE = "administrative"
    FINANCIAL = "financial"
    SUPPORT = "support"


__all__ = [
    "DepartmentType",
]