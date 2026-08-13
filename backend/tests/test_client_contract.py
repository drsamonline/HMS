from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_client_project_files_exist():
    for rel in ("client/HHMS.Client/HHMS.Client.csproj","client/HHMS.Client/Program.cs","client/HHMS.Client/MainForm.cs","client/HHMS.Client/Bridge/DiscoveryBridge.cs","frontend/index.html"):
        assert (ROOT/rel).is_file()
def test_webview_uses_stable_hhms_origin():
    text=(ROOT/"client/HHMS.Client/MainForm.cs").read_text(encoding="utf-8")
    assert "app.hhms.local" in text and "SetVirtualHostNameToFolderMapping" in text
def test_auth_and_patient_contracts():
    cfg=(ROOT/"frontend/js/config.js").read_text(encoding="utf-8")
    api=(ROOT/"frontend/js/api.js").read_text(encoding="utf-8")
    assert "/api/v1/auth/login" in cfg and "/api/v1/patients" in cfg and "Authorization" in api
