"""HHMS first-run administrator bootstrap CLI.

Creates the initial administrator account (and the ``admin`` role) directly in
the configured database so a freshly installed server can be logged into via
``POST /api/v1/auth/login``. The administration user-management API itself
requires an existing admin, so this one-time bootstrap is the entry point for
every clean install.

Usage (source tree)::

    python -m app.cli.create_admin --username admin --full-name "Hospital Administrator"
    # password: interactive prompt, or set env HHMS_ADMIN_INITIAL_PASSWORD

The packaged server binary exposes the same behaviour through a subcommand::

    HHMS-Server create-admin [--username NAME] [--full-name NAME] [--no-change-warning]

Behavior:
  * Refuses to create a second account while any user already exists, unless
    ``--force`` is passed (the bootstrap is for first-run only; day-to-day
    user management happens through the Administration API once an admin
    can log in).
  * Assigns an active role named "admin" (created on demand; permissions are
    managed afterwards through the Administration UI/API).
  * Records ``auth.first_login_pending_for_user_id`` in SystemSetting so the
    web client can prompt a mandatory password change on the first login.
  * Prints a mandatory password-change warning unless ``--no-change-warning``.

Exit codes: 0 success, 1 invalid input/confirmation, 2 unexpected error.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from getpass import getpass

from sqlalchemy import func, select

MIN_PASSWORD_LENGTH = 8

# Built-in default for evaluation/test installs: if no password is supplied
# (flag or HHMS_ADMIN_INITIAL_PASSWORD env var), the bootstrap uses this so a
# fresh build can be logged into immediately with admin/admin. A loud warning
# is printed; change it before production use.
DEFAULT_BOOTSTRAP_PASSWORD = "admin"


def _parser(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hhms create-admin",
        description="Create the initial HHMS administrator account.",
    )
    parser.add_argument("--username", default=os.environ.get("HHMS_ADMIN_USERNAME", "admin"))
    parser.add_argument("--full-name", default=os.environ.get("HHMS_ADMIN_FULL_NAME", "Hospital Administrator"))
    parser.add_argument("--email", default=os.environ.get("HHMS_ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.environ.get("HHMS_ADMIN_INITIAL_PASSWORD"),
                       help="Initial password. If omitted, the built-in default 'admin' "
                            "is used so a fresh build can be tested immediately.")
    parser.add_argument("--no-change-warning", action="store_true",
                        help="Skip the mandatory password-change warning output.")
    parser.add_argument("--force", action="store_true",
                        help="Allow creating additional users even when accounts already exist.")
    parser.add_argument("--prompt", action="store_true",
                        help="Interactively prompt for the password instead of using the default 'admin'.")
    parser.add_argument("--confirm", action="store_true",
                        help="(deprecated, no-op) kept for backwards compatibility; the default "
                             "password 'admin' is now used automatically when none is supplied.")
    return parser.parse_args(argv)


FIRST_LOGIN_SETTING_KEY = "auth.first_login_pending_for_user_id"


async def _create(args: argparse.Namespace, password: str) -> int:
    # Imported lazily so `--help` stays fast and dependency-free.
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.system_setting import SystemSetting
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()
    async with factory() as db:
        existing = await db.scalar(select(User).where(User.username == args.username.strip()))
        if existing is not None:
            print(f"User '{existing.username}' already exists (id={existing.id}); nothing to do.")
            return 0

        user_count = await db.scalar(select(func.count()).select_from(User))
        if user_count and not args.force:
            print("error: users already exist in this database; the first-run bootstrap "
                  "refuses to add more. Use the Administration API (or --force).", file=sys.stderr)
            return 1

        user = User(
            username=args.username.strip(),
            password_hash=hash_password(password),
            full_name=args.full_name.strip(),
            email=(args.email.strip() if args.email else None),
            designation="Administrator",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        role = await db.scalar(select(Role).where(func.lower(Role.role_name) == "admin"))
        if role is None:
            role = Role(role_name="admin", description="System administrator", is_active=True)
            db.add(role)
            await db.flush()

        db.add(UserRole(user_id=user.id, role_id=role.id))

        # Flag for the client: force a password change on first login.
        setting = await db.scalar(select(SystemSetting).where(SystemSetting.setting_key == FIRST_LOGIN_SETTING_KEY))
        if setting is None:
            db.add(SystemSetting(
                setting_key=FIRST_LOGIN_SETTING_KEY,
                setting_value=str(user.id),
                setting_type="int",
                description="User id that must change their password on first login.",
                is_editable=True,
            ))
        else:
            setting.setting_value = str(user.id)

        await db.commit()

        print(f"Administrator created: username='{user.username}' id={user.id} role='{role.role_name}'.")
        if not args.no_change_warning:
            print("WARNING: change this password immediately after the first successful login.")
        return 0


def ensure_default_admin() -> int:
    """Idempotently create the default ``admin``/``admin`` account at startup.

    Called by the server after migrations so a freshly installed build can be
    logged into immediately (username ``admin``, password ``admin``) without
    any manual CLI step. Safe on every boot: does nothing when at least one
    user already exists, and never overwrites an existing admin's password.
    Opt out with ``HHMS_BOOTSTRAP_DEFAULT_ADMIN=false``. Returns the total
    number of users afterwards.
    """
    import asyncio
    import os

    if os.environ.get("HHMS_BOOTSTRAP_DEFAULT_ADMIN", "").strip().lower() in {"false", "0", "no"}:
        return 0

    from sqlalchemy import func, select

    from app.db.session import get_session_factory
    from app.models.user import User

    async def _count_users() -> int:
        factory = get_session_factory()
        async with factory() as db:
            return await db.scalar(select(func.count()).select_from(User)) or 0

    count = asyncio.run(_count_users())
    if count:
        return count
    main([])
    return asyncio.run(_count_users())


def main(argv: list[str] | None = None) -> int:
    args = _parser(argv)
    username = args.username.strip()
    if not username:
        print("error: --username must not be empty", file=sys.stderr)
        return 1
    if not args.full_name.strip():
        print("error: --full-name must not be empty", file=sys.stderr)
        return 1

    password = args.password
    used_default = False
    if password is None:
        # No flag/env supplied: fall back to the built-in default 'admin' so a
        # freshly downloaded build can be tested immediately. Interactive
        # prompting remains available via --prompt (kept for scripted/CLI use).
        if args.prompt:
            try:
                password = getpass(f"Password for '{username}' (min {MIN_PASSWORD_LENGTH} chars): ")
                confirm = getpass("Repeat password: ")
            except EOFError:
                print("error: cannot prompt for password in a non-interactive terminal; "
                      "set HHMS_ADMIN_INITIAL_PASSWORD or pass --password", file=sys.stderr)
                return 1
            if password != confirm:
                print("error: passwords do not match", file=sys.stderr)
                return 1
        else:
            password = DEFAULT_BOOTSTRAP_PASSWORD
            used_default = True

    if len(password) < MIN_PASSWORD_LENGTH and not used_default:
        print(f"error: password must be at least {MIN_PASSWORD_LENGTH} characters", file=sys.stderr)
        return 1

    try:
        rc = asyncio.run(_create(args, password))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"error: failed to create administrator: {exc}", file=sys.stderr)
        return 2
    if used_default and rc == 0:
        print("")
        print("=" * 64)
        print(f"  DEFAULT LOGIN ACTIVE:  username='{username}'  password='{DEFAULT_BOOTSTRAP_PASSWORD}'")
        print("  This build uses a well-known default password intended for")
        print("  testing only. Change it before exposing this server on any")
        print("  network or using it with real patient data.")
        print("=" * 64)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
