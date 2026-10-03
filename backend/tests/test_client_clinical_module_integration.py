"""Regression checks for client clinical module integration."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_clinical_modules_are_integrated_into_client_shell():
    index=(ROOT/"frontend/index.html").read_text(encoding="utf-8")
    app=(ROOT/"frontend/js/app.js").read_text(encoding="utf-8")
    assert (ROOT/"frontend/js/clinical.js").exists()
    assert (ROOT/"frontend/js/ipd.js").exists()
    assert (ROOT/"frontend/js/investigations.js").exists()
    assert "openClinicalWorkspace" in app
    assert "openIPDWorkspace" in app
    assert "openInvestigationsWorkspace" in app
    assert 'data-record-view="investigations"' in index
