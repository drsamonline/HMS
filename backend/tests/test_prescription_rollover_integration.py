"""Batch 77 — Prescription rollover end-to-end contract.

Unlike the static contract tests, this suite actually executes
``archive_manager.rollover_case_year`` against a throwaway SQLite database and
proves the prescription lineage survives physical visit/dispense archival:

* completed-year prescriptions/items are removed from the live database,
* permanent archive-reference rows preserve identity and lineage pointers,
* live dispense rows keep working with a detached ``prescription_item_id``,
* archived dispense rows remain readable through the historical endpoint
  query (``read_dispenses``) even though their parent prescription/item and
  visit rows no longer exist in the archive snapshot's joined tables.
"""
from __future__ import annotations

import asyncio
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[2]

ARCHIVE_YEAR = 2024


def _runtime_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point every HHMS runtime path at the temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_file = data_dir / "hhms.sqlite3"

    from app.config import runtime_paths

    monkeypatch.setattr(runtime_paths, "application_root", lambda: tmp_path)
    monkeypatch.setattr(runtime_paths, "data_directory", lambda: data_dir)
    monkeypatch.setattr(runtime_paths, "database_path", lambda: db_file)
    monkeypatch.setattr(
        runtime_paths, "archive_directory", lambda: data_dir / "archive"
    )
    monkeypatch.setattr(
        runtime_paths, "cold_archive_directory", lambda: data_dir / "cold-archive"
    )
    monkeypatch.setattr(
        runtime_paths, "backups_directory", lambda: data_dir / "backups"
    )

    # The services modules bind these helpers at import time; rebind them so
    # both archive_manager and backup_service operate on the temp database.
    import app.services.archive_manager as am
    import app.services.backup as bs

    monkeypatch.setattr(am, "database_path", lambda: db_file)
    monkeypatch.setattr(
        am, "archive_directory", lambda: runtime_paths.archive_directory()
    )
    monkeypatch.setattr(
        am, "cold_archive_directory", lambda: runtime_paths.cold_archive_directory()
    )
    monkeypatch.setattr(bs, "database_path", lambda: db_file)
    monkeypatch.setattr(bs, "backups_directory", lambda: data_dir / "backups")

    # One cache entry may already hold absolute paths from earlier suites.
    try:
        from app.config.settings import get_settings

        get_settings.cache_clear()
    except AttributeError:
        pass

    return db_file


@pytest.fixture()
def session_factory(tmp_path, monkeypatch):
    _runtime_paths(tmp_path, monkeypatch)

    import app.models  # noqa: F401  (register all mappers)
    from app.models.base import Base

    url = f"sqlite+aiosqlite:///{(tmp_path / 'data' / 'hhms.sqlite3').as_posix()}"
    engine = create_async_engine(url)

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    asyncio.run(engine.dispose())


async def _seed(db: AsyncSession) -> dict[str, int]:
    from app.models.dispense_record import DispenseRecord
    from app.models.medicine import Medicine
    from app.models.patient import Patient
    from app.models.prescription import Prescription
    from app.models.prescription_item import PrescriptionItem
    from app.models.visit import Visit

    now = datetime.now(timezone.utc)

    patient = Patient(
        patient_number="P-0001",
        first_name="Test",
        last_name="Patient",
        gender="male",
        registration_date=date(2024, 1, 5),
    )
    db.add(patient)
    await db.flush()

    visit = Visit(
        patient_id=patient.id,
        visit_number="V-2024-0001",
        visit_type="follow-up",
        visit_datetime=datetime(2024, 6, 1, tzinfo=timezone.utc),
        consultation_status="completed",
        consulting_doctor_id=1,
        visit_year=ARCHIVE_YEAR,
        storage_tier="live",
        is_current_year=False,
    )
    db.add(visit)
    await db.flush()

    medicine = Medicine(
        name="Arsenicum Album",
        potency="30C",
        generic_name="Arsenicum album",
    )
    db.add(medicine)
    await db.flush()

    prescription = Prescription(
        visit_id=visit.id,
        prescription_number="RX-2024-0001",
        prescribed_by=1,
        prescription_datetime=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
        diagnosis="test diagnosis",
        prescription_year=ARCHIVE_YEAR,
        storage_tier="live",
        is_current_year=False,
        created_at=now,
        updated_at=now,
    )
    db.add(prescription)
    await db.flush()

    item = PrescriptionItem(
        prescription_id=prescription.id,
        medicine_id=medicine.id,
        dosage="1 drop",
        frequency="TDS",
        duration_days=5,
        quantity=1,
        item_year=ARCHIVE_YEAR,
        storage_tier="live",
        is_current_year=False,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    await db.flush()

    archived_dispense = DispenseRecord(
        prescription_item_id=item.id,
        medicine_id=medicine.id,
        stock_batch_id=None,
        quantity_dispensed=1,
        dispense_date=date(2024, 6, 2),
        dispensed_by=1,
        dispense_year=ARCHIVE_YEAR,
        storage_tier="live",
        is_current_year=False,
    )
    live_dispense = DispenseRecord(
        prescription_item_id=item.id,
        medicine_id=medicine.id,
        stock_batch_id=None,
        quantity_dispensed=2,
        dispense_date=date(2025, 1, 3),
        dispensed_by=1,
        dispense_year=2025,
        storage_tier="live",
        is_current_year=True,
    )
    db.add_all([archived_dispense, live_dispense])
    await db.flush()

    ids = {
        "patient_id": patient.id,
        "visit_id": visit.id,
        "prescription_id": prescription.id,
        "item_id": item.id,
        "medicine_id": medicine.id,
        "archived_dispense_id": archived_dispense.id,
        "live_dispense_id": live_dispense.id,
    }
    await db.commit()
    return ids


def test_rollover_archives_prescription_lineage_end_to_end(session_factory):
    async def run():
        from app.models.clinical_archive_reference import (
            PrescriptionArchiveReference,
            PrescriptionItemArchiveReference,
        )
        from app.models.dispense_record import DispenseRecord
        from app.models.prescription import Prescription
        from app.models.prescription_item import PrescriptionItem
        from app.models.visit import Visit
        from app.services.archive_manager import archive_manager

        async with session_factory() as db:
            ids = await _seed(db)

            preview = await archive_manager.rollover_preview(db)
            assert preview["prescription_count"] == 1
            assert preview["prescription_item_count"] == 1

            result = await archive_manager.rollover_case_year(db, ARCHIVE_YEAR)
            assert result["status"] == "completed"
            assert result["prescriptions_archived"] == 1
            assert result["prescription_items_archived"] == 1

            # Live rows are physically gone...
            assert await db.scalar(
                select(Prescription).where(
                    Prescription.id == ids["prescription_id"]
                )
            ) is None
            assert await db.scalar(
                select(PrescriptionItem).where(
                    PrescriptionItem.id == ids["item_id"]
                )
            ) is None
            assert await db.scalar(
                select(Visit).where(Visit.id == ids["visit_id"])
            ) is None

            # ...but identity/lineage survive as permanent references.
            pres_ref = await db.scalar(
                select(PrescriptionArchiveReference).where(
                    PrescriptionArchiveReference.original_prescription_id
                    == ids["prescription_id"]
                )
            )
            assert pres_ref is not None
            assert pres_ref.visit_id == ids["visit_id"]
            assert pres_ref.prescription_number == "RX-2024-0001"

            item_ref = await db.scalar(
                select(PrescriptionItemArchiveReference).where(
                    PrescriptionItemArchiveReference.original_item_id
                    == ids["item_id"]
                )
            )
            assert item_ref is not None
            assert item_ref.original_prescription_id == ids["prescription_id"]

            # Archived dispense row deleted; live dispense row detached but kept.
            assert await db.scalar(
                select(DispenseRecord).where(
                    DispenseRecord.id == ids["archived_dispense_id"]
                )
            ) is None
            survivor = await db.scalar(
                select(DispenseRecord).where(
                    DispenseRecord.id == ids["live_dispense_id"]
                )
            )
            assert survivor is not None
            assert survivor.prescription_item_id is None

            from app.models.archive_manifest import ArchiveManifest

            manifest = await db.scalar(select(ArchiveManifest))
            assert manifest is not None

            # Historical read resolves inside the archive snapshot.
            rows = await archive_manager.read_prescriptions(
                db, ARCHIVE_YEAR, ids["patient_id"]
            )
            assert len(rows) == 1
            assert rows[0]["prescription_number"] == "RX-2024-0001"

            item_rows = await archive_manager.read_prescription_items(
                db, ARCHIVE_YEAR, ids["patient_id"]
            )
            assert len(item_rows) == 1
            assert item_rows[0]["dosage"] == "1 drop"

            dispense_rows = await archive_manager.read_dispenses(
                db, ARCHIVE_YEAR, ids["patient_id"]
            )
            assert len(dispense_rows) == 1
            assert dispense_rows[0]["id"] == ids["archived_dispense_id"]

    asyncio.run(run())


def test_read_dispenses_falls_back_when_snapshot_lacks_lineage(
    session_factory, tmp_path
):
    """Legacy archives (pre-Batch-77) had visits/prescriptions deleted without
    lifecycle rows; the dispense read must still surface archived dispenses."""
    from app.models.archive_manifest import ArchiveManifest
    from app.services.archive_manager import archive_manager

    async def run():
        async with session_factory() as db:
            ids = await _seed(db)
            target, chosen, checksum = await archive_manager._prepare_archive_file(
                db, ARCHIVE_YEAR
            )
            # Simulate a legacy snapshot: strip the lineage tables entirely so
            # the primary JOIN cannot resolve, forcing the fallback read.
            con = sqlite3.connect(target)
            con.executescript(
                "DROP TABLE PrescriptionItem; DROP TABLE Prescription; DROP TABLE Visit;"
            )
            con.commit()
            con.close()
            manifest = ArchiveManifest(
                archive_year=ARCHIVE_YEAR,
                storage_tier=chosen,
                file_path=str(target),
                checksum_sha256=checksum,
                size_bytes=target.stat().st_size,
                verified=True,
            )
            db.add(manifest)
            await db.commit()

            rows = await archive_manager.read_dispenses(
                db, ARCHIVE_YEAR, ids["patient_id"]
            )
            assert len(rows) == 1
            assert rows[0]["id"] == ids["archived_dispense_id"]

    asyncio.run(run())
