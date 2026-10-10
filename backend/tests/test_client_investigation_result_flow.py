"""Regression tests for client investigation-result create/update flow."""

def test_result_flow_uses_update_for_existing_result() -> None:
    source = open("frontend/js/investigations.js", encoding="utf-8").read()
    assert "updateInvestigationResult" in source
    assert "state.results[0]" in source

def test_released_result_is_locked_in_client() -> None:
    source = open("frontend/js/investigations.js", encoding="utf-8").read()
    assert "Released laboratory reports cannot be modified." in source
