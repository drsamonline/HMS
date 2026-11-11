"""
The public key this build verifies licences against.

A licence is a JWT signed with the vendor's private key. This file holds the matching
public key, so a copy of the software can tell a real licence from a written one
without contacting anybody.

**This is the development key.** It must be replaced before the first copy is sold:
run ``python -m app.cli.licence keygen`` once on a machine that is not this repository,
keep the private key somewhere it cannot leak, and paste the public key here. A build
that ships with the development key will accept any licence signed with the
development private key, which is whoever has this repository.

The private key is never committed and never shipped.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

#: PEM-encoded RSA public key. Empty means "this build cannot verify licences", which
#: is a deliberate state for a source checkout rather than a failure.
RELEASE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtdA1vCZUjFf6hpaoOfC2
ddp07VtFFnzouIJCloUqPS/jQSr88yDBe7Eb+55OrGf4DR7fJOTgYqLV9BWnKxk9
bt9eD7Jbo3bKUfEZKrEuxcTrEj3Dm8llF4mOnlA5N6cSYFWh1ViXvHiGVQet5R9r
+C6xdD9huRgiy8afZ3MadtZOyiixWQP02zWjsSHh3pXP2ved4abaZF26dRkJixIu
v8ChTi46Oi7XIG9Mjmc+Bdyxq6Cw5/swknsXzD62X34LTj+fBfpXPGSLxntSpWhI
6qeBXE6KalvuSZ5ueTiDLERQRc/H82qtGvCt3SxqduaZvp/WmaLt6YpX5uhVPqR2
zQIDAQAB
-----END PUBLIC KEY-----"""

#: True while the key above is the development one.
IS_DEVELOPMENT_KEY = "MIIBIjANBgkqhkiG9w0B" in RELEASE_PUBLIC_KEY

__all__ = ["IS_DEVELOPMENT_KEY", "RELEASE_PUBLIC_KEY"]
