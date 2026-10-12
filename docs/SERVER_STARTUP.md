# HHMS Server Startup and Runtime Hardening

## Startup sequence

`HHMS-Server.exe` (or source `python -m app.server` from `backend/`) performs:

1. Create writable `data/`, `data/logs/`, `data/uploads/`, and `data/backups/`.
2. Load or generate a persistent local JWT secret at `data/secret.key` when `SECRET_KEY` is not supplied (min length 32; owner-only file mode).
3. Configure rotating file logging.
4. Apply pending Alembic migrations to the configured database.
5. Bootstrap the default administrator (`admin` / `admin`) when the users table is empty — idempotent, never touches existing accounts; disable with `HHMS_BOOTSTRAP_DEFAULT_ADMIN=false`.
6. Seed the 2025 demo dataset when the database is pristine (marker-guarded, service-layer writes only) — disable with `HHMS_SEED_DEMO_DATA=false`; a seeding failure never blocks boot. See [DEMO_DATA.md](DEMO_DATA.md).
7. Start Uvicorn on the configured LAN host/port and start the UDP LAN-discovery responder (`DISCOVERY_PORT`, default `38541`).

## Served surfaces

The server also hosts the built-in web GUI: `frontend/` is mounted at `/` (API routes under `/api/v1` take precedence), so opening `http://<server>:8000/` in any LAN browser is enough — the WebView2 desktop client is an optional shell over the same UI. Interactive API docs live at `/docs`, machine-readable spec at `/openapi.json`.

## First-run behavior

The packaged server can start without a pre-created secret. Runtime state is stored beside the executable, while `.env` remains an optional configuration override. A fresh install is fully usable out of the box: log in as `admin` / `admin` (change immediately) and every dashboard/report renders populated 2025 demo figures.

## Smoke test

`HHMS-Server --smoke-test` (also `python -m app.server --smoke-test`) boots the real first-run path against a throwaway runtime root — migrations, default-admin bootstrap, demo seed — then polls `/health` and asserts the reported version matches `VERSION`, exiting 0/1. Both CI build jobs gate on it, so a broken out-of-the-box experience fails the release build instead of shipping.

## Failure behavior

If migrations or runtime preparation fail, server startup stops instead of serving an uninitialized database.

## Deployment note

Before production: execute the [secret-key rotation runbook](SECRET_ROTATION_RUNBOOK.md), set `HHMS_SEED_DEMO_DATA=false`, change the default admin password, and open the LAN firewall for the HTTP port plus UDP `38541` (discovery). Clean-machine verification (migration startup, restart persistence, writable directories, backup/restore) is covered by the Batch 104/106/108 QA suites.
