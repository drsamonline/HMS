"""HHMS number-sequence generation service."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.number_sequence import NumberSequence


class NumberSequenceService:
    """Generate configurable human-readable identifiers inside the caller transaction.

    Concurrency model
    -----------------
    The canonical mechanism is ``SELECT ... FOR UPDATE`` (row lock held for
    the caller's transaction), which serialises minting correctly on real
    database backends (PostgreSQL/MySQL).

    SQLite cannot honour that lock: it has no ``FOR UPDATE`` support and the
    driver silently downgrades the clause, so two concurrent transactions in
    one server process can read the same counter value before either commits
    and mint duplicate identifiers.  For SQLite connections this service
    therefore mints atomically with a single-writer
    ``UPDATE ... SET current_value = current_value + 1 RETURNING ...``
    statement — the increment happens entirely inside the database engine,
    so racing writers can never observe the same pre-increment value.  The
    loaded ORM instance's state is refreshed from the returned row so the
    caller's session stays consistent without issuing a second write at
    flush time.
    """

    def _mint_lock(self) -> asyncio.Lock:
        """Per-event-loop in-process mint lock (lazily bound).

        ``asyncio.Lock`` created at import/service-construction time binds
        to whichever loop first touches it; under multi-loop runtimes
        (e.g. several ``TestClient`` threads, or any off-loop worker) that
        raises ``RuntimeError: ... bound to a different event loop``.
        Keying the lock by the *running* loop keeps same-loop tasks
        serialised while remaining safe across loops.  Cross-loop and
        cross-process safety always comes from the atomic SQLite UPDATE
        below, which is a single write statement serialised by the DB.
        """
        loop = asyncio.get_running_loop()
        locks = getattr(self, "_mint_locks", None)
        if locks is None:
            locks = {}
            self._mint_locks = locks
        lock = locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            locks[loop] = lock
        return lock

    async def next_number(self, db: AsyncSession, sequence_name: str) -> str:
        async with self._mint_lock():
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
            reset_now = sequence.last_reset_at is None
            self._reset_if_due(sequence, now)

            bind_dialect = db.get_bind().dialect.name
            if bind_dialect == "sqlite":
                current_value = await self._mint_sqlite_atomic(
                    db, sequence, now, reset_now=reset_now
                )
            else:
                sequence.current_value += 1
                if sequence.last_reset_at is None:
                    sequence.last_reset_at = now
                sequence.updated_at = now
                current_value = sequence.current_value

            value = str(current_value).zfill(sequence.padding_length)
            return f"{sequence.prefix}{value}{sequence.suffix}"

    async def _mint_sqlite_atomic(
        self,
        db: AsyncSession,
        sequence: NumberSequence,
        now: datetime,
        *,
        reset_now: bool,
    ) -> int:
        """Mint via a single-writer ``UPDATE ... RETURNING`` on SQLite.

        The whole increment executes inside the database engine, so racing
        transactions cannot observe the same pre-increment value even when
        ``FOR UPDATE`` row locking is unavailable.
        """
        result = await db.execute(
            update(NumberSequence)
            .where(NumberSequence.id == sequence.id)
            .values(
                current_value=NumberSequence.current_value + 1,
                last_reset_at=case(
                    (NumberSequence.last_reset_at.is_(None), now),
                    else_=NumberSequence.last_reset_at,
                ),
                updated_at=now,
            )
            .returning(NumberSequence.current_value)
            .execution_options(synchronize_session=False)
        )
        row = result.first()
        if row is None:  # pragma: no cover - defensive
            raise ResourceNotFoundException(
                "Number sequence row disappeared during minting."
            )
        current_value = int(row[0])

        # Mirror the authoritative DB values onto the identity-mapped ORM
        # instance *without* marking it dirty (plain ``instance.__dict__``
        # writes bypass the attribute-change tracker), so session flush does
        # not re-issue an overwrite of the counter.
        state_values = sequence.__dict__
        state_values["current_value"] = current_value
        state_values["updated_at"] = now
        if reset_now or state_values.get("last_reset_at") is None:
            state_values["last_reset_at"] = now
        return current_value

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
