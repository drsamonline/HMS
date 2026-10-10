"""Contract tests for the client IPD workspace batch."""

from pathlib import Path


def test_ipd_workspace_assets_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "frontend/js/ipd.js").exists()


def test_ipd_workspace_api_names_are_present() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "frontend/js/api.js").read_text(encoding="utf-8")
    for name in ("listAdmissions", "createAdmission", "listIPDAssessments", "createDischarge"):
        assert f"export async function {name}" in source
