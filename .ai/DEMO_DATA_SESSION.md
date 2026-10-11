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
