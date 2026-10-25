# HHMS 0.0.2 — release notes

**2026-10-25**

## What changed

- **Licence.** The repository carries its own EULA — *HHMS — Homeopathic Hospital Management
  System, PROPRIETARY SOFTWARE LICENSE AGREEMENT*, Version 1.0, effective 12 October 2026,
  Copyright (c) 2026 Dr. Sohil Momin, Vadodara, Gujarat, India. All rights reserved.
  It is deliberately NOT the PolyForm Noncommercial licence the open apps use, and it is
  recorded in `registry/licence-policy.json` so no sweep ever normalises it.
- **Version.** This is the first versioned release. The repository had no `VERSION` file, so
  the licence and the work had nothing to be released under.

## What this is, and is not

HHMS is a **LAN-based hospital management system** for homeopathic hospitals and clinics:
the database is server-owned and local, and there is no internet dependency. It is
**proprietary software under active development** — not an open app, and it is not
published as one:

- **no public demo** — there is no `docs/play/`, so the build's demo guard does not apply
  and no preview of the system is published;
- **no app-pipeline release** — it uses its own `release.yml`, not `build-apps.yml`, so it
  is not swept into the open apps' rolling `app-latest` releases;
- **its licence is skipped by the enforcer** — `registry/licence-policy.json` lists it as a
  deliberate licence, and the licence tool reads that policy before it touches anything.

## Why this file exists separately

`CHANGELOG.md` in this repository is 114 KB. Rewriting it in one API commit failed twice with
an HTML error — the payload was too large. A dated release note is the honest answer for a
product anyway: the changelog keeps the full history, and each release has its own page.
