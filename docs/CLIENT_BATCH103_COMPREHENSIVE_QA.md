# Batch 103 — Comprehensive QA (Milestone 6, in progress)

**Status:** In progress — end-to-end route suite delivered; integration/LAN/performance/clean-machine passes remain.

## What this batch is about
Batch 102 closed the remaining functional surfaces. Batch 103 begins Milestone 6: proving the whole application works as
deployed software, not just as isolated units. The first deliverable is a **full-stack QA harness** that exercises real HTTP
routes through the complete FastAPI stack (middleware → exception handlers → auth dependency → service layer → async
SQLAlchemy → database), so regressions that unit tests structurally cannot see are caught before release packaging.

## Delivered in this session

### 1. Shared QA harness (`backend/tests/_qa_harness.py`)
- `make_client()` — context manager giving each test block a fresh in-memory SQLite schema and a `TestClient` bound to the
  real `/api/v1` router with production middleware and error handlers installed.
- Schema creation runs through the async engine (`asyncio.run` + `engine.begin()` + `run_sync(create_all)`); teardown
  disposes the engine inside a dedicated event loop — no greenlet crashes, no cross-test leakage.
- Helpers: `auth_headers()` (signed JWT for authorized probes), `seed_user()` (active account with hashed password),
  `seed_number_sequence()` (identifier sequences required by write endpoints), `api_get/api_post/api_patch`.

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

## Test totals
- New E2E suite: **10 passed**
- Full backend suite: **391 passed, 0 failed** (381 functional + 10 end-to-end)

## Remaining Milestone 6 scope (next sessions)
1. Cross-module integration tests (billing ↔ payments ↔ refunds flows with real data, beyond the empty-state proofs above).
2. Multi-client LAN testing (discovery, concurrent sessions).
3. Performance testing (dashboard scan bounds under load).
4. Clean-machine installation testing — the gate into Milestone 7 (release packaging & deployment).

## Changed files
- `backend/tests/_qa_harness.py` (new/repaired)
- `backend/tests/test_batch103_qa_end_to_end.py` (new)
- `backend/app/services/auth.py` (product fix: `password_hash`)
- `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `.ai/PROJECT_STATE.md` (advanced to Batch 103; test count 391)
