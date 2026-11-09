"""HHMS configuration CLI.

The same catalogue and the same precedence as the interface, for the two jobs a
browser is bad at: reading the effective configuration of a server you cannot log
into, and provisioning a second installation from the first.

Usage (source tree)::

    python -m app.cli.config get [KEY ...]
    python -m app.cli.config set KEY VALUE [KEY VALUE ...]
    python -m app.cli.config reset KEY
    python -m app.cli.config export --file settings.json
    python -m app.cli.config import --file settings.json

``get`` with no keys prints every setting, its value and where the value came
from. Secrets are printed as ``********`` unless ``--reveal`` is passed, which
exists for the one case that needs it: moving a signing key between servers.

Exit codes: 0 success, 1 invalid input or a refused value, 2 unexpected error.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.core.settings_catalogue import BY_KEY, GROUPS, in_group
from app.db.session import get_session_factory
from app.services import settings_store


def _parse(raw: str):
    """Read a CLI value as JSON when it looks like one, otherwise as text."""

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


async def _get(keys: list[str], reveal: bool) -> int:
    factory = get_session_factory()
    async with factory() as db:
        if keys:
            for key in keys:
                try:
                    result = await settings_store.effective(db, key)
                except ResourceNotFoundException as exc:
                    print(f"{key}: {exc}", file=sys.stderr)
                    return 1
                _print(result, reveal)
            return 0

        effective = await settings_store.effective_all(db)
        for group in GROUPS:
            print(f"\n[{group}]")
            for spec in in_group(group):
                _print(effective[spec.key], reveal)
        return 0


def _print(result, reveal: bool) -> None:
    value = result.value
    if result.spec.type == "secret" and value and not reveal:
        value = "********"
    print(f"{result.spec.key:<32} {value!r:<28} ({result.source})")


async def _set(pairs: list[str]) -> int:
    if len(pairs) % 2:
        print("set needs KEY VALUE pairs", file=sys.stderr)
        return 1

    factory = get_session_factory()
    async with factory() as db:
        # Validate everything first, for the same reason the API does.
        for index in range(0, len(pairs), 2):
            try:
                await settings_store.validate(db, pairs[index], _parse(pairs[index + 1]))
            except (BusinessRuleException, ResourceNotFoundException) as exc:
                print(f"refused: {exc}", file=sys.stderr)
                return 1

        for index in range(0, len(pairs), 2):
            result = await settings_store.set_value(
                db, pairs[index], _parse(pairs[index + 1])
            )
            _print(result, reveal=False)
        await db.commit()
    return 0


async def _reset(key: str) -> int:
    factory = get_session_factory()
    async with factory() as db:
        try:
            result = await settings_store.reset_value(db, key)
        except ResourceNotFoundException as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 1
        await db.commit()
        _print(result, reveal=False)
    return 0


async def _export(path: Path) -> int:
    factory = get_session_factory()
    async with factory() as db:
        effective = await settings_store.effective_all(db)
        payload = {
            "schema": 1,
            "values": {
                key: result.value
                for key, result in effective.items()
                if result.source == "database"
            },
        }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {len(payload['values'])} settings to {path}")
    return 0


async def _import(path: Path) -> int:
    if not path.is_file():
        print(f"no such file: {path}", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("values", payload)

    factory = get_session_factory()
    async with factory() as db:
        for key, value in values.items():
            try:
                await settings_store.validate(db, key, value)
            except (BusinessRuleException, ResourceNotFoundException) as exc:
                print(f"refused: {exc}", file=sys.stderr)
                return 1
        for key, value in values.items():
            await settings_store.set_value(db, key, value)
        await db.commit()
    print(f"applied {len(values)} settings from {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hhms-server config")
    sub = parser.add_subparsers(dest="command", required=True)

    get = sub.add_parser("get", help="print settings and where each value came from")
    get.add_argument("keys", nargs="*")
    get.add_argument("--reveal", action="store_true", help="print secret values")

    set_ = sub.add_parser("set", help="set KEY VALUE pairs")
    set_.add_argument("pairs", nargs="+")

    reset = sub.add_parser("reset", help="remove an override")
    reset.add_argument("key")

    export = sub.add_parser("export", help="write the overrides to a file")
    export.add_argument("--file", default="hhms-settings.json")

    imp = sub.add_parser("import", help="apply a file of overrides")
    imp.add_argument("--file", required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "get":
            return asyncio.run(_get(args.keys, args.reveal))
        if args.command == "set":
            return asyncio.run(_set(args.pairs))
        if args.command == "reset":
            return asyncio.run(_reset(args.key))
        if args.command == "export":
            return asyncio.run(_export(Path(args.file)))
        if args.command == "import":
            return asyncio.run(_import(Path(args.file)))
    except Exception as exc:  # noqa: BLE001 - the CLI must not traceback at a user
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
