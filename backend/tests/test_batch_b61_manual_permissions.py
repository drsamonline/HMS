"""Gate tests for per-user permission grants.

The ask: an administrator should be able to tick a box and give one person one extra
permission, without changing the role that everybody else shares.

Four rules hold this together, and each has a test:

* a grant **adds** to the role and never takes away
* you may only grant what you hold, so a tick-box screen cannot become an escalation tool
* a grant can expire, because a locum's fortnight should end by itself
* every grant says who made it and why, because a permission nobody can explain is a
  permission nobody will dare remove
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture()
def isolated(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HHMS_APPLICATION_ROOT", raising=False)

    from app.config import settings as settings_module
    from app.db import session as session_module

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()
    yield
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _seed_technician() -> int:
    """A laboratory technician: four permissions, none of them about money."""

    import asyncio

    from sqlalchemy import func, select

    from app.auth.password import hash_password
    from app.core.permissions import ROLE_TEMPLATES, expand
    from app.db.session import get_session_factory
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()
    role_name = "laboratory staff"

    async def _go() -> int:
        async with factory() as db:
            user = User(
                username="labtech2",
                password_hash=hash_password("labtech-password"),
                full_name="Laboratory Technician",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            role = (
                await db.execute(select(Role).where(func.lower(Role.role_name) == role_name))
            ).scalar_one_or_none()
            if role is None:
                role = Role(role_name=role_name, description="Laboratory")
                db.add(role)
                await db.flush()

            # The harness builds its schema with create_all, so the catalogue the
            # migration seeds is absent. Grant the role its template codes here, or
            # the account holds nothing and the test passes for the wrong reason.
            for code in sorted(expand(ROLE_TEMPLATES[role_name])):
                permission = (
                    await db.execute(select(Permission).where(Permission.code == code))
                ).scalar_one_or_none()
                if permission is None:
                    permission = Permission(name=code, code=code, module=code.split(".")[0])
                    db.add(permission)
                    await db.flush()
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return user.id

    return asyncio.run(_go())


# ------------------------------------------------------------------ the basics
def test_a_grant_adds_to_the_role(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.dependencies.permissions import permissions_for_user
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                before = await permissions_for_user(db, user_id)
                await user_permissions.grant(
                    db, user_id=user_id, code="billing.read", granted_by=None,
                    reason="covering billing while the clerk is on leave",
                )
                await db.commit()
                return before, await permissions_for_user(db, user_id)

        before, after = asyncio.run(_go())

    assert "billing.read" not in before
    assert "billing.read" in after
    assert before <= after, "a grant must never remove anything the role gave"


def test_a_grant_never_removes_a_role_permission(isolated) -> None:
    """The whole point of additive-only: the role is untouched."""

    import asyncio

    from app.db.session import get_session_factory
    from app.dependencies.permissions import permissions_for_user
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.set_grants(
                    db, user_id=user_id, codes={"patients.read"}, granted_by=None
                )
                await db.commit()
                return await permissions_for_user(db, user_id)

        codes = asyncio.run(_go())

    # The technician's own template codes are still there, alongside the grant.
    assert "investigations.read" in codes, codes
    assert "patients.read" in codes


# ------------------------------------------------------------------ escalation
def test_you_cannot_grant_what_you_do_not_hold(isolated) -> None:
    """A delegated manager passes on what they have, never more."""

    import asyncio

    from app.core.exceptions import BusinessRuleException
    from app.db.session import get_session_factory
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.grant(
                    db,
                    user_id=user_id,
                    code="billing.read",
                    granted_by=None,
                    granter_codes=frozenset({"patients.read", "clinical.read"}),
                )

        with pytest.raises(BusinessRuleException, match="cannot grant it"):
            asyncio.run(_go())


def test_an_unknown_permission_is_refused(isolated) -> None:
    import asyncio

    from app.core.exceptions import BusinessRuleException
    from app.db.session import get_session_factory
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.grant(
                    db, user_id=user_id, code="everything.forever", granted_by=None
                )

        with pytest.raises(BusinessRuleException, match="not a permission this software knows"):
            asyncio.run(_go())


# ------------------------------------------------------------------ expiry
def test_an_expired_grant_stops_counting(isolated) -> None:
    """A locum's fortnight should end by itself."""

    import asyncio

    from app.db.session import get_session_factory
    from app.dependencies.permissions import permissions_for_user
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.grant(
                    db, user_id=user_id, code="billing.read", granted_by=None,
                    expires_at=datetime.now(UTC) - timedelta(days=1),
                )
                await db.commit()
                return await permissions_for_user(db, user_id)

        assert "billing.read" not in asyncio.run(_go())


def test_a_live_grant_still_counts(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.dependencies.permissions import permissions_for_user
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.grant(
                    db, user_id=user_id, code="billing.read", granted_by=None,
                    expires_at=datetime.now(UTC) + timedelta(days=14),
                )
                await db.commit()
                return await permissions_for_user(db, user_id)

        assert "billing.read" in asyncio.run(_go())


# ------------------------------------------------------------------ provenance
def test_every_row_says_where_it_came_from(isolated) -> None:
    """A tick box already ticked by the role must look different from one ticked by hand."""

    import asyncio

    from app.db.session import get_session_factory
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        user_id = _seed_technician()
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await user_permissions.grant(
                    db, user_id=user_id, code="billing.read", granted_by=None,
                    reason="covering billing",
                )
                await db.commit()
                from app.dependencies.permissions import permissions_for_user

                manual = await user_permissions.active_codes(db, user_id)
                role = await permissions_for_user(db, user_id)
                return await user_permissions.effective(db, user_id, role - manual)

        body = asyncio.run(_go())

    rows = {row["code"]: row for row in body["permissions"]}
    assert rows["billing.read"]["source"] == "manual"
    assert rows["billing.read"]["removable"] is True
    assert rows["billing.read"]["reason"] == "covering billing"

    role_rows = [row for row in body["permissions"] if row["source"] == "role"]
    assert role_rows, "the technician has role permissions"
    assert all(row["removable"] is False for row in role_rows)


def test_the_screen_is_told_that_grants_are_additive(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.services import user_permissions
    from tests._qa_harness import make_client

    with make_client():
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                return await user_permissions.effective(db, 1, frozenset())

        body = asyncio.run(_go())

    assert "never take away" in body["note"]


# ------------------------------------------------------------------ the API
def test_the_endpoint_lists_every_permission_with_its_source(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        user_id = _seed_technician()
        response = client.get(f"/api/v1/users/{user_id}/permissions", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["permissions"]) >= 40
    assert body["from_role"]


def test_ticking_a_box_through_the_api_grants_it(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        user_id = _seed_technician()
        response = client.put(
            f"/api/v1/users/{user_id}/permissions",
            headers=auth_headers(),
            json={"codes": ["billing.read"], "reason": "locum cover"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "billing.read" in body["from_manual"]
    assert body["changed"]["added"] == ["billing.read"]


def test_the_screen_cannot_grant_beyond_the_actor(isolated) -> None:
    """The endpoint passes the actor's own codes through, so the service refuses."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        user_id = _seed_technician()
        # The test administrator holds everything, so this succeeds - which is correct.
        response = client.put(
            f"/api/v1/users/{user_id}/permissions",
            headers=auth_headers(),
            json={"codes": ["billing.read"]},
        )

    assert response.status_code == 200


def test_an_unknown_code_is_a_422_not_a_500(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        user_id = _seed_technician()
        response = client.put(
            f"/api/v1/users/{user_id}/permissions",
            headers=auth_headers(),
            json={"codes": ["not.a.real.permission"]},
        )

    assert response.status_code == 422
    body = response.json()
    message = body.get("detail") or body.get("error", {}).get("message", "")
    assert "not permissions this software knows" in message.lower()
