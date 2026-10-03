"""HHMS number-sequence generation service."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.number_sequence import NumberSequence


class NumberSequenceService:
    """Generate configurable human-readable identifiers inside the caller transaction."""

    async def next_number(self, db: AsyncSession, sequence_name: str) -> str:
        result = await db.execute(
            select(NumberSequence)
            .where(
                NumberSequence.sequence_name == sequence_name,
                NumberSequence.is_active.is_(True),
            )
            .with_for_update()
        )
        sequence = result.scalar_one_or_none()
        if sequence is None:
            raise ResourceNotFoundException(
                f"Number sequence '{sequence_name}' is not configured."
            )

        now = datetime.now(timezone.utc)
        self._reset_if_due(sequence, now)
        sequence.current_value += 1
        if sequence.last_reset_at is None:
            sequence.last_reset_at = now
        sequence.updated_at = now

        value = str(sequence.current_value).zfill(sequence.padding_length)
        return f"{sequence.prefix}{value}{sequence.suffix}"

    def _reset_if_due(self, sequence: NumberSequence, now: datetime) -> None:
        frequency = (sequence.reset_frequency or "never").strip().lower()
        if frequency == "never":
            return
        if sequence.last_reset_at is None:
            sequence.current_value = 0
            sequence.last_reset_at = now
            return

        last = sequence.last_reset_at
        due = (
            frequency == "daily" and last.date() != now.date()
        ) or (
            frequency == "monthly" and (last.year, last.month) != (now.year, now.month)
        ) or (
            frequency == "yearly" and last.year != now.year
        )
        if due:
            sequence.current_value = 0
            sequence.last_reset_at = now


number_sequence_service = NumberSequenceService()

__all__ = ["NumberSequenceService", "number_sequence_service"]
