# Batch 103 — Comprehensive QA (Milestone 6)

**Status:** ✅ Complete — E2E route suite, cross-module integration and performance benchmark delivered in Batch 103;
the remaining Milestone 6 passes (multi-client LAN testing, clean-machine installation) were closed in Batch 104
(see [CLIENT_BATCH104_LAN_MULTI_CLIENT_INSTALLATION_QA.md](CLIENT_BATCH104_LAN_MULTI_CLIENT_INSTALLATION_QA.md)).
Milestone 6 is now fully complete with the full backend suite at **403 passed**.

## What this batch is about
Batch 102 closed the remaining functional surfaces. Batch 103 begins Milestone 6: proving the whole application works as
deployed software, not just as isolated units. The first deliverable is a **full-stack QA harness** that exercises real HTTP
routes through the complete FastAPI stack (middleware → exception handlers → auth dependency → service layer → async
SQLAlchemy → database), so regressions that unit tests structurally cannot see are caught before release packaging.

## Delivered so far

### 1. Shared QA harness (`backend/tests/_qa_harness.py`)
- `make_client()` — context manager giving each test block a fresh in-memory SQLite schema and a `TestClient` bound to the
  real `/api/v1` router with production middleware and error handlers installed.
- Schema creation runs through the async engine (`asyncio.run` + `engine.begin()` + `run_sync(create_all)`); teardown
  disposes the engine inside a dedicated event loop — no greenlet crashes, no cross-test leakage.
- Helpers: `auth_headers()` (signed JWT for authorized probes), `seed_user()` (active account with hashed password),
  `seed_number_sequence()` (identifier sequences required by write endpoints), `seed_visit()` (direct Visit insert that
  maintains the `visit_number` sequence for cross-module chains), `api_get/api_post/api_patch/api_put`.

### 2. A real product bug found and fixed ✅
The very first end-to-end login probe returned **HTTP 500**: `app/services/auth.py` verified credentials against
`user.hashed_password`, but the User model column is `password_hash`. **Every real login would have crashed.** Fixed to
`user.password_hash` and locked in by regression tests. This is exactly the defect class Milestone 6 exists to catch —
no prior test ever drove the full login route.

### 3. End-to-end route suite (`backend/tests/test_batch103_qa_end_to_end.py`, 10 tests)
| Area | Proven behavior |
| --- | --- |
| Health | `GET /health/live` answers 200 `{"status": "healthy"}` without authentication |
| Auth | Valid seeded credentials → 200 bearer token; wrong password → structured 401 (never 500) |
| Auth | `GET /auth/me` round-trips with a genuinely issued token; unauthenticated & forged-token requests rejected 401 |
| Patients | Create over HTTP mints the sequence number (`P-0001`), normalizes padded text (`"QA "` → `"QA"`), then fetch / list+search / empty-search all behave |
| Error paths | Missing `NumberSequence` configuration surfaces as a handled 404, not a crash |
| Dashboard | All 14 dashboard GET feeds — including the Batch 99 discharge audit, Batch 100 refund audit & OPD queue summary, and Batch 102 investigation billing reconciliation — answer 200 with well-formed envelopes on a cold, empty database |

Route paths were verified against the actual `@router.get` decorators registered on the dashboard router, correcting two
mis-guessed probe paths from the initial QA pass (they were harness errors, not product defects).

### 4. Cross-module integration suite (`backend/tests/test_batch103_cross_module_integration.py`, 2 tests)
| Flow | Proven behavior |
| --- | --- |
| OPD journey | Patient registered over HTTP (`P-0001`) → visit seeded (`V-0001`, readable via `GET /visits/{id}`) → OPD token minted (`token_number == 1`, status `waiting`) |
| Guard rails | Duplicate token for the same visit rejected as a handled 4xx — never a 500 |
| Queue lifecycle | `PUT /opd-tokens/{id}` progresses `waiting → called → completed` with timestamps; queue list returns exactly the progressed row |
| Warm-state feeds | All 14 dashboard/audit feeds (Batches 98–102 incl. refund audit, discharge audit and investigation billing reconciliation) answer 200 with dict envelopes once real patient/visit/token rows exist — closing the cold-state-only gap of the first suite |

### 5. Performance smoke benchmark
File-backed SQLite database, full middleware stack, single client:
- Login round-trip (argon2 verification + JWT issue): ~0.6 s one-off, then 200 sequential patient registrations in **1.92 s (~104 writes/s)**.
- List read (100-row page): **9.8 ms**.
- All 14 dashboard audit feeds: **102.5 ms total (7.3 ms avg)** on a warm 200-patient database.

Verdict: comfortably inside the sub-second interaction budget for the intended single-server LAN deployment; no optimization
work required before Milestone 7 packaging.

## Test totals
- E2E route suite: **10 passed** · Cross-module integration suite: **2 passed**
- Full backend suite: **393 passed, 0 failed** (381 functional + 12 QA/E2E/integration)

## Remaining Milestone 6 scope (closed in Batch 104 ✅)
1. Multi-client LAN testing (discovery, concurrent sessions against a shared server process) — done in Batch 104.
2. Clean-machine installation testing — the gate into Milestone 7 (release packaging & deployment) — done in Batch 104.

## Changed files
- `backend/tests/_qa_harness.py` (new/repaired; extended with `seed_visit()`, `api_put()`)
- `backend/tests/test_batch103_qa_end_to_end.py` (new)
- `backend/tests/test_batch103_cross_module_integration.py` (new)
- `backend/app/services/auth.py` (product fix: `password_hash`)
- `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `.ai/PROJECT_STATE.md` (advanced to Batch 103; test count 393)
