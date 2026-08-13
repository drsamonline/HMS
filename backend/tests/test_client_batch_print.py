"""Client batch printing contract tests."""

def test_batch_print_assets_exist():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    assert (root/"frontend/js/print.js").exists()
    assert (root/"frontend/js/reports.js").exists()
    assert (root/"frontend/css/print.css").exists()
