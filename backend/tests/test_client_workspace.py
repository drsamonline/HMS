from pathlib import Path

def test_client_workspace_assets_exist():
    root=Path(__file__).resolve().parents[2]
    assert (root/"frontend/index.html").exists()
    assert (root/"frontend/js/api.js").exists()
    assert (root/"frontend/js/app.js").exists()
