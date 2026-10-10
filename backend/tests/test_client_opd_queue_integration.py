from pathlib import Path

def test_opd_client_assets_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "frontend/js/opd.js").exists()
    assert (root / "frontend/index.html").exists()
    assert (root / "frontend/js/rbac.js").exists()
