"""Headless setup.

The wizard exists so a hospital administrator can configure the system from a
browser. This exists for the case the browser cannot serve: a server being built by
a script, a machine with no screen, or an operator who would rather type four flags
than click ten steps.

It runs the same service functions the wizard does, in the same order, so the two
cannot drift: there is one implementation of "create the first administrator" and
this is a caller of it.

Usage::

    python -m app.cli.setup \\
        --hospital-name "Anand Homoeopathy Hospital" \\
        --admin-username dr.momin --admin-full-name "Dr Sohil Momin" \\
        --admin-password-env HHMS_ADMIN_PASSWORD \\
        --modules pharmacy,ipd,billing

Exit codes: 0 success, 1 refused, 2 unexpected error.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from app.core.exceptions import BusinessRuleException
from app.db.session import get_session_factory
from app.modules.registry import BY_CODE
from app.services import module_state, settings_store, setup, setup_steps


async def _run(args: argparse.Namespace) -> int:
    password = os.environ.get(args.admin_password_env, "")
    if not password:
        print(
            f"set {args.admin_password_env} to the administrator password; it is "
            "not taken on the command line, where it would land in shell history",
            file=sys.stderr,
        )
        return 1

    factory = get_session_factory()

    async with factory() as db:
        if await setup.is_complete(db):
            print("This installation is already set up.", file=sys.stderr)
            return 1

        steps: list[tuple[str, dict]] = [
            ("identity", {"HOSPITAL_NAME": args.hospital_name}),
            (
                "people",
                {
                    "username": args.admin_username,
                    "password": password,
                    "full_name": args.admin_full_name,
                },
            ),
        ]

        if args.modules:
            wanted = [code.strip() for code in args.modules.split(",") if code.strip()]
            unknown = [code for code in wanted if code not in BY_CODE]
            if unknown:
                print(f"unknown modules: {', '.join(unknown)}", file=sys.stderr)
                return 1
            steps.append(("modules", {"modules": wanted}))

        for step, values in steps:
            handler = setup_steps.HANDLERS.get(step)
            try:
                if handler is not None:
                    outcome = await handler(db, values)
                else:
                    for key, value in values.items():
                        await settings_store.validate(db, key, value)
                    for key, value in values.items():
                        await settings_store.set_value(db, key, value)
                    outcome = {}
                await setup.mark_step(db, step)
                await db.commit()
            except BusinessRuleException as exc:
                await db.rollback()
                print(f"{step}: {exc}", file=sys.stderr)
                return 1
            print(f"{step}: ok {outcome if outcome else ''}".rstrip())

        try:
            await setup.complete(db)
        except BusinessRuleException as exc:
            print(f"finish: {exc}", file=sys.stderr)
            return 1
        await db.commit()

        modules = sorted(await module_state.enabled_codes(db))

    print(f"setup complete; modules: {', '.join(modules)}")
    print(f"sign in as {args.admin_username}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hhms-server setup")
    parser.add_argument("--hospital-name", required=True)
    parser.add_argument("--admin-username", required=True)
    parser.add_argument("--admin-full-name", required=True)
    parser.add_argument(
        "--admin-password-env",
        default="HHMS_ADMIN_PASSWORD",
        help="name of the environment variable holding the password",
    )
    parser.add_argument(
        "--modules",
        default="",
        help="comma-separated module codes to enable, e.g. pharmacy,ipd,billing",
    )
    args = parser.parse_args(argv)

    try:
        return asyncio.run(_run(args))
    except Exception as exc:  # noqa: BLE001 - a CLI must not traceback at an operator
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
