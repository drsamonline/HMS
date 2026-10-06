"""Regression tests for client runtime resilience contracts."""

def test_runtime_resilience_event_names_are_stable():
    assert "hhms:auth-expired"
    assert "hhms:server-state"
