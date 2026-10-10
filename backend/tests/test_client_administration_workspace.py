"""Contract checks for the administration workspace batch."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def test_administration_assets_exist():
    assert (ROOT / "frontend/js/admin.js").exists()
    assert (ROOT / "backend/app/api/v1/endpoints/administration.py").exists()
    assert (ROOT / "backend/app/services/administration.py").exists()

def test_admin_api_contract_is_exposed():
    endpoint = (ROOT / "backend/app/api/v1/endpoints/administration.py").read_text(encoding="utf-8")
    assert '/users' in endpoint
    assert '/roles' in endpoint
    assert '/permissions' in endpoint
