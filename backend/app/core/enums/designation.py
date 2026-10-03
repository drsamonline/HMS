"""
Designation type enumerations for HHMS.

Defines the functional classification of staff designations.
"""

from __future__ import annotations

from enum import StrEnum


class DesignationType(StrEnum):
    """
    Classification of staff designations.
    """

    MEDICAL = "medical"
    NURSING = "nursing"
    PARAMEDICAL = "paramedical"
    ADMINISTRATIVE = "administrative"
    TECHNICAL = "technical"
    SUPPORT = "support"
    MANAGEMENT = "management"


__all__ = [
    "DesignationType",
]