"""The vendor's side of licensing.

    python -m app.cli.licence keygen --private vendor-private.pem --public vendor-public.pem
    python -m app.cli.licence issue  --private vendor-private.pem --edition hospital \\
                                     --customer "Sunrise Homoeopathy" --months 12 \\
                                     --out licence.key
    python -m app.cli.licence inspect licence.key
    python -m app.cli.licence check   licence.key

Two commands matter. ``keygen`` runs once, on a machine that is not the repository, and
its private key never leaves it. ``issue`` is then a sentence: who, which edition, until
when.

``inspect`` reads a licence without needing the public key, so support can answer "what
did we sell them" from the file alone. ``check`` verifies it the way the software will.

The private key is the whole security of this scheme. If it leaks, every licence ever
issued can be forged, and the only remedy is a new key and a release. The tool says so
on the way out rather than assuming anybody read this docstring.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.editions import EDITIONS


def _keygen(private_out: Path, public_out: Path, *, force: bool = False) -> int:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if private_out.exists() and not force:
        print(f"{private_out} exists. Refusing to overwrite a private key.", file=sys.stderr)
        return 1

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_out.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_out.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    print(f"private key: {private_out}  <- never commit this, never ship it")
    print(f"public key:  {public_out}  <- paste into backend/app/core/licence_keys.py")
    print()
    print("If this private key leaks, every licence you have issued can be forged.")
    print("Keep one copy, offline, and back it up somewhere you would keep a bank draft.")
    return 0


def _issue(args) -> int:
    import jwt

    private_key = Path(args.private).read_text()
    now = datetime.now(UTC)
    months = args.months
    if args.trial and months is None:
        months = 1  # a trial defaults to a month, which is enough to decide

    claims = {
        "edition": args.edition,
        "customer": args.customer,
        "kind": "trial" if args.trial else "paid",
        "iat": int(now.timestamp()),
        "ref": args.reference or f"{args.edition}-{now:%Y%m%d%H%M%S}",
    }
    if months:
        claims["exp"] = int((now + timedelta(days=30 * months)).timestamp())
    if args.machines:
        claims["machines"] = args.machines

    token = jwt.encode(claims, private_key, algorithm="RS256")
    Path(args.out).write_text(token)

    until = f"{(now + timedelta(days=30 * months)):%d %B %Y}" if months else "no expiry"
    label = "trial of" if args.trial else ""
    print(f"issued {label} {args.edition} to {args.customer}, valid until {until}")
    if args.trial:
        print("This is a trial: the full product for the period above, then the grace")
        print("period, then the free edition. Tell them the date.")
    print(f"written to {args.out}")
    print()
    print("Send this file to the customer and tell them to put it at data/licence.key")
    print("on the server, then restart. It is signed, so it does not matter how it")
    print("travels - but it is unique to them, so do not publish it.")
    return 0


def _inspect(path: Path) -> int:
    """Read the claims without verifying - support answering 'what did we sell them'."""

    import jwt

    token = path.read_text().strip()
    claims = jwt.decode(token, options={"verify_signature": False})
    print(json.dumps(claims, indent=2, sort_keys=True))
    print()
    print("Read without verification: this shows what the file claims, not that it is")
    print("genuine. Use `check` for that.")
    return 0


def _check(path: Path) -> int:
    """Verify the way the software will."""

    from app.core.licensing import verify

    try:
        licence = verify(path.read_text().strip())
    except ValueError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(licence.summary(), indent=2, sort_keys=True))
    if licence.expired:
        print()
        print("This licence has expired. The software keeps running for the grace")
        print("period, then falls back to the free edition.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hhms-server licence")
    sub = parser.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen", help="generate the vendor's signing keypair")
    keygen.add_argument("--private", default="vendor-private.pem")
    keygen.add_argument("--public", default="vendor-public.pem")
    keygen.add_argument("--force", action="store_true")

    issue = sub.add_parser("issue", help="sign a licence for a customer")
    issue.add_argument("--private", required=True)
    issue.add_argument("--edition", required=True, choices=sorted(EDITIONS))
    issue.add_argument("--customer", required=True)
    issue.add_argument("--months", type=int, default=None, help="0 for no expiry")
    issue.add_argument(
        "--trial",
        action="store_true",
        help="mark this as a trial; defaults to one month if --months is omitted",
    )
    issue.add_argument(
        "--machines",
        type=int,
        default=None,
        help="how many servers they said they would run (advisory, never enforced)",
    )
    issue.add_argument("--reference", default=None)
    issue.add_argument("--out", default="licence.key")

    inspect = sub.add_parser("inspect", help="read a licence without verifying it")
    inspect.add_argument("path")

    check = sub.add_parser("check", help="verify a licence as the software will")
    check.add_argument("path")

    args = parser.parse_args(argv)

    if args.command == "keygen":
        return _keygen(Path(args.private), Path(args.public), force=args.force)
    if args.command == "issue":
        return _issue(args)
    if args.command == "inspect":
        return _inspect(Path(args.path))
    return _check(Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
