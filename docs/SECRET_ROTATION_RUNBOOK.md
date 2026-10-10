# HHMS Secret-Key Rotation Runbook (Batch 115)

This runbook closes the last production-release gate recorded since Batch 107:
the JWT signing secret (`data/secret.key`) must be rotated before public
release, and its handling hardened.

## Why rotation is mandatory

- `data/secret.key` was committed to this repository's git history during the
  early development period (it remains reachable in old commits even though it
  is now ignored). Anyone with repository access can recover that historical
  key and forge valid HS256 access tokens against any deployment that still
  uses it.
- A leaked signing secret compromises **all** authentication: tokens are
  stateless, so a forged token is indistinguishable from a genuine one.
- Therefore no deployment may reuse the historically committed key. Rotation
  is the corrective control; the hardening below is preventive.

## What changed in Batch 115 (preventive hardening)

| Area | Change |
| --- | --- |
| `backend/app/config/settings.py` | `SECRET_KEY` now carries an enforced `min_length=32` validation constraint; trivially short secrets are rejected at model-validation time. |
| `_load_or_create_secret_key()` | Persisted key files are chmod-0600 (owner-only) on POSIX after load/create; keys shorter than 32 chars loaded from disk raise `RuntimeError` pointing at this runbook. |
| `scripts/deploy/rotate-secret-key.ps1` | New operator utility: backs up the current key, generates a fresh 48-byte url-safe secret (same format as the server), writes atomically, tightens Windows ACLs, prints a SHA-256 fingerprint. Supports `-WhatIf`. |
| `scripts/deploy/install-first-run.sh` | Fresh installs already generate a random key with mode 600 — unchanged contract, verified by the Batch 115 QA suite. |
| `.gitignore` | `data/secret.key`, `data/server_id`, and `data/logs/` are ignored going forward (runtime artifacts must never be committed). |

## Rotation procedure (production)

Perform while the server is stopped; clients should be warned in advance
because **every issued token becomes invalid immediately**.

1. Stop the HHMS server service / close `HHMS Server.exe`.
2. Back up and rotate:
   - Windows (installed runtime root):
     `powershell -ExecutionPolicy Bypass -File scripts\deploy\rotate-secret-key.ps1 -RuntimeRoot "<runtime-root>"`
   - Linux/source deployments: stop the server, then either delete
     `data/secret.key` (the server regenerates one with mode 600 on next
     start) or write a fresh value yourself:
     `python -c "import secrets,pathlib;pathlib.Path('data/secret.key').write_text(secrets.token_urlsafe(48));" && chmod 600 data/secret.key`
3. Restart the server. Confirm `GET /api/v1/health` returns 200.
4. Verify old tokens fail: replay a pre-rotation bearer token against any
   protected endpoint; expect HTTP 401.
5. Record the new key fingerprint (printed by the PowerShell utility, or
   `sha256sum data/secret.key | cut -c1-12`) in the operations log. Never
   record the key itself.
6. All users log in again; confirm login + a protected workflow succeed.

## Rotation triggers / schedule

- **Immediately:** before the v1.0 public release (this batch's gate).
- **Immediately:** on any suspected compromise, staff departure with admin
  access, or accidental commit of the key.
- **Routine:** at least every 180 days, aligned with the maintenance
  scheduler window.

## Verification matrix (automated)

`backend/tests/test_batch115_secret_rotation_release_gate_qa.py` covers:
enforced min-length validation, short persisted-key rejection, 0600 file
mode, generated-key entropy/format, rotation-script contract (backup,
atomic write, fingerprint, no plaintext echo), first-run bootstrap, and
git-hygiene guards (secret path ignored, not tracked).
