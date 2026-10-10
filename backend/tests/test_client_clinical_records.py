"""Client clinical records batch 10 contract tests."""
from pathlib import Path

def test_clinical_module_and_api_exports_exist():
    api = Path("frontend/js/api.js").read_text(encoding="utf-8")
    clinical = Path("frontend/js/clinical.js").read_text(encoding="utf-8")
    for name in ["listDiagnoses", "createDiagnosis", "searchICD11", "listFollowups", "createFollowup", "createPrescription", "listMedicines"]:
        assert name in api
    assert "openClinicalWorkspace" in clinical
    assert "Quick Generals" in clinical
    assert "Modalities JSON" in clinical

def test_client_has_explicit_clinical_workspace_entry():
    app = Path("frontend/js/app.js").read_text(encoding="utf-8")
    assert 'data-record-view="${view}"' in app or 'view==="clinical"' in app
    assert "openClinicalWorkspace" in app
