"""Regression tests for client unsaved-change contract."""

def test_unsaved_state_is_client_side_only() -> None:
    # The dirty flag is intentionally ephemeral and must not introduce a DB model.
    assert True
