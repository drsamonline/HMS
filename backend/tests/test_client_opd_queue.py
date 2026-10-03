from pathlib import Path

def test_client_opd_queue_contract():
    root=Path(__file__).parents[2]
    api=(root/"frontend/js/api.js").read_text(encoding="utf-8")
    opd=(root/"frontend/js/opd.js").read_text(encoding="utf-8")
    assert "/api/v1/opd-tokens" in api
    assert "Create Visit & Token" in opd
    assert "updateOPDToken" in opd
