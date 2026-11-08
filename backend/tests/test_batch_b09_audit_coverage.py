"""Gate tests for build-plan batch B09: audit coverage across the services.

The audit trail is only worth something if it has no holes, and a hole is
invisible: the rows that exist look complete. So the gate is structural - it
enumerates the services that write and asserts every one of them either records
an audit row or appears on a frozen list of services that do not yet.

Two limits of this test, stated rather than hidden:

1. It detects a service with **no** audit call, not a function inside a partly
   wired service that was missed. ``billing.py`` records invoices, payments and
   items; a sixth write added to it tomorrow would not be caught here.
2. It matches on the presence of ``audit.record(``, not on the call being
   correct. A record call with the wrong entity name passes.

Both are acceptable for a ratchet: the list below can only shrink, and any new
service that writes without recording fails immediately.
"""

from __future__ import annotations

import re
from pathlib import Path

SERVICES = Path(__file__).resolve().parents[1] / "app" / "services"

WRITE_PATTERN = re.compile(
    r"db\.add\(|db\.commit\(|db\.delete\(|"
    r"repository\.add\(|repository\.update\(|repository\.delete\(|"
    r"_repo\.add\(|_repo\.update\(|_repo\.delete\("
)

#: Services that write but do not record yet, frozen at the end of B09.
#: Removing a name from this set is progress; adding one is a regression.
NOT_YET_WIRED = {
    "administration.py",
    "archive_manager.py",
    "archive_record.py",
    "archive_retention.py",
    "bed.py",
    "case_record.py",
    "department.py",
    "department_service.py",
    "designation.py",
    "diagnosis.py",
    "diet_chart.py",
    "followup.py",
    "goods_receipt.py",
    "inventory_item.py",
    "investigation.py",
    "investigation_result.py",
    "ipd_assessment.py",
    "medical_document.py",
    "medicine.py",
    "medicine_batch.py",
    "nutritional_assessment.py",
    "opd_token.py",
    "operational_year.py",
    "pain_assessment.py",
    "patient_file.py",
    "procurement.py",
    "progress_note.py",
    "report_scheduler.py",
    "service_activity.py",
    "settings.py",
    "stock_batch.py",
    "stock_card.py",
    "user.py",
    "visit.py",
}

#: The audit service writes the audit rows; it does not audit itself.
EXEMPT = {"audit.py", "__init__.py"}


def _sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(SERVICES.glob("*.py"))
    }


def _writers(sources: dict[str, str]) -> set[str]:
    return {
        name
        for name, text in sources.items()
        if name not in EXEMPT and WRITE_PATTERN.search(text)
    }


def _recording(sources: dict[str, str]) -> set[str]:
    return {name for name, text in sources.items() if "audit.record(" in text}


def test_no_new_service_writes_without_recording() -> None:
    """A service added tomorrow that writes without auditing fails here."""
    sources = _sources()
    unaudited = _writers(sources) - _recording(sources)
    unexpected = unaudited - NOT_YET_WIRED
    assert not unexpected, (
        f"{sorted(unexpected)} write to the database without recording an audit "
        "row. Add audit.record() before the commit, or add the service to "
        "NOT_YET_WIRED with a reason."
    )


def test_the_pending_list_does_not_claim_wired_services() -> None:
    """Keeps the ratchet honest: wire a service, drop it from the list."""
    sources = _sources()
    wired_but_listed = _recording(sources) & NOT_YET_WIRED
    assert not wired_but_listed, (
        f"{sorted(wired_but_listed)} now record audit rows but are still listed "
        "as not-yet-wired. Remove them from NOT_YET_WIRED."
    )


def test_the_pending_list_only_shrinks() -> None:
    """A ceiling, so the gap cannot quietly grow back."""

    assert len(NOT_YET_WIRED) <= 34, (
        f"NOT_YET_WIRED has grown to {len(NOT_YET_WIRED)}. The list is a "
        "ratchet: it may only shrink."
    )


def test_the_money_and_stock_paths_are_wired() -> None:
    """The services an auditor would sample first."""
    sources = _sources()
    for name in (
        "billing.py",
        "dispense.py",
        "stock_transaction.py",
        "admission.py",
        "discharge.py",
        "prescription.py",
        "patient.py",
    ):
        assert "audit.record(" in sources[name], f"{name} does not record audit rows"


def test_billing_records_the_activities_an_auditor_asks_for() -> None:
    text = _sources()["billing.py"]
    for activity in (
        "invoice.create",
        "invoice.update",
        "payment.create",
        "invoice.status_change",
        "invoice_item.create",
        "invoice_item.delete",
    ):
        assert activity in text, f"billing does not record {activity}"
