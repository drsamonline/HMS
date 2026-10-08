# Batch 104 — Multi-Client LAN QA & Clean-Machine Installation Testing (Milestone 6 completion)

**Status:** ✅ Complete — closes Milestone 6. Full backend suite: **403 passed, 0 failed**.

## What this batch is about
Batch 103 delivered the E2E route suite, cross-module integration tests and a performance benchmark. Batch 104
closes the two remaining Milestone 6 gates: proving the packaged server survives **multiple concurrent LAN
clients** against one shared database, and proving a **fresh machine can install from nothing** (empty directory →
migrated schema → working login). Both gates found real release-blocking defects that no prior test could see,
because every existing suite used `create_all` on in-memory SQLite.

## Delivered

### 1. Harness extension (`backend/tests/_qa_harness.py`)
- `_build_application()` — shared full-stack ASGI assembly (middleware + exception handlers + `api_router` under `/api/v1`).
- `make_file_client(db_path)` — context manager over a **file-backed SQLite DB with WAL journaling + `busy_timeout=5000`**,
  handing out any number of independent `TestClient`s against one shared schema — the in-process analogue of several
  LAN client machines hitting one packaged server process/data file.
- `seed_client_user(index)` — active Users with pre-computed Argon2 hashes (hashed once outside the event loop),
  returning `(username, password)` for real login round-trips; `token_for_login()` obtains bearer tokens through the
  real `POST /auth/login` route.
- `concurrent_map(fn, items, workers=8)` — ThreadPoolExecutor fan-out driving simultaneous requests through the full
  stack, one client per thread.
- Test isolation hardened: cached settings/engine/session-factory cleared on every harness entry/exit
  (`get_settings.cache_clear()` alongside engine clears) so per-test `DATABASE_URL` overrides take effect.

### 2. Multi-client LAN suite (`backend/tests/test_batch104_multi_client_lan_qa.py`, 5 tests)
| Area | Proven behavior |
| --- | --- |
| Concurrent logins | N seeded users log in simultaneously through separate clients on one shared file DB; every response 200 with a valid bearer token |
| Concurrent token mints | Authenticated OPD token creation + round-trip under parallel load; strictly unique sequence numbers, no 500s |
| Concurrent registrations | Parallel patient registrations mint gap-free unique `P-####` identifiers (atomic UPDATE-based `NumberSequence` path) |
| UDP discovery | Real `HHMS_DISCOVER_V1` request/response handshake on an ephemeral port; payload agrees with `/health/discovery` |
| Health/version | Server identity and version consistent across concurrent probes |

### 3. Clean-machine installation suite (`backend/tests/test_batch104_clean_install_simulation.py`, 5 tests)
| Area | Proven behavior |
| --- | --- |
| Fresh bootstrap | Real Alembic chain **0001→0028** runs to head on an empty file DB in a fresh directory |
| Idempotency | Re-running `upgrade head` on an installed DB is a no-op |
| Schema parity | ORM metadata vs migrated schema match (columns present on both sides) |
| Empty-DB auth | First user registration + login round-trip works on a freshly installed database |
| Relocation | Runtime directories created and honored via `HHMS_APPLICATION_ROOT` override |

## Release-blocking defects found & fixed (product)
1. **SQLite concurrency deadlock** — `app/db/session.py` applied `StaticPool` to *all* SQLite URLs, pinning a single
   DBAPI connection that deadlocks any concurrent workload on the packaged file-based LAN runtime (only correct for
   `:memory:`). Now: StaticPool for `:memory:` only; file-based SQLite uses QueuePool (5+10 overflow) with
   per-connection `PRAGMA journal_mode=WAL` and `busy_timeout=5000`. Found by py-spy profiling of the hanging test.
2. **Migration chain could not reach head on a fresh install** — repaired across the chain: `0007`/`0015` invalid
   ALTER/FK patterns wrapped in `op.batch_alter_table()`; `0019` partial-index clauses wrapped in `sa.text()`;
   `0018` rewritten to create previously missing base tables (`StockBatch`, `PrescriptionItem`, `DispenseRecord`)
   that had only ever existed via `create_all`; 184 `created_at`/`updated_at` columns across 15 migrations given
   `server_default=sa.text('CURRENT_TIMESTAMP')` (fresh-install inserts were failing `NOT NULL constraint failed`).
3. **Loop-bound `asyncio.Lock`** — module-level lock in `app/services/number_sequence.py` bound to whichever event
   loop first used it, breaking under per-request loops; replaced with an atomic single-statement SQL
   `UPDATE … RETURNING` mint safe across loops and processes.

Also: Alembic config resolution hardened for relocated/clean installs (`HHMS_APPLICATION_ROOT` honored when locating
`alembic.ini` and the versions path), and secret-hygiene cleanup (`data/secret.key`, logs and SQLite runtime files
removed from git tracking and covered by `.gitignore`; stale `__pycache__` purged from the index).

## Why these gaps existed
Every pre-Batch-104 suite created schema via `Base.metadata.create_all` on in-memory SQLite with a single pooled
connection — the migration chain and multi-connection file-DB behavior were structurally untested. Batch 104's two
suites are the first to run the real Alembic chain and real concurrent clients, which is exactly the Milestone 6
mandate before release packaging.

## Test totals
- Multi-client LAN suite: **5 passed** · Clean-install suite: **5 passed**
- Full backend suite: **403 passed, 0 failed** (381 functional + 12 Batch 103 QA/E2E/integration + 10 Batch 104)

## Changed files
- `backend/tests/_qa_harness.py` (extended: `make_file_client`, `seed_client_user`, `token_for_login`, `concurrent_map`, isolation fixes)
- `backend/tests/test_batch104_multi_client_lan_qa.py` (new)
- `backend/tests/test_batch104_clean_install_simulation.py` (new)
- `backend/app/db/session.py` (pool/WAL fix)
- `backend/app/services/number_sequence.py` (atomic mint fix)
- `backend/alembic/versions/` (migration repairs: 0007, 0015, 0018, 0019, timestamp server defaults across 15 files)
- `.gitignore`, `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `.ai/PROJECT_STATE.md` (Milestone 6 closed; next: Batch 105 — Milestone 7 release packaging)
