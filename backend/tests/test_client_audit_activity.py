"""Regression tests for audit/activity visibility contracts."""
from app.schemas.audit_log import AuditLogRead


def test_audit_log_schema_fields() -> None:
    row = AuditLogRead(
        id=1, user_id=2, activity="update", entity_name="Patient", entity_id=3,
        action_timestamp="2026-08-14T10:00:00Z", ip_address=None, remarks=None,
    )
    assert row.entity_name == "Patient"
    assert row.entity_id == 3
