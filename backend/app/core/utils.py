"""
HHMS Core Utilities

Framework-independent utility functions used across the
Hospital Homoeopathic Management System (HHMS).

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

T = TypeVar("T")


def utc_now() -> datetime:
    """
    Return the current UTC-aware datetime.

    Returns
    -------
    datetime
        Current UTC datetime.
    """
    return datetime.now(UTC)


def generate_uuid() -> UUID:
    """
    Generate a UUID version 4.

    Returns
    -------
    UUID
        Random UUID.
    """
    return uuid4()


def is_blank(value: str | None) -> bool:
    """
    Determine whether a string is empty or contains
    only whitespace.

    Parameters
    ----------
    value : str | None

    Returns
    -------
    bool
    """
    return value is None or value.strip() == ""


def normalize_string(value: str) -> str:
    """
    Normalize whitespace in a string.

    Parameters
    ----------
    value : str

    Returns
    -------
    str
    """
    return " ".join(value.strip().split())


def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a new dictionary with all keys containing
    None values removed.

    Parameters
    ----------
    data : dict[str, Any]

    Returns
    -------
    dict[str, Any]
    """
    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


def chunks(items: list[T], size: int) -> list[list[T]]:
    """
    Split a list into equally sized chunks.

    Parameters
    ----------
    items : list[T]
        Source list.

    size : int
        Maximum number of elements per chunk.

    Returns
    -------
    list[list[T]]
        Chunked list.

    Raises
    ------
    ValueError
        If the chunk size is less than one.
    """

    if size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    return [
        items[index : index + size]
        for index in range(0, len(items), size)
    ]