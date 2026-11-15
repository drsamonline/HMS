"""
HHMS Server-Side Password Policy
================================

One function decides whether the server will accept a password, and it runs
before the password is hashed and stored. Until this module existed the only
floor was ``min_length=8`` on the request schema, and ``SECURITY.md`` described
the policy as client-side, which was wrong in both directions: the length floor
*was* enforced by the server, and nothing else was enforced anywhere.

The policy is deliberately small. It refuses four things:

1. a password shorter than ``PASSWORD_MIN_LENGTH``;
2. a password on the short common-password list below;
3. a password made of one character repeated;
4. a password identical to the username it is issued for.

It does **not** impose character-class rules. A composition rule ("one upper,
one digit, one symbol") reliably produces ``Password1!`` and is measurably worse
than a length floor plus a small deny-list; what this project needs from a LAN
hospital system is a refusal of the passwords people actually type, not a rule
that pushes them towards a predictable pattern.

Two notes for whoever changes this file:

* ``BaseSchema`` sets ``str_strip_whitespace=True``, so the password this module
  sees is the password that will be hashed. Leading and trailing spaces are not
  part of an HHMS password, and a whitespace-only password is empty.
* The error message never echoes the password back. A rejected password reaches
  the log through the validation error, and a password in a log file is a
  password in a backup.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.core.constants import PASSWORD_MIN_LENGTH

#: The upper bound the request schemas already carry, repeated here so a caller
#: that bypasses the schema gets the same answer as the API boundary.
PASSWORD_MAX_LENGTH = 256

#: Passwords that are common enough that accepting them is the whole vulnerability.
#: Kept short on purpose: this is a deny-list for a LAN deployment, not a
#: breach corpus, and a list nobody can read is a list nobody will maintain.
COMMON_PASSWORDS: frozenset[str] = frozenset(
    {
        "12345678",
        "123456789",
        "1234567890",
        "87654321",
        "password",
        "password1",
        "password12",
        "password123",
        "passw0rd",
        "p@ssw0rd",
        "p@ssword",
        "qwertyui",
        "qwerty123",
        "qwertyuiop",
        "asdfghjk",
        "iloveyou",
        "letmein1",
        "welcome1",
        "welcome123",
        "admin123",
        "administrator",
        "changeme",
        "changeme1",
        "hospital",
        "hospital1",
        "hospital123",
        "homeopathy",
        "homeopathic",
        "hhms1234",
        "hhmsadmin",
        "doctor123",
        "doctor1234",
        "patient1",
        "patient123",
        "clinic123",
        "reception1",
        "india123",
        "maharashtra",
    }
)


class PasswordPolicyError(ValueError):
    """A password the server refuses.

    Subclasses :class:`ValueError` because that is what a Pydantic validator has
    to raise for the refusal to become a 422 with a readable message instead of a
    500.
    """


def check_password(password: str, username: str | None = None) -> str:
    """Return ``password`` unchanged if the policy accepts it, else raise.

    Args:
        password: The plaintext password supplied at the API boundary.
        username: The account it is being issued for, when known. A password
            equal to its own username is refused; a caller that does not know the
            username yet (a bare schema unit check) may omit it.

    Raises:
        PasswordPolicyError: naming the rule that was broken. The message never
            contains the password.

    Returns:
        The same password, so the caller can use the call inline.
    """

    if not password or not password.strip():
        raise PasswordPolicyError("Password must not be empty.")

    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at most {PASSWORD_MAX_LENGTH} characters."
        )

    lowered = password.lower()

    if lowered in COMMON_PASSWORDS:
        raise PasswordPolicyError(
            "Password is one of the most commonly used passwords; choose another."
        )

    if len(set(password)) == 1:
        raise PasswordPolicyError(
            "Password must not be a single character repeated."
        )

    if username and lowered == username.strip().lower():
        raise PasswordPolicyError("Password must not be the same as the username.")

    return password


__all__ = [
    "COMMON_PASSWORDS",
    "PASSWORD_MAX_LENGTH",
    "PasswordPolicyError",
    "check_password",
]
