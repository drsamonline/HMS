"""A laboratory technician can read the hospital's refund audit.

Not a style problem. Found while explaining why `dashboard.py` is 2,573 lines, and the
size turned out to be the symptom rather than the disease.

Eighteen endpoints live in one router under one permission, `reporting.read`. Six roles
hold it, including **laboratory staff** and **medical records**. The endpoints they gain
access to include:

    /dashboard/refund-audit                 every refund and who authorised it
    /dashboard/receivables-aging            what the hospital is owed, by age
    /dashboard/invoice-overpayments         money taken that should not have been
    /dashboard/invoice-payment-reconciliation
    /dashboard/receipt-numbering-continuity

A lab technician holds four permissions and `billing.read` is **not** one of them. They
cannot open the billing module. They can read the reconciliation reports about it.

That is the finding. The line count is why nobody noticed.
"""

from __future__ import annotations

import pytest


def _lab_technician_headers() -> dict:
    """Seed a laboratory technician and return their header."""

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
                username="labtech",
                password_hash=hash_password("labtech-password"),
                full_name="Laboratory Technician",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            role = (
                await db.execute(
                    select(Role).where(func.lower(Role.role_name) == "laboratory staff")
                )
            ).scalar_one()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return user.id

    import asyncio

    user_id = asyncio.run(_seed())
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- the finding
def test_a_lab_technician_cannot_open_the_billing_module() -> None:
    """The baseline: they hold four permissions and billing.read is not one of them."""

    from app.core.permissions import ROLE_TEMPLATES

    template = ROLE_TEMPLATES["laboratory staff"]
    permissions = getattr(template, "permissions", template)

    assert "reporting.read" in permissions
    assert "billing.read" not in permissions


@pytest.mark.xfail(
    reason=(
        "F-07: the dashboard router guards eighteen endpoints with one permission, so a "
        "role that may not open billing can read the billing reconciliation reports. "
        "This test records the gap. Remove the marker when the router is split."
    ),
    strict=True,
)
def test_a_lab_technician_cannot_read_the_refund_audit() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _lab_technician_headers()
        response = client.get("/api/v1/dashboard/refund-audit", headers=headers)

    assert response.status_code == 403, (
        f"a laboratory technician read the refund audit ({response.status_code})"
    )


@pytest.mark.xfail(reason="F-07: same gap, the receivables side.", strict=True)
def test_a_lab_technician_cannot_read_receivables_aging() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        headers = _lab_technician_headers()
        response = client.get("/api/v1/dashboard/receivables-aging", headers=headers)

    assert response.status_code == 403


# ---------------------------------------------------------------- the shape
def test_the_dashboard_router_is_really_four_modules() -> None:
    """The split is by the question each route answers, not by size.

    Recorded here because the count is what makes the permission problem invisible:
    eighteen routes in one file read as one thing, and they are not one thing.
    """

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints" / "dashboard.py"
    ).read_text(encoding="utf-8")

    financial = [
        "receivables-aging",
        "invoice-receipt-continuity",
        "receipt-numbering-continuity",
        "invoice-payment-reconciliation",
        "payment-method-summary",
        "invoice-overpayments",
        "refund-audit",
    ]
    clinical = ["due-followups", "pending-investigations", "discharge-audit"]
    operational = ["bed-occupancy", "opd-queue-summary"]

    for path in financial + clinical + operational:
        assert f'"/{path}"' in source or f'"{path}"' in source, path

    assert len(financial) == 7, "seven of thirteen routes ask 'does the money reconcile'"


def test_every_dashboard_route_uses_the_same_permission() -> None:
    """This assertion is the finding. It should fail the day somebody splits the router."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints" / "dashboard.py"
    ).read_text(encoding="utf-8")

    import re

    guards = set(re.findall(r'require\("([^"]+)"\)', source))
    assert guards == {"reporting.read"}, (
        "the router now has more than one permission - if that is deliberate, update "
        f"F-07 in docs/CODE_AUDIT.md. Guards found: {sorted(guards)}"
    )
