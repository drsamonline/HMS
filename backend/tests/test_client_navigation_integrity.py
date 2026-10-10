"""Client navigation integrity and record-level RBAC tests."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_record_tabs_have_permission_keys():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for key in ("clinical", "ipd", "investigations", "billing", "mrd", "reports"):
        assert f'data-record-view="{key}" data-access="{key}"' in html


def test_client_html_has_single_script_bootstrap():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert html.count('src="./js/app.js"') == 1
    assert html.count('src="./js/dashboard.js"') == 1
    assert html.count("</body>") == 1
