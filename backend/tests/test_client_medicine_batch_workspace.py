"""Client medicine/batch workspace contract tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_medicine_master_workspace_is_reachable_from_admin_module() -> None:
    source = (ROOT / "frontend/js/admin.js").read_text(encoding="utf-8")
    assert "renderPharmacyMaster" in source
    assert "listMedicines" in source
    assert "listMedicineBatches" in source

def test_medicine_batch_api_is_exposed_to_client() -> None:
    source = (ROOT / "frontend/js/api.js").read_text(encoding="utf-8")
    for name in ("createMedicine", "updateMedicine", "listMedicineBatches", "createMedicineBatch", "updateMedicineBatch"):
        assert f"export async function {name}" in source
