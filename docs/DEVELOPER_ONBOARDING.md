# HHMS Developer Onboarding Guide

Get a new contributor from clone to their first green batch in about an hour.
Read the project constitution first: [`.ai/`](../.ai) — `PROJECT_STATE.md`
(current truth), `IMPLEMENTATION_RULES` / `CODING_RULES` (how we work), and
[CONTRIBUTING.md](../CONTRIBUTING.md).

Related documents: [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md),
[FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md),
[API_SPECIFICATION.md](API_SPECIFICATION.md), [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md),
[TESTING_STRATEGY.md](TESTING_STRATEGY.md), [SERVER_STARTUP.md](SERVER_STARTUP.md).

---

## 1. What HHMS is (30 seconds)

LAN-only Homeopathic Hospital Management System: FastAPI + SQLite (server-owned,
WAL, Alembic-migrated) behind `HHMS-Server.exe` (PyInstaller one-file); HTML/CSS/
vanilla-JS UI hosted in WebView2 by `HHMS-Client.exe`; UDP discovery; RBAC-driven
navigation. No cloud, no internet dependency. Version comes from the root
`VERSION` file only (single-source versioning via `backend/app/release_version.py`).

## 2. Repository map

| Path | Contents |
|------|----------|
| `backend/app/` | FastAPI app: routers (`api/v1/endpoints`), services, models, repositories, middleware (rate limiting), settings |
| `backend/alembic/` | Migration chain (fresh installs bootstrap 0001→head automatically) |
| `backend/tests/` | Pytest suites; shared full-stack harness `_qa_harness.py`; per-batch QA suites `test_batchNNN_*.py` |
| `frontend/` | `index.html` SPA shell, `js/` modules (`rbac.js`, `app.js`, `api.js`, …), CSS |
| `client/HHMS.Client/` | C#/.NET WebView2 launcher (single-file self-contained win-x64 publish; WebView2 SDK pinned 1.0.3856.49) |
| `scripts/deploy/` | `build-server.sh`, `install-first-run.sh`, `server-launch.ps1`, `build-installer.ps1` (Inno→NSIS, `-IncludeClient`) |
| `.github/workflows/release.yml` | CI: test gate → Linux bundle → Windows EXE/installer → checksummed GitHub Release on `v*` tags |
| `docs/` | Specification + per-batch design/QA pages ([INDEX.md](INDEX.md)) |
| `.ai/` | Constitution, decisions, review checklist, PROJECT_STATE.md |
| `data/` | Runtime data (git-ignored): SQLite DB, `secret.key`, uploads, backups, logs |

## 3. Environment setup

Python 3.13+, then:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                       # includes alembic + pinned pytest 8.4.x
cp .env.example .env 2>/dev/null || true              # optional local overrides
uvicorn app.main:app --reload                         # dev server on :8000
curl http://127.0.0.1:8000/api/v1/health              # expect status ok + VERSION string
```

Client-side development needs no build step — edit `frontend/` and refresh. The
WebView2 launcher requires .NET SDK; `dotnet publish -c Release -r win-x64`
produces `HHMS-Client.exe`. Server packaging requires PyInstaller
(`scripts/deploy/build-server.sh`); installer builds require Inno Setup 6 (or
NSIS fallback) on Windows.

## 4. Testing workflow (the contract you must keep green)

```bash
cd backend && pytest tests/            # full suite — currently 478 passed, 2 skipped
```

- The 2 skips are tier-2 opt-in EXE-build tests (`HHMS_RUN_EXE_BUILD=1` runs them).
- Batch QA suites import the shared harness **flat**: `import _qa_harness`
  (there is deliberately no `tests/__init__.py` — do not add package-style imports).
- The harness mounts the real ASGI stack (middleware incl. the login rate limiter
  with a clamped ≥200 budget, auth, services, DB) on in-memory SQLite; file-backed
  release-QA suites simulate the packaged runtime instead.
- Test users needing admin verbs must have a **real seeded active admin role**
  (UserRole→Role join) — raw JWT subjects are rejected by `_require_admin` by design.

## 5. How batches work here

Development proceeds in numbered batches (…108, 109, 110, 111) under the D-008
mega-batching policy. Every batch follows the fixed order in
[docs/INDEX.md](INDEX.md) §Development Workflow: specification → review →
implementation → code review → testing → commit → state update. Closing ritual
(mandatory, part of the batch — not follow-up work):

1. New QA suite `backend/tests/test_batchNNN_*.py` covering the change.
2. Full suite re-run; record exact counts (e.g. "478 passed, 2 skipped").
3. Docs page `docs/CLIENT_BATCHNNN_*.md` + row in `docs/INDEX.md`.
4. Advance `.ai/PROJECT_STATE.md` (Current/Prior milestone + dedicated section),
   `ROADMAP.md` (checkboxes + Current Position), `CHANGELOG.md` (top entry),
   `README.md` (counts + Release Engineering bullets).
5. Repo hygiene check before commit: no `.pyc`/logs/data artifacts staged
   (`.gitignore` covers them; regressions here have happened twice — check
   `git diff --cached --stat`).
6. Commit referencing the batch number.

## 6. Conventions that bite newcomers

- **Naming**: see [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md); DB tables use
  PascalCase names (`Role`, `UserRole`), columns like `role_name`.
- **Auth**: JWT HS256 pinned; reserved claims can't be overridden by callers;
  malformed subject → structured 401 (fail closed), never a 500.
- **Rate limits**: `POST /api/v1/auth/login` is throttled sliding-window per
  client (`LOGIN_RATE_LIMIT_ATTEMPTS`/`WINDOW_SECONDS`); your tests must either
  stay under the harness clamp or reset the limiter.
- **SQLite pools**: `StaticPool` for `:memory:` ONLY; file DBs use QueuePool +
  WAL + busy_timeout (Batch 104 deadlock lesson). Number sequences mint via
  atomic SQL, not loop-bound asyncio locks.
- **Pagination**: repository searches push SQL-level `LIMIT/OFFSET`; API page
  size capped `le=100`, offsets `ge=0`.
- **RBAC front end**: navigation visibility comes only from `GET /auth/me`;
  `ACCESS` vocabulary in `frontend/js/rbac.js` must cover every `data-access`
  key in `index.html` (QA-enforced); denial = hidden + disabled + aria-hidden.
- **Versioning**: never hardcode versions; read `release_version.py` / root
  `VERSION`. Client constants must stay in lock-step.
- **Migrations**: additive chain only; fresh-install bootstrap is QA-tested —
  run the clean-install simulation suite after touching `alembic/`.

## 7. Debugging & tooling pointers

- Server console log + `data/logs/hhms.log`; every response carries
  `X-Process-Time` (perf probes assert on it).
- `/api/v1/health` distinguishes "not our app" vs "our app, broken DB".
- Reproduce client issues in a plain browser against `http://<host>:8000`
  frontend serving or static files — isolates WebView2 from app bugs.
- LAN discovery payloads: UDP `HHMS_DISCOVER_V1` request/response shapes are
  asserted in `tests/test_batch104_multi_client_lan_qa.py`.

## 8. Where to pick up work now

Open Milestone 7 items (see ROADMAP): WebView2 offline redistributable CAB
bundling, cross-module client integration polish, final print/printer hardware
QA, and the production release itself — **gated on rotating `data/secret.key`**,
which persists in git history through Batch 104-era commits. Pick the next
batch number from `.ai/PROJECT_STATE.md` ("Next after …") and follow §5.

## 9. First-week exercise (recommended)

1. Run the full suite locally; find the newest `CLIENT_BATCH*` doc and read it
   beside its test file.
2. Add one parametrized case to the most recent batch's QA suite without
   touching product code; keep everything green.
3. Write the closing ritual (§5) for a tiny documentation fix to learn the
   bookkeeping flow before taking a functional batch.
