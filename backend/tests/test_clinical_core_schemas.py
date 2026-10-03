"""Clinical Core schema tests."""

from app.schemas.case_record import CaseRecordCreate


def test_case_record_allows_partial_documentation() -> None:
    record = CaseRecordCreate(
        patient_id=1,
        chief_complaints="Headache for three days.",
        modalities={
            "pressure": {
                "effect": "amel",
                "details": None,
            }
        },
    )

    assert record.patient_id == 1
    assert record.mental_generals is None
    assert record.family_history is None
    assert record.modalities["pressure"]["effect"] == "amel"


def test_case_record_rejects_two_encounters() -> None:
    try:
        CaseRecordCreate(
            patient_id=1,
            visit_id=2,
            admission_id=3,
        )
    except ValueError:
        return

    raise AssertionError("Both visit_id and admission_id must be rejected.")
