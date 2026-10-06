# HHMS Deployment Scripts (Batch 105 — Milestone 7)

| Script | Platform | Purpose |
| --- | --- | --- |
| `build-server.sh` | Linux/macOS | PyInstaller one-dir build of `backend/packaging/HHMS-Server.spec`; copies `VERSION` next to the bundle. Run inside a venv with `backend/requirements.txt` + `pyinstaller`. |
| `install-first-run.sh` | Linux/macOS | Clean-machine bootstrap for source deployments: creates the `data/` tree, persists `secret.key`, runs `alembic upgrade head`, starts the server, and asserts the `/health` version handshake. Accepts an optional runtime-root argument to simulate a fresh install (`scripts/deploy/install-first-run.sh "$(mktemp -d)"`). |
| `server-launch.ps1` | Windows | Launches the packaged `HHMS-Server.exe` (falls back to source), honours `-DataRoot` relocation via `HHMS_APPLICATION_ROOT`, and optionally waits for `/health` with the same version handshake. |

## Frozen-runtime notes

- The server spec bundles `alembic/`, `alembic.ini` and `VERSION` as data
  files and registers `backend/packaging/hooks/runtime_hook_alembic_path.py`
  as a PyInstaller **runtime hook**, which prepends the bundled migration
  tree to `sys.path` so first-run `prepare_runtime()` works identically in
  frozen and source runtimes.
- Release versioning has a single source of truth: the repository-root
  `VERSION` file, resolved by `backend/app/release_version.py` in every
  layout (source checkout → application root → `sys._MEIPASS` bundle).
- WebView2: the C# client (`client/HHMS.Client`) requires the Evergreen
  WebView2 Runtime; target machines with no pre-installed runtime should
  ship `Microsoft.WebView2.FixedVersionRuntime` alongside the client EXE
  (documented in `docs/SERVER_PACKAGING.md`).

All script contracts above are enforced by
`backend/tests/test_batch105_release_packaging_qa.py`.
