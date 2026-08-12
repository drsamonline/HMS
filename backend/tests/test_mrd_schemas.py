"""Schema tests for HHMS MRD records."""
from datetime import datetime, timezone

from app.schemas.archive_record import ArchiveRecordCreate
from app.schemas.patient_file import PatientFileCreate


def test_patient_file_allows_optional_location_fields() -> None:
    record = PatientFileCreate(
        patient_id=1,
        file_no="MRD-0001",
        file_type="OPD",
    )
    assert record.location is None
    assert record.shelf_no is None
    assert record.rack_no is None


def test_archive_record_allows_progressive_completion() -> None:
    record = ArchiveRecordCreate(patient_file_id=1)
    assert record.archive_date is None
    assert record.archive_location is None
    assert record.box_no is None


def test_archive_record_accepts_partial_archive_data() -> None:
    record = ArchiveRecordCreate(
        patient_file_id=1,
        archive_date=datetime.now(timezone.utc),
        archive_location="MRD Room",
    )
    assert record.archive_location == "MRD Room"
