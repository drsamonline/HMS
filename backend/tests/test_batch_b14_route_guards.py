"""Gate tests for build-plan batch B14: every route declares a guard, and the
guard is the one its module needs.

The B13 gate proved the mechanism on a toy application. This one proves it on the
real routes, with a real restricted actor: a store keeper who may touch stock and
must not touch patients, billing or the audit trail.
"""

from __future__ import annotations

import asyncio

from app.dependencies.permissions import PUBLIC_PATHS, route_permission


RESTRICTED_ROLE = "store keeper"


def _restricted_headers() -> dict:
    """Seed a store keeper inside the current database and return their header.

    Must be called inside an active ``with make_client()`` block, because the
    harness creates the schema that the account lives in.
    """

    from sqlalchemy import func, select

    from app.auth.jwt import create_access_token
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username="storekeeper",
                password_hash=hash_password("storekeeper-password"),
                full_name="Store Keeper",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            role = (
                await db.execute(
                    select(Role).where(func.lower(Role.role_name) == RESTRICTED_ROLE)
                )
            ).scalar_one_or_none()
            if role is None:
                role = Role(role_name=RESTRICTED_ROLE, description="Stock and stores")
                db.add(role)
                await db.flush()

            # The harness builds its schema with create_all, so the catalogue
            # seeded by migration is absent. Grant this role its template codes
            # here, or the account would hold nothing and every route would
            # refuse it - which would make the test pass for the wrong reason.
            from app.core.permissions import ROLE_TEMPLATES, expand
            from app.models.permission import Permission
            from app.models.role_permission import RolePermission

            for code in sorted(expand(ROLE_TEMPLATES[RESTRICTED_ROLE])):
                permission = (
                    await db.execute(
                        select(Permission).where(Permission.code == code)
                    )
                ).scalar_one_or_none()
                if permission is None:
                    permission = Permission(
                        name=code, code=code, module=code.split(".")[0]
                    )
                    db.add(permission)
                    await db.flush()
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return user.id

    user_id = asyncio.run(_seed())
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------- the guard is present
def test_every_route_outside_the_public_list_declares_a_guard() -> None:
    """The enumeration B15 formalises; cheap enough to assert here too."""

    from app.api.v1.api import api_router

    unguarded = []
    for route in api_router.routes:
        path = getattr(route, "path", "")
        full = f"/api/v1{path}" if not path.startswith("/api") else path
        if full in PUBLIC_PATHS:
            continue
        if route_permission(route) is None:
            unguarded.append((sorted(getattr(route, "methods", []) or []), full))

    assert not unguarded, f"routes with no permission guard: {unguarded}"


def test_the_public_list_is_small_and_named() -> None:
    """A public route is a decision, so the list is short and explicit."""

    assert len(PUBLIC_PATHS) <= 6
    for path in PUBLIC_PATHS:
        assert path.startswith("/api/v1/"), path


# --------------------------------------------------- the guard is the right one
def test_a_restricted_role_cannot_read_patients() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _restricted_headers()
        response = client.get("/api/v1/patients", headers=headers)
    assert response.status_code == 403, response.text
    assert "patients.read" in response.json()["error"]["message"]


def test_a_restricted_role_can_read_stock() -> None:
    """The other half: the guard must not be a blanket refusal."""

    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _restricted_headers()
        response = client.get("/api/v1/inventory-items", headers=headers)
    assert response.status_code == 200, response.text


def test_a_restricted_role_cannot_write_an_invoice() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _restricted_headers()
        response = client.post(
            "/api/v1/billing/invoices",
            headers=headers,
            json={"patient_id": 1, "total_amount": "100.00"},
        )
    assert response.status_code == 403, response.text
    assert "billing.write" in response.json()["error"]["message"]


def test_a_restricted_role_cannot_read_the_audit_trail() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _restricted_headers()
        response = client.get("/api/v1/audit-logs", headers=headers)
    assert response.status_code == 403, response.text


def test_an_administrator_is_not_refused() -> None:
    """The seeded administrator holds every code, so none of the above is a lockout."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        headers = auth_headers()
        assert client.get("/api/v1/patients", headers=headers).status_code == 200
        assert client.get("/api/v1/inventory-items", headers=headers).status_code == 200
        assert client.get("/api/v1/audit-logs", headers=headers).status_code == 200
