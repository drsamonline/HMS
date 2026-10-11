# Demo Data & Docs Cleanup — Resumable Session Log

**Purpose:** single authoritative document for the "fill project with 2025 testing data + update documents/remove clutter" task.
**Protocol (mandatory, every run):**
1. Read this file FIRST. Resume from the first unchecked item under **Next actions**.
2. Update **Progress ledger** and **Findings** as work happens — append, never delete history.
3. When a problem is fixed, move it from *Open problems* to *Fixed problems* with commit reference + verification evidence.
4. Before ending a run: check off completed items, record exact commands + results, `git add`/commit this file together with code changes.
5. All paths relative to `/workspace`. Baseline suite: **546 passed, 2 skipped** (opt-in EXE-build tier-2 skips).

---

## Task statement (user)
- Fill the project with testing data of year **2025** so it can be used directly (out-of-the-box populated DB).
- Update documents; remove clutter — excessive README explanations of coding batches etc.
- Keep all findings in this one document; each run updates it; fixes are recorded so data remains resumable.

## Status: IN PROGRESS

## Progress ledger
| # | Step | State | Evidence |
|---|------|-------|----------|
| 1 | Explore repo/runtime layout | ✅ DONE | see Findings F1–F7 |
| 2 | Confirm prescription route bug | ✅ DONE | F8 verified in source |
| 3 | Create this session log | ✅ DONE (this run) | file exists at `.ai/DEMO_DATA_SESSION.md` |
| 4 | Fix POST /prescriptions kwarg bug | ✅ DONE | Patch applied in `endpoints/prescriptions.py` (`prescription_in=` → `data=`); see Fixed OP-1 |
| 5 | Write `backend/app/cli/seed_demo_data.py` (idempotent, 2025 dataset) | ✅ DONE | seeds 40 patients/120 visits/…; marker-based idempotency |
| 6 | Startup integration + GUI-first OOBE | ✅ DONE | auto-seed on first run (no commands); `seed-demo-data` subcommand; opt-out `HHMS_SEED_DEMO_DATA=false` |
| 7 | Execute seed against `data/hhms.sqlite3`; verify counts via API | ✅ DONE | repo DB seeded; login+patients list verified over HTTP |
| 8 | Docs cleanup: rewrite README (no batch narration), trim ROADMAP/CHANGELOG noise, move batch docs → `docs/history/`, update `docs/INDEX.md` | ✅ DONE | README 225→139 lines; ROADMAP 241→95; docs/DEMO_DATA.md added |
| 9 | Regression: full backend suite ≥546 pass; hygiene pre-commit check | ✅ DONE | 546 passed, 2 skipped (fixed stale 0028→0029 head assertions in test_batch104) |
| 10 | Commit + close-out entry in this file | ⬜ TODO | — |

## Next actions (resume here)
1. ~~Apply F8 patch~~ DONE.
2. Implement seeder per Plan P1; test on an EPHEMERAL copy first (`HHMS_APPLICATION_ROOT=/tmp/hhms-seedtest`), then against real `data/` root.
3. Wire startup flag per Plan P2.
4. Seed production DB per Plan P3; record row counts table below.
5. Docs cleanup per Plan P4.
6. Full test suite + hygiene + commit per Plan P5. Append results.

## Findings (verified facts)
- **F1 Runtime paths.** DB path `data/hhms.sqlite3` resolved by `app/config/runtime_paths.py`; env override `HHMS_APPLICATION_ROOT`. No DB file currently shipped (fresh-install state). Migrations applied at startup via `prepare_runtime()` (Alembic 0001→head ~0028).
- **F2 Admin bootstrap.** `app/server.py::run()` → `ensure_default_admin()` seeds `admin/admin`, no-ops once any user exists. CLI analog: `backend/app/cli/create_admin.py`.
- **F3 Number sequences.** Seeded by migration `0010_hospital_system_settings.py` (patient_number, visit_number, admission_number, invoice_number, opd_token); services mint case/prescription/receipt/investigation/discharge numbers. Missing-sequence pattern: `backend/tests/_qa_harness.py::seed_number_sequence`.
- **F4 Auth.** JWT via `POST /api/v1/auth/login` (admin/admin). Billing casts JWT `sub` to int → seeded users must have numeric ids (real DB users do). Login rate limiter clamped ≥200 in harness; seeding via HTTP must stay within budget or use service layer.
- **F5 Routes/schemas needed for 2025 dataset** (all under `/api/v1`): patients (`PatientCreate`), visits (`VisitCreate`, tz-aware datetimes), opd tokens, cases, prescriptions (+items w/ medicine ids), medicines + batches, stock batches, dispenses, investigations + results, invoices (`InvoiceCreate`: patient+visit+total_amount), invoice items, payments (`PaymentCreate`), beds (`BedCreate`), admissions, discharges.
- **F6 QA harness proof.** `backend/tests/_qa_harness.py` runs full ASGI stack incl. print envelopes over real routes — reference flows for the seeder.
- **F7 .ai conventions.** Repo keeps `CODING_RULES.md`, `DECISIONS.md`, `PROJECT_STATE.md` etc. in `.ai/` — session log lives there.
- **F8 REAL PATH CORRECTION (supersedes earlier claim).** Prescription endpoint lives at `backend/app/api/v1/endpoints/prescriptions.py` (**not** `routes/prescriptions.py`). Verified this run: create route calls `prescription_service.create(db, prescription_in=...)` while service signature is `create(self, db, data: PrescriptionCreate)` → kwarg mismatch `TypeError` on every HTTP POST /prescriptions (confirms prior-run bug claim, now with exact location + patch). Service handles items internally (`for item_data in data.items:` at line ~145), so single-kwarg fix suffices. Same check needed for other endpoints' service calls during seeder work.
- **F9 Prior-session summary claims** (from conversation, not re-verified this run): 546-test baseline clean; two non-code open items (printer QA field checklist, release tag push). Treat as context only until re-checked.

## Open problems
- ~~OP-1~~ → moved to Fixed.
- **OP-2** Not yet determined whether seeder should use HTTP routes or service layer directly. Decision leaning: **service layer** inside one async session (avoids rate limiter, auth churn, HTTP overhead; still exercises integrity rules). Re-evaluate if service signatures prove awkward.

## Fixed problems
- **OP-1 POST /prescriptions kwarg TypeError** (F8). Patched `backend/app/api/v1/endpoints/prescriptions.py` create route: `prescription_service.create(db, prescription_in=prescription_in)` → `create(db, data=prescription_in)`, matching service signature `create(self, db, data: PrescriptionCreate)` (`app/services/prescription.py:105`). Verification: full backend suite run after patch (see Run log); update route at line ~139 checked — it calls the service with correct kwargs already.

## Plan
- **P1 Seeder** `backend/app/cli/seed_demo_data.py`: idempotent (guard table/marker row `demo_seed_meta` or settings key + year tag), async, service-layer. Dataset: admin + clinicians (doctor/pharma/billing), hospital settings/departments/designations/services, ~25 medicines + batches/stock (expiry in 2025/2026), beds across wards, suppliers; ~40 patients registered Jan–Dec 2025; ~120 visits w/ OPD tokens, case records, prescriptions, dispenses, investigations+results; 6–8 IPD admissions w/ notes + discharges; invoices/payments (~70% paid, some outstanding, 1 refund) all dated 2025. Standalone command `python -m app.cli.seed_demo_data [--year 2025] [--reset]`.
- **P2 Startup**: in `server.py::run()` after `ensure_default_admin()`, call seeder when env `HHMS_SEED_DEMO_DATA=true` (default OFF so tests/CI unaffected).
- **P3 Populate**: run seeder against repo `data/` root; ship? — decide: sqlite files are gitignored, so "directly usable" = one-command seed documented in README + auto-flag; ALSO generate `data/hhms.sqlite3` locally so user can run immediately. Verify counts via GET endpoints.
- **P4 Docs**: README rewritten without Batch NN narration (keep features/install/usage/seed instructions); ROADMAP condensed; CHANGELOG kept but README/docs stop referencing batches; remaining per-batch `docs/CLIENT_*.md` moved to `docs/history/`; `docs/INDEX.md` updated; add short `docs/DEMO_DATA.md`.
- **P5 Verification**: `pytest backend/tests` ≥546 pass/2 skip; staged-tree hygiene check (no .pyc/logs/secrets); commit.

## Seed results (fill during P3)
_(empty)_

## Run log
- **Run 2026-10-10 (earlier):** Re-established ground truth: repo clean at commit 6729552 (Batch 119 cont., tag build-6729552…), baseline suite known 546/2. Created this resumable session log consolidating all prior-run findings (F1–F9). No product code changed yet. Tool-quota ended run before applying OP-1 fix.
- **Run 2026-10-10 #3:** Applied OP-1 fix (`endpoints/prescriptions.py`: `prescription_in=` → `data=` in create route service call). Verified: full backend suite **546 passed, 2 skipped** post-patch (baseline preserved). Ledger step 4 ✅; OP-1 moved to Fixed problems. Next: seeder (Plan P1).

## Run log — 2026-10-11 #A (GUI-first OOBE)
- **F10 Pristine-check bug FIXED (OP-3).** `seed_demo_on_first_run()` used a fragile `NumberSequence` row-count heuristic (>5 ⇒ not pristine) that failed because migrations legitimately ship more than five bootstrap sequences on current head. Replaced with exact detection: demo marker setting `demo_seed.year.<YEAR>` short-circuits re-seeding; sequence count is no longer consulted. Verified on ephemeral root `/tmp/hhms-firstrun`: first call seeds (True), second call no-ops (False).
- **Full boot verification.** Real server start (`python -m app.server`, fresh `HHMS_APPLICATION_ROOT=/tmp/hhms-boot2`) auto-seeded 2025 demo data with zero user commands; admin/admin login returned a JWT and the patients endpoint served seeded records. GUI-only OOBE achieved: unzip build → double-click/run server → dashboard populated.
- **Portability note.** `data/*.sqlite3` remains gitignored (runtime artifacts). Portability is delivered by the deterministic first-run auto-seed rather than shipping a binary DB; users who want a literal pre-built file can copy their local `data/hhms.sqlite3`.
- Ledger updated (steps 5–8 ✅, step 9 in progress). Next: full regression suite + commit.

## Fixed problems (append when resolved)
- **OP-3 First-run auto-seed never fired** (see F10). Patched `app/cli/seed_demo_data.py::seed_demo_on_first_run._is_pristine` (marker-based detection; dropped seq-count heuristic). Verification: ephemeral-root double-call test + real server boot with HTTP login/patients check (this run's log).

- **Run 2026-10-11 #B:** Full suite green: **546 passed, 2 skipped**. Repaired three stale migration-head assertions (`0028_prescription_operational_year_lifecycle` → `0029_department_service_is_active`) in `tests/test_batch104_clean_install_simulation.py`. Ledger step 9 ✅.

## Run log — 2026-10-11 #C (auto-release build failure)
- **OP-4 CI smoke test blind to OOBE regressions.** Auto-build release failed because `release.yml` gates the Linux/Windows bundles on `HHMS-Server --smoke-test`, which previously only probed `/health` — first-run bootstrap/seeding errors shipped silently and broke builds. Fixed by making `_smoke_test()` mirror the real `run()` path: `prepare_runtime()` → `ensure_default_admin()` → `seed_demo_on_first_run()` before the health probe; `create_admin.py` CLI now also calls `prepare_runtime()` so it works standalone on fresh installs.
- Verification (this run): full backend suite **546 passed, 2 skipped**; clean ephemeral root (`/tmp/hhms-smoke`) `python -m app.server --smoke-test` → migrations 0001→0029 applied, default admin created, 2025 demo data auto-seeded (40 patients / 120 visits / 120 prescriptions / 241 dispenses / 40 investigations / 8 admissions / 128 invoices / 118 payments), `smoke-test ok: health 0.0.1`, exit 0. Same command is what CI runs for both platform bundles, so a broken OOBE now fails the build instead of shipping.
- Changed files staged: `backend/app/server.py`, `backend/app/cli/create_admin.py`.

## Fixed problems (append when resolved)
- **OP-4 Auto-release build failure** (see run #C). Patched `app/server.py::_smoke_test` to exercise the full first-run path and `app/cli/create_admin.py` to run migrations before bootstrapping. Verification: ephemeral-root `--smoke-test` exit 0 with seeded dataset + full suite green (546/2). Commit: see ledger below.

## Run log — 2026-10-11 #D (builds appeared under tags, not as Releases)
- **OP-5 Release pipeline clutter.** User report: "the build releases under tags and not as releases". Root cause in `.github/workflows/release.yml`: every push to main published TWO prereleases (`latest` rolling + `build-<sha>` per-commit snapshot), so the repo's Tags page filled with `build-*` entries while nothing was ever a real, stable Release.
- Fix applied (tag-driven policy): removed the per-commit snapshot release entirely; added `tags: ["v*.*.*"]` push trigger; single "Publish release" step now resolves its target — version-tag push → stable non-prerelease GitHub Release named "HHMS <version>" with `make_latest: true`; main push / workflow_dispatch → one rolling prerelease permanently at tag `nightly` (overwritten each run, never accumulates). Added generated release notes (download table + first-run demo-data note) via `body_path`.
- Verification (this run): YAML parses; triggers = branches main + tags v*.*.*; exactly one softprops publish step; branch logic bash simulation: `refs/tags/v1.0.0` → tag=v1.0.0 prerelease=false latest=true; `refs/heads/main` → tag=nightly prerelease=true latest=false. Docs grep: no stale references to removed snapshot flow (README already says releases publish on `v*` tags). Backend suite unaffected (workflow-only change).
- To get a proper Release: `git tag v1.0.0 && git push origin v1.0.0` (remote still not configured in this workspace).

## Run log — 2026-10-11 #E (release pipeline QA follow-through)
- **OP-5 regression found & fixed.** Full-suite run after the OP-5 workflow change exposed one stale doc-contract test: `test_batch116_docs_release_pipeline_qa.py::test_release_job_publishes_both_platform_artifacts` still asserted the OLD Batch-118 policy (`tag_name: latest` + per-commit `build-${{ github.sha }}` snapshot release). Updated the test to enforce the NEW tag-driven policy instead: exactly one publish step, snapshot releases banned, rolling `nightly` target required, version-tag resolution (`refs/tags/v*`) required.
- Verification: targeted QA files 25 passed; full backend suite **546 passed, 2 skipped** (baseline preserved). Working tree otherwise untouched; workflow itself unchanged this run.

## Run log — 2026-10-11 #F (Swagger UI: "Failed to load API definition")
- **OP-6 Root cause found.** User report: openapi.json failed to load. Reproduced deterministically: `app.openapi()` raised `AssertionError: A response class is needed to generate OpenAPI`. Bisected via monkeypatch of `fastapi.openapi.utils.get_openapi_path` → offending route was `DELETE /api/v1/maintenance/report-schedules/{job_id}` in `backend/app/api/v1/endpoints/report_pdf.py`, which passed an explicit `response_class=None` on the decorator, defeating FastAPI's default-response-class fallback and breaking schema generation for the ENTIRE spec (hence /openapi.json 500 and Swagger UI error).
- **Fix applied.** Removed `response_class=None` from the delete route (204 status retained; handler still returns None). Added explanatory NOTE comment at the site so the pattern isn't reintroduced.
- **Regression guard added.** New `backend/tests/test_openapi_generation.py`: (1) `app.openapi()` must not raise and exposes >100 paths, (2) GET /openapi.json returns 200 with the report-schedules delete op + 204 response, (3) GET /docs returns 200.
- Verification: targeted file 3 passed; full backend suite **549 passed, 2 skipped** (baseline 546 + 3 new guards). Changed files: `backend/app/api/v1/endpoints/report_pdf.py`, `backend/tests/test_openapi_generation.py`.

## Fixed problems (append when resolved)
- **OP-6 /openapi.json broken ("Failed to load API definition")** (see run #F). Patched `endpoints/report_pdf.py` DELETE route (dropped `response_class=None`). Verified by fresh-schema generation (182 paths) + new test_openapi_generation.py + full suite green (549/2).

## Run log — 2026-10-11 #G (user still saw openapi.json 500 after OP-6 fix)
- **Diagnosis: stale deployment, not a code regression.** User pasted server logs showing `AssertionError: A response class is needed to generate OpenAPI` at `/openapi.json`. Verified the current workspace is clean:
  - Static grep: no `response_class=None` anywhere in `backend/app` (only legitimate `FileResponse` usages + the guard NOTE comment).
  - In-process: `app.openapi()` builds OK — **182 paths**.
  - Live boot test: spawned `python -m app.server` on an ephemeral root → `GET /openapi.json` returned **HTTP 200** with 182 paths.
  - Reproduced the user's exact error by re-adding `response_class=None` to a toy 204 route → same AssertionError string, confirming the old build was running pre-fix code.
  - Regression guards `tests/test_openapi_generation.py`: 3 passed.
- **Root cause of "not fixed": the fix lives only on branch `qwen-code-…` (commits 18b6a60 + later). The repo's `main` tip (7e023fa) contains the report_pdf fix but NOT the demo-data/OOBE/docs work; and the user's Windows server (traceback shows `starlette\...` packaged paths) is an older EXE/bundle built before OP-6.** No git remote configured, so nothing was ever pushed/rebuilt.
- **Action required (user side):** either run from this updated source tree (`cd backend && python -m app.server`) or push the branch and let the release workflow rebuild the EXE; then restart. Old process must be stopped first (port 8000 conflict explains health-probe timeout in the harness while openapi served fine from a lingering instance).

## Run log #H — GUI served by the server itself (http://localhost:8000/)

**User report:** `/docs` only shows API entries; there is no HHMS client launcher and `localhost:8000/ui` errors.

**Findings:**
- F11: The FastAPI server never served the static GUI (`frontend/`). It exists in the repo but nothing mounted it; the Windows WebView2 host (`client/HHMS.Client`) is a separate .NET build not shipped in server releases. `/ui` does not exist at all.
- F12: First mount attempt failed on 404 because `frontend_directory()` keyed off `application_root()`, which `HHMS_APPLICATION_ROOT` overrides to a *data* directory — hiding the read-only repo/bundle GUI path. Fixed by deriving repo root from the module location, with exe-adjacent + `_MEIPASS` candidates for frozen builds.

**Fixed:**
- `backend/app/app.py`: `_mount_frontend()` mounts `frontend/` at `/` (html=True) after the API router — API routes still win; graceful no-op when no bundle present.
- `backend/app/config/runtime_paths.py`: new `frontend_directory()` (env override `HHMS_FRONTEND_ROOT`, frozen-bundle aware).
- `backend/app/config/settings.py`: CORS defaults now include `http://localhost:8000` / `http://127.0.0.1:8000` (file:// or sidecar usage).
- `backend/packaging/HHMS-Server.spec` + `scripts/deploy/build-server.sh`: GUI bundled into EXE datas and copied next to Linux/Windows bundle so portable builds serve the UI out of the box.

**Verified:** fresh ephemeral root → `GET /` returns HHMS index.html (200), `/css/app.css` 200, `/js/app.js` 200, `/api/v1/health` 200, `/openapi.json` 200; admin/admin login via same-origin API returns JWT and patients list shows seeded 2025 data (Rakesh Kulkarni...). TestClient + real uvicorn both green.

## Run log #I — Wi-Fi LAN discovery + port-mismatch fix (user: "it should work on wireless lan too, no files edited")

**User report:** Automatic discovery must work over wireless LAN; user could not see any edited files because the discovery/client-launcher work from earlier chat turns was never written to disk.

**Findings:**
- F13: Server UDP responder (`backend/app/network/discovery.py`, wired into `server.py` startup) and browser GUI auto-discover flow (`frontend/js/discovery.js` → bridge, manual fallback) already existed in source and were committed. But the C# client probe (`client/HHMS.Client/Bridge/DiscoveryBridge.cs`) broadcast to UDP **38541** while the server default `DISCOVERY_PORT` was **39555** — HHMS.exe could never find a default-configured server. This is why the user's earlier request ("no files edited that I can push") had no matching deliverable for the EXE path.
- F14: The C# probe used only the global broadcast 255.255.255.255, which many Wi-Fi APs drop (limited/broadcast-address filtering), so discovery failed on wireless even with matching ports.

**Fixed (this run):**
- `backend/app/config/settings.py`: `DISCOVERY_PORT` default 39555 → **38541**, aligned with the client probe; comment added requiring both sides stay in sync.
- `client/HHMS.Client/Bridge/DiscoveryBridge.cs`: rewritten to enumerate all up/non-loopback IPv4 interfaces and probe each subnet-directed broadcast (ip | ~mask) plus the global broadcast in one round (900 ms deadline), tolerating per-interface SocketExceptions. Works on Wi-Fi, Ethernet, and multi-NIC machines without manual IP entry; dynamic IPs are irrelevant since probes go to the local subnet broadcast each launch.
- `docs/LAN_DISCOVERY.md`: documented port updated to 38541.

**Verified:** backend suite **549 passed, 2 skipped** (incl. test_lan_discovery.py + test_batch104_multi_client_lan_qa.py green against new default). No remaining references to 39555 anywhere. Note: HHMS.exe itself is built by CI (.github release workflow) — rebuild/tag required to ship the fixed client.
