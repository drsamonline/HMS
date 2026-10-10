# Batch 105 — Release Packaging Infrastructure & Deployment Scripts

**Milestone:** 7 (Release) — part 1
**Status:** ✅ Complete (packaging infrastructure; EXE build execution deferred to Batch 106)
**Test suite:** `backend/tests/test_batch105_release_packaging_qa.py` (18 tests) — full backend suite **421 passed**

## Scope

Batch 105 establishes the release-packaging foundations required by Milestone 7:
one canonical version source, Alembic that works inside a frozen executable, an
updated server spec, and first-run/build/deploy scripts — all verified without
requiring an actual Windows/Linux EXE build in this environment.

## Delivered

### 1. Single-source release versioning — `backend/app/release_version.py`
- Canonical version comes from the repository-root `VERSION` file (`0.0.1`).
- Resolution order adapts to runtime layout:
  - **PyInstaller frozen:** `_MEIPASS/VERSION` → exe-adjacent `VERSION` → repo-root walk.
  - **Source checkout:** repo-root walk from the module location.
- `app/config/settings.py` derives `APP_VERSION` from this module (no more
  hardcoded default), so `/health` reports the true release version on every
  layout — the client's version handshake therefore validates against the
  packaged release, not a stale constant.

### 2. Frozen-runtime Alembic — `backend/packaging/hooks/runtime_hook_alembic_path.py`
- PyInstaller runtime hook injecting the bundled migration directory into
  `sys.path`, so `alembic upgrade head` resolves the versions package inside
  the packaged server (the failure mode that would otherwise break every fresh
  install of the EXE).
- `backend/packaging/HHMS-Server.spec` updated: bundles the `VERSION` file as a
  data asset and registers the runtime hook.

### 3. Deployment scripts — `scripts/deploy/`
| Script | Purpose |
|---|---|
| `build-server.sh` | Linux/macOS PyInstaller build wrapper (spec-driven, output under `dist/`) |
| `install-first-run.sh` | First-run kit: creates runtime dirs, bootstraps a fresh DB through the verified 0001→0028 chain, health probe |
| `server-launch.ps1` | Windows launcher; surfaces the WebView2 prerequisite check in the launch banner |
| `README.md` | Usage documentation for all three |

### 4. QA suite (18 tests) — `backend/tests/test_batch105_release_packaging_qa.py`
- Version resolution across all three layouts (parametrized fake-frozen/source trees).
- Runtime-hook path-injection behavior (inserts bundled dir, idempotent, no-op when absent).
- Spec-file integrity: hook registered, `VERSION` bundled, datas well-formed tuples.
- Deployment-script syntax: `bash -n` on both shell scripts, executable bits set, PowerShell parse-lint where `pwsh` is available.
- `/health` handshake: reports the VERSION-file release version with a stable server id.

### 5. Secret-hygiene completion
- `.gitignore` hardened: runtime data (`data/*.sqlite3*`, `secret.key`, `server_id`,
  uploads, backups, logs), build artifacts (`build/`, `dist/`), environments and caches.
- **334 stale tracked artifacts untracked**: 328 committed `__pycache__/*.pyc` files,
  the live `data/hhms.sqlite3` (+WAL/SHM), `data/logs/hhms.log`, `data/server_id`.
- ⚠️ Residual risk: `data/secret.key` remains in git **history** (through Batch
  104-era commits). The JWT signing secret must be rotated before any production
  release — gated under ROADMAP "Production release".

## Environment note
The test venv had drifted to pytest 9.x, whose stricter plugin loading rejects a
pre-existing system `libtmux` plugin (mark-on-fixture pattern) and crashes
collection. This is not a project defect; the pinned stack (pytest 8.4.2) was
restored and all suites re-verified green.

## Remaining Milestone 7 scope (Batch 106+)
- Execute actual PyInstaller builds on Windows and Linux runners (server + client EXEs).
- WebView2 offline redistributable bundling in the client installer.
- Documentation finalization and user training materials.
- Production release (after secret rotation).
