# Security Policy

This document states what HHMS does today. It is written to be checked against
the code: every claim below is implemented in the release it describes, and
anything not yet built is listed under **Not yet built** rather than described
as if it were.

The full technical design lives in
[docs/SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md), which is the
target; this file is the present.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.0.x   | Yes       |

## Reporting a Vulnerability

1. **Do not** disclose the vulnerability publicly.
2. Open a private security advisory on this repository, or email the maintainer.
3. Include a description, reproduction steps, potential impact, and a suggested
   fix if you have one.

### Response Timeline

| Stage | Target |
|-------|--------|
| Acknowledge | 48 hours |
| Assess initial impact | 7 days |
| Fix critical issues | 30 days |

## What HHMS does today

### Authentication

- Passwords are hashed with Argon2 through `pwdlib`.
- Access tokens are HS256 JWTs with a 30-minute default lifetime.
- The signing secret is generated at 48 bytes of URL-safe randomness on first
  boot, persisted to `data/secret.key` with owner-only permissions, and rejected
  at startup if shorter than 32 characters.
- The JWT algorithm is pinned and reserved claims cannot be overridden by a
  caller; both are covered by tests.
- Login is throttled by a sliding-window limiter mounted as the outermost
  middleware, so an over-budget attempt is refused before any password work
  happens.

### Transport and headers

- Every response carries `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Content-Security-Policy`, `Permissions-Policy` and
  `Cross-Origin-Opener-Policy`.
- The content policy permits inline script and style because the current GUI
  renders inline blocks. It is not a nonce-based policy yet.

### Authorisation

- Roles, permissions and role-permission assignment are modelled and
  administered through the API.
- The client hides navigation a user cannot use, and fails closed: an account
  with no permission codes sees no module.

### Data integrity

- SQLite connections set `PRAGMA foreign_keys=ON`, so the relationships declared
  in the models are enforced rather than merely documented.
- Numbered documents (invoices, receipts, cases, admissions) come from locked
  sequences, and receipt continuity is audited from live data rather than from
  stored counters.
- A fully paid invoice cannot be modified, a cancelled invoice cannot be
  modified, a refund cannot exceed the amount collected, and there is no delete
  endpoint for a payment.

### Logging

- Request logs record path, status code, request id and duration. They do not
  record request bodies, query strings containing identifiers, or any patient
  data.
- Unhandled exceptions are logged with a traceback server-side and returned to
  the client as a generic message.

### Deployment boundary

- The SQLite database is server-owned. Clients never open it; they speak
  HTTP/JSON over the hospital LAN.
- The server binds to the LAN and does not require internet access.

## Not yet built

These are known gaps, not oversights. Each is scheduled in the build plan and
this section is deleted as each one lands.

| Gap | Effect today | Planned |
|-----|--------------|---------|
| Server-side permission enforcement | Every authenticated user can call every endpoint, including administration and backup restore | Build plan B12-B15 |
| Audit trail writes | The `AuditLog` table and its read API exist; no write path records an action | B07-B11 |
| Encryption at rest | The database file and its backups are plaintext | Not scheduled |
| Encryption in transit | HTTP on the LAN; no TLS listener and no reverse-proxy guidance | Not scheduled |
| Server-side password policy | Only the client enforces a minimum length | B24 |
| Session revocation | Stateless JWT with no denylist; logout is client-side | Not scheduled |
| Field-level access control | Any authenticated user can read any patient's full record | B12-B15 |
| Dependency vulnerability scanning | Dependabot covers GitHub Actions only; no pip audit and no SAST in CI | Not scheduled |
| Multi-factor authentication | Not supported | Not scheduled |

## Best Practices for Administrators

- Change the default administrator password on first login, and disable the
  bootstrap account with `HHMS_BOOTSTRAP_DEFAULT_ADMIN=false` once a named
  administrator exists.
- Set `HHMS_SEED_DEMO_DATA=false` on any installation holding real patient data.
- Keep the server on the hospital LAN only. Do not expose the port to the
  internet.
- Run verified backups on a schedule and test a restore.
- Restrict physical and network access to the server machine: today the
  database file is the security boundary.

## Best Practices for Developers

- Never commit secrets. `data/secret.key`, `.env` and `data/` stay out of version
  control.
- Never bypass authentication or authorisation in a route, including in tests
  that call the service layer directly.
- Validate every input against [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).
- Keep dependencies current and keep GitHub Actions pinned to commit SHAs.
