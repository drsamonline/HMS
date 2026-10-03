"""Client RBAC navigation contract tests."""
from pathlib import Path

ROOT=Path(__file__).parents[2]

def test_client_exposes_current_user_profile_api():
    api=(ROOT/"frontend/js/api.js").read_text(encoding="utf-8")
    assert "getCurrentUserProfile" in api

def test_navigation_contains_access_markers():
    index=(ROOT/"frontend/index.html").read_text(encoding="utf-8")
    for key in ("patients","statistics","reports"):
        assert f'data-access="{key}"' in index

def test_rbac_module_has_admin_and_permission_paths():
    rbac=(ROOT/"frontend/js/rbac.js").read_text(encoding="utf-8")
    assert "ALL_ACCESS_ROLES" in rbac
    assert "permissions" in rbac
