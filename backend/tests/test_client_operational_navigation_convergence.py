from pathlib import Path

def test_merged_operational_navigation_contract():
    html=Path("frontend/index.html").read_text(encoding="utf-8")
    for view in ("inventory","procurement","activity","backups"):
        assert f'data-app-view="{view}"' in html
