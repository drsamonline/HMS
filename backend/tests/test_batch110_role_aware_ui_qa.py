"""Batch 110 (Milestone 7 part 6) — Role-Aware UI & Cross-Module Integration QA.

Locks the role-aware navigation contract end-to-end:

* ``GET /api/v1/auth/me`` answers with the authenticated user's profile,
  including sorted ``roles`` and ``permissions`` lists derived live from
  the ``UserRole``/``RolePermission`` join (no stale client-side cache).
* Inactive roles never leak into the profile payload.
* The client RBAC module gates every ``data-access`` navigation key in
  ``index.html`` through an explicit permission vocabulary, grants
  blanket access to administrator roles, and hides/disables denied
  nav items (aria-hidden + disabled) via ``applyNavigationAccess``.
* Deny-by-default when no profile is available (logged-out shell).
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from _qa_harness import make_client

ROOT = Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# Backend: /auth/me profile contract
# ---------------------------------------------------------------------------


def _seed_profile(*, username: str):
    """Create a user with one active role carrying one permission."""
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username=username,
                password_hash=hash_password("batch110-password"),
                full_name="Batch 110 QA",
                email=None,
                is_active=True,
            )
            role = Role(role_name="Receptionist", description="front desk", is_active=True)
            inactive_role = Role(role_name="Legacy Auditor", description="retired", is_active=False)
            perm = Permission(
                name="Read Patients", code="patients.read", module="patients", is_active=True
            )
            db.add_all([user, role, inactive_role, perm])
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.add(UserRole(user_id=user.id, role_id=inactive_role.id))
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
            await db.commit()
            return int(user.id)

    return asyncio.run(_seed())


def test_auth_me_profile_payload():
    with make_client() as client:
        uid = _seed_profile(username="batch110-profile")
        from app.auth.jwt import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token(subject=str(uid))}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["username"] == "batch110-profile"
        assert body["is_active"] is True
        # Active role only — the inactive Legacy Auditor must not leak.
        assert body["roles"] == ["Receptionist"]
        assert body["permissions"] == ["patients.read"]


def test_auth_me_rejects_nonexistent_user():
    with make_client() as client:
        from app.auth.jwt import create_access_token

        # Well-formed subject, but no matching User row — profile lookup
        # must fail closed (401/404), never 500.
        headers = {"Authorization": f"Bearer {create_access_token(subject='999999')}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code in (401, 404), resp.text


def test_auth_me_refuses_malformed_subject():
    with make_client() as client:
        from app.auth.jwt import create_access_token

        # Non-numeric subject must be rejected as a clean 401
        # (AuthenticationException), never crash the endpoint.
        headers = {"Authorization": f"Bearer {create_access_token(subject='qa-batch103')}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# Client: RBAC navigation contract
# ---------------------------------------------------------------------------


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_every_nav_access_key_has_rbac_vocabulary():
    index = _read("frontend/index.html")
    rbac = _read("frontend/js/rbac.js")
    keys = set(re.findall(r'data-access="([^"]+)"', index))
    assert keys, "index.html must expose data-access markers"
    vocab = {a or b for a, b in re.findall(
        r'^\s*(?:"([\w-]+)"|(\w+))\s*:\s*\[', rbac, re.MULTILINE)}
    missing = keys - vocab
    assert not missing, f"nav keys without ACCESS vocabulary: {sorted(missing)}"


def test_administrator_roles_grant_blanket_access():
    rbac = _read("frontend/js/rbac.js")
    m = re.search(r"ALL_ACCESS_ROLES=new Set\(\[(.*?)\]\)", rbac)
    assert m, "ALL_ACCESS_ROLES set missing"
    roles = set(re.findall(r'"([^"]+)"', m.group(1)))
    assert {"admin", "administrator"} <= roles
    # Case-insensitive normalization applied before the blanket check.
    assert "normalize=v=>String(v??\"\").trim().toLowerCase()" in rbac.replace(" ", "") or "toLowerCase()" in rbac
    assert 'const roles=(profile.roles||[]).map(normalize)' in rbac


def test_can_access_denies_without_profile():
    rbac = _read("frontend/js/rbac.js")
    assert "if(!profile)return false;" in rbac.replace("\r", "")


def test_navigation_gate_hides_and_disables_denied_items():
    rbac = _read("frontend/js/rbac.js")
    assert ".nav-item[data-access]" in rbac
    assert 'button.classList.toggle("hidden",!allowed)' in rbac
    assert 'button.setAttribute("aria-hidden",String(!allowed))' in rbac
    assert "button.disabled=!allowed" in rbac


def test_app_wires_profile_to_navigation_gate():
    app_js = _read("frontend/js/app.js")
    assert "applyNavigationAccess(currentUserProfile)" in app_js
    assert "applyRecordAccess(currentUserProfile)" in app_js
    # Logged-out shell starts deny-by-default.
    assert "applyNavigationAccess(null)" in app_js


def test_api_exposes_current_user_profile_endpoint():
    api_js = _read("frontend/js/api.js")
    assert 'request("/api/v1/auth/me")' in api_js


def test_backend_profile_service_filters_inactive_roles():
    src = _read("backend/app/services/auth.py")
    assert "Role.is_active.is_(True)" in src
    assert "not user.is_active" in src
