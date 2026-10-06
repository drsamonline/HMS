"""Regression checks for client operational workspace integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_client_api_exposes_procurement_calls() -> None:
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    for name in ("listSuppliers", "createSupplier", "listPurchaseOrders", "createPurchaseOrder", "createGoodsReceipt"):
        assert f"export async function {name}" in api

def test_shell_wires_operational_workspaces() -> None:
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "frontend" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'data-app-view="inventory"' in html
    assert 'data-app-view="procurement"' in html
    assert 'data-app-view="activity"' in html
    assert 'data-record-view="pharmacy"' in html
    for fn in ("openInventoryWorkspace", "openProcurementWorkspace", "openActivityWorkspace", "openPharmacyWorkspace"):
        assert fn in app
