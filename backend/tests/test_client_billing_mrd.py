"""Client contract checks for billing and MRD integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_frontend_billing_and_mrd_modules_exist() -> None:
    assert (ROOT / "frontend/js/billing.js").exists()
    assert (ROOT / "frontend/js/mrd.js").exists()


def test_patient_workspace_wires_billing_and_mrd() -> None:
    app = (ROOT / "frontend/js/app.js").read_text(encoding="utf-8")
    assert 'openBillingWorkspace' in app
    assert 'openMRDWorkspace' in app
