# Batch 111 — Documentation & Training Finalization (Milestone 7 part 7)

Closes the two open Milestone 7 documentation items — "Documentation
finalization" and "User training materials" — by shipping the three audience
guides that take HHMS from a built system to a deployable, trainable product:

| Guide | Audience | Scope |
|-------|----------|-------|
| [USER_GUIDE.md](../USER_GUIDE.md) | End users (reception, clinicians, ward, pharmacy, lab, billing, stores, records staff) | Starting the client, sign-in/lockout behavior, role-driven navigation map, core daily workflows (registration → OPD token → case/prescription → IPD → billing → reports/printing), data-entry conventions, client-side troubleshooting table, do-not list |
| [ADMIN_TRAINING.md](../ADMIN_TRAINING.md) | Clinic administrator / IT owner | Architecture ownership summary, server + client installation (incl. WebView2 runtime prerequisite handling), day-1 configuration checklist, users/roles/RBAC management, daily operations, backup policy via the Backups workspace, quarterly restore/disaster drill, escalation matrix, security hygiene incl. secret-key rotation gate |
| [DEVELOPER_ONBOARDING.md](../DEVELOPER_ONBOARDING.md) | New contributors | Repo map, environment setup, testing contract (flat `import _qa_harness`, harness rate-limiter clamp, real seeded admin roles), the mandatory batch closing ritual, gotcha list of QA-enforced conventions (SQLite pools, pagination bounds, RBAC vocabulary, single-source versioning, additive migrations), debugging pointers, first-week exercise |

## Grounding discipline

Every factual claim in the guides was verified against the repository before
writing — no invented UI or behavior:

- Rate-limiter defaults (10/min per client, `LOGIN_RATE_LIMIT_ATTEMPTS` /
  `LOGIN_RATE_LIMIT_WINDOW_SECONDS`) — `app/middleware/rate_limit.py`, `app/config/settings.py` (Batch 109).
- Blanket-access roles (`admin`, `administrator`, `hospital administrator`,
  `super administrator`), the `ACCESS` module vocabulary, deny-by-default and
  hidden/disabled/aria-hidden denial triple — `frontend/js/rbac.js` +
  `frontend/index.html` (Batch 110); the guide's module table covers exactly the
  14 `data-access` nav keys present in the shell.
- Backup verbs, pre-restore safety snapshot, corrupt-upload rejection, admin
  gating — maintenance endpoints verified end-to-end in Batch 108.
- Installer layout (`HHMS-Setup-<version>.exe`, no-admin user-writable install,
  data survival on uninstall, `-IncludeClient`) — `scripts/deploy/build-installer.ps1` (Batches 107–108).
- UDP discovery `HHMS_DISCOVER_V1`, `/api/v1/health` VERSION handshake,
  `X-Process-Time`, single-source `VERSION` file — Batches 104–106 artifacts.
- Test counts quoted (478 passed, 2 skipped; tier-2 `HHMS_RUN_EXE_BUILD=1`) —
  current suite state at close of Batch 110.
- All cross-document links resolve to files that exist in `docs/` or repo root
  (checked programmatically; one dangling `DEVELOPMENT_ENVIRONMENT.md` reference
  caught and replaced with `SERVER_STARTUP.md` during review).

## Bookkeeping

- Three rows added to `docs/INDEX.md` after the Batch 110 entry; catalogue count
  117 → 121; Recommended Reading Order gained end-user, administrator, and
  new-contributor pointers.
- `.ai/PROJECT_STATE.md`, `ROADMAP.md` (Milestones 3–5 doc item, Milestone 7
  lines, Current Position), `CHANGELOG.md`, and `README.md` advanced to Batch 111.

## Verification

Documentation-only batch: no product code touched, so the backend suite is
expected to stay at **478 passed, 2 skipped** (re-run confirmed at close).

## Remaining Milestone 7 scope

WebView2 offline redistributable CAB bundling, cross-module client integration
polish, final print/printer hardware QA on target hardware, prescription-template
final QA, report scheduling, seed-data final pass, and production release — the
latter gated on rotating `data/secret.key` (persists in git history through
Batch 104-era commits).
