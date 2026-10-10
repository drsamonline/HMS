from pathlib import Path
def test_procurement_wiring_exists():
 root=Path(__file__).resolve().parents[1]
 assert (root/'app/api/v1/endpoints/procurement.py').exists()
 assert (root.parent/'frontend/js/procurement.js').exists()
