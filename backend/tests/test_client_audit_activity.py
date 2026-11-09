"""Regression tests for audit/activity visibility contracts."""
from app.schemas.audit_log import AuditLogRead


def test_audit_log_schema_fields() -> None:
    # Contract updated by build plan B07/B11: the read schema now carries the
    # evidence fields (actor, outcome, request id, reason) because the review
    # screen shows them. The fields the client already rendered are unchanged.
    row = AuditLogRead(
        id=1, user_id=2, actor_username="admin", actor_role="admin",
        activity="update", outcome="success", entity_name="Patient", entity_id=3,
        action_timestamp="2026-08-14T10:00:00Z", request_id=None,
        ip_address=None, reason=None, remarks=None,
    )
    assert row.entity_name == "Patient"
    assert row.entity_id == 3
    assert row.outcome == "success"
    assert row.actor_username == "admin"
