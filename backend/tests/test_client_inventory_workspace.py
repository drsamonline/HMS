"""Client inventory workspace contract tests."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_inventory_workspace_module_exists():
    assert (ROOT/"frontend/js/inventory.js").is_file()
def test_inventory_api_contains_stock_endpoints():
    text=(ROOT/"frontend/js/api.js").read_text(encoding="utf-8")
    assert "/api/v1/inventory-items" in text
    assert "/api/v1/stock-transactions" in text
