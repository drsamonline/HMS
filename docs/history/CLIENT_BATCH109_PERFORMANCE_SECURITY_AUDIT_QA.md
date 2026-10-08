# Batch 109 — Performance & Security Audit Pass (Milestone 7 · part 5)

Closes the pre-release performance and security audit scope for HHMS. The
audit identified one real gap — `POST /api/v1/auth/login` had no brute-force
throttle — plus several invariants worth locking down permanently (middleware
ordering, JWT handling, pagination bounds, health-probe latency).

## Security fix: login rate limiting

New dependency-free middleware module `backend/app/middleware/rate_limit.py`:

| Component | Behaviour |
| --- | --- |
| `SlidingWindowRateLimiter` | Thread-safe sliding-window counter keyed per client; deque of hit timestamps per key, exact budget enforcement under races (`threading.Lock`), deterministic window expiry, `reset()` for tests/admin. Rejects `limit < 1` and non-positive windows. |
| `_client_key(scope)` | Identity resolution: first `X-Forwarded-For` entry when present (proxied deployments), otherwise the raw TCP peer — so spoofing a proxy header only shifts *your own* bucket, never another client's. |
| `RateLimitMiddleware` | ASGI middleware that meters **only** `RATE_LIMITED_PATHS = {"/api/v1/auth/login"}` (method-sensitive: `GET /api/v1/auth/login` is not metered). Over-budget clients receive a structured HTTP **429** with `Retry-After` *before* any Argon2 verification work happens — capping both credential-stuffing throughput and hash-work DoS. Non-login traffic (health probes, patient reads) never consumes the login budget. |

Wiring: mounted as the **outermost** middleware in `create_application()`
(`backend/app/app.py`) so throttled requests are rejected before logging,
request-ID, and process-time overhead. The QA harness stack
(`backend/tests/_qa_harness.py`) mirrors production ordering with a clamped
budget (`max(settings, 200)`) so legitimate suites — concurrent LAN logins,
repeated auth probes — never trip it.

Settings surface (`backend/app/config/settings.py`, env-overridable, validated):

- `LOGIN_RATE_LIMIT_ATTEMPTS` (default 10, `ge=1`)
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (default 60, `ge=1`)

## Performance gates

- Patient list pagination must push SQL-level `LIMIT`/`OFFSET`
  (`PatientRepository.search`) — bounded pages, no unbounded fetches or
  Python-side slicing.
- `GET /patients` hard-caps page size at the query level (`le=100`) and
  rejects negative offsets (`ge=0`).
- Health probes stay sub-second: 50 sequential in-process `/api/v1/health`
  requests complete in well under 2 s with `X-Process-Time` present —
  regression tripwire for CI runners.

## JWT audit invariants

- Reserved claims (`exp`, `iat`, `sub`, …) cannot be overridden through
  `additional_claims`.
- Expired tokens are rejected on decode (`ExpiredSignatureError`); tampered
  signatures raise `InvalidTokenError`. Note: `create_access_token` itself
  refuses non-positive lifetimes, so the QA suite forges an expired token
  directly with the pinned algorithm/secret to exercise decode-side
  enforcement.
- Algorithm pinning: only `JWT_ALGORITHM` (HS256) is accepted at decode;
  `alg:none` and RS256 confusion attacks are rejected.
- Secret-key minimum-entropy guard remains asserted (short secrets refused).

## QA suite

`backend/tests/test_batch109_performance_security_audit_qa.py` — **20 tests**:
6 limiter unit-contract tests (budget, per-key isolation, deterministic
expiry, reset, invalid config, 100-thread race exactness), 3 wiring/ordering
tests (production outermost, harness mirror, path scoping), 2 settings tests,
2 end-to-end throttle tests (real ASGI stack, 429 + `Retry-After` over
`X-Forwarded-For` identity, non-login traffic exemption), 3 performance-gate
tests, and 4 JWT/secret invariant tests.

Fixes surfaced during verification: the suite used package-style
`tests._qa_harness` imports although `tests/` has no `__init__.py` (switched
to the flat `import _qa_harness` contract shared by every other batch suite),
and the expired-JWT test misused `create_access_token(expires_delta=-30)`
which raises by design (switched to direct forging).

## Environment note

The `alembic` runtime package (declared in `requirements.txt` since
Batch 104-era migrations) was missing from the CI venv, breaking collection
of `test_batch104_clean_install_simulation.py` and `test_server_startup.py`.
Installed via `pip install alembic` (no code change required).

## Results

Full backend suite after Batch 109: **468 passed, 2 skipped** (up from 448;
+20 Batch 109 tests; skips remain the opt-in tier-2 EXE-build tests).

Remaining Milestone 7 scope: WebView2 offline redistributable CAB bundling,
documentation/training finalization, production release gated on secret-key
rotation (`data/secret.key` persists in git history through Batch 104-era
commits).
