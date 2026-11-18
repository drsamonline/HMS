"""Batch 118 — the server-side password policy.

Before this batch the only floor on a password was ``min_length=8`` on four
request schemas, and ``SECURITY.md`` described the policy as client-side. Both
halves of that were wrong: the server did enforce a length floor, and it enforced
nothing else — ``password123``, ``qwertyui`` and ``aaaaaaaa`` were all accepted
for any account, including the administrator the setup wizard creates.

``app.core.password_policy.check_password`` now decides, and the four schemas that
accept a password call it. This file proves three things:

* the policy refuses what it says it refuses, and accepts what a hospital will
  actually type;
* the policy is *wired* — a DTO that stops calling it fails here rather than
  quietly going back to length-only;
* the refusal arrives at the API boundary as a 422 that names the rule, not a 500
  and not a silent acceptance.

No database is needed for most of this: the policy is a pure function and the
schemas are pure Pydantic. The one API test uses the shared harness.
"""

from __future__ import annotations

import pytest
from _qa_harness import make_client, seed_user, token_for_login
from pydantic import ValidationError

from app.core.constants import PASSWORD_MIN_LENGTH
from app.core.password_policy import (
    COMMON_PASSWORDS,
    PASSWORD_MAX_LENGTH,
    PasswordPolicyError,
    check_password,
)
from app.schemas.admin import AdminUserCreate, AdminUserUpdate
from app.schemas.user import UserCreate, UserUpdate

#: Passwords the policy must refuse, with the rule each one breaks. The reasons
#: are checked, not just the refusal: a policy that refuses everything passes a
#: test that only counts exceptions.
REFUSED = [
    ("", "empty"),
    ("       ", "empty"),
    ("short7!", "at least"),
    ("x" * (PASSWORD_MIN_LENGTH - 1), "at least"),
    ("y" * (PASSWORD_MAX_LENGTH + 1), "at most"),
    ("password", "commonly used"),
    ("PASSWORD", "commonly used"),
    ("Password123", "commonly used"),
    ("qwertyui", "commonly used"),
    ("hospital123", "commonly used"),
    ("aaaaaaaa", "single character repeated"),
    ("11111111", "single character repeated"),
]

#: Passwords the policy must accept. These are the shapes a hospital types, and
#: every one of them is used by another test in this suite — a policy that refuses
#: them would turn the rest of the suite red, which is not a policy, it is an outage.
ACCEPTED = [
    "hospital-2026",
    "qa-password",
    "qa-secret-123",
    "qa-b08-password",
    "wrong-password",
    "different-2026",
    "Lan-QA-Passw0rd!",
    "Dr Momin 2026",
]


@pytest.mark.parametrize(("password", "reason"), REFUSED)
def test_policy_refuses_and_names_the_rule(password: str, reason: str) -> None:
    with pytest.raises(PasswordPolicyError) as refusal:
        check_password(password)

    assert reason in str(refusal.value), (
        f"{password!r} was refused, but the message does not name {reason!r}: "
        f"{refusal.value}"
    )


@pytest.mark.parametrize("password", ACCEPTED)
def test_policy_accepts_what_the_hospital_types(password: str) -> None:
    assert check_password(password) == password


def test_the_refusal_never_echoes_the_password() -> None:
    """A rejected password must not reach the log through its own error message."""

    secret = "qwertyui"

    with pytest.raises(PasswordPolicyError) as refusal:
        check_password(secret)

    assert secret not in str(refusal.value)


def test_a_password_equal_to_its_username_is_refused() -> None:
    with pytest.raises(PasswordPolicyError, match="same as the username"):
        check_password("dr.momin", username="dr.momin")

    # Case and surrounding whitespace must not be a way around it.
    with pytest.raises(PasswordPolicyError, match="same as the username"):
        check_password("DR.MOMIN", username="  dr.momin  ")

    # A username of a different password is not a collision.
    assert check_password("dr.momin-2026", username="dr.momin") == "dr.momin-2026"


def test_the_common_list_is_lowercase_and_readable() -> None:
    """The deny-list is compared against a lowercased password, so every entry
    has to be lowercase or it can never match."""

    assert COMMON_PASSWORDS, "an empty deny-list silently accepts everything"

    for entry in COMMON_PASSWORDS:
        assert entry == entry.lower(), f"{entry!r} can never match a lowered password"
        assert entry.strip() == entry, f"{entry!r} carries whitespace"


# --- wiring: a DTO that stops calling the policy fails here -------------------


def test_user_create_uses_the_policy() -> None:
    with pytest.raises(ValidationError, match="commonly used"):
        UserCreate(
            username="new.doctor",
            email="doctor@example.com",
            full_name="New Doctor",
            password="password123",
        )

    created = UserCreate(
        username="new.doctor",
        email="doctor@example.com",
        full_name="New Doctor",
        password="hospital-2026",
    )

    assert created.password == "hospital-2026"


def test_user_create_refuses_its_own_username_as_a_password() -> None:
    with pytest.raises(ValidationError, match="same as the username"):
        UserCreate(
            username="new.doctor",
            email="doctor@example.com",
            full_name="New Doctor",
            password="new.doctor",
        )


def test_user_update_uses_the_policy_only_when_a_password_is_supplied() -> None:
    with pytest.raises(ValidationError, match="commonly used"):
        UserUpdate(password="qwertyui")

    # No password at all is a legal update, and must stay legal.
    assert UserUpdate(full_name="Renamed").password is None


def test_admin_user_create_uses_the_policy() -> None:
    with pytest.raises(ValidationError, match="commonly used"):
        AdminUserCreate(
            username="second.admin",
            password="administrator",
            full_name="Second Admin",
        )

    created = AdminUserCreate(
        username="second.admin",
        password="qa-secret-123",
        full_name="Second Admin",
    )

    assert created.password == "qa-secret-123"


def test_admin_user_update_uses_the_policy() -> None:
    with pytest.raises(ValidationError, match="single character repeated"):
        AdminUserUpdate(password="aaaaaaaa")

    assert AdminUserUpdate(is_active=False).password is None


# --- the boundary: 422 with a message, not a 500 ------------------------------


def test_the_api_refuses_a_common_password_with_422() -> None:
    """The refusal reaches the boundary as a 422 that names the rule.

    ``/administration/users`` is the route an administrator creates an account on,
    so it is the one that has to refuse ``password123`` — and refuse it as a
    validation error, not a 500, and without echoing the password back.
    """

    with make_client() as client:
        seed_user()
        token = token_for_login(client, "qa-admin", "qa-password")

        response = client.post(
            "/api/v1/administration/users",
            json={
                "username": "weak.password.user",
                "full_name": "Weak Password",
                "password": "password123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422, response.text
        assert "commonly used" in response.text
        assert "password123" not in response.text
