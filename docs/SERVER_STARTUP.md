# HHMS Server Startup and Runtime Hardening

## Startup sequence

`HHMS-Server.exe` (or source `python backend/app/server.py`) performs:

1. Create writable `data/`, `data/logs/`, `data/uploads/`, and `data/backups/`.
2. Load or generate a persistent local JWT secret at `data/secret.key` when `SECRET_KEY` is not supplied.
3. Configure rotating file logging.
4. Apply pending Alembic migrations to the configured database.
5. Start Uvicorn on the configured LAN host/port.

## First-run behavior

The packaged server can start without a pre-created secret. Runtime state is stored beside the executable, while `.env` remains an optional configuration override.

## Failure behavior

If migrations or runtime preparation fail, server startup stops instead of serving an uninitialized database.

## Deployment note

The next packaging milestone should verify a clean Windows machine, migration startup, restart persistence, writable directories, backup/restore, and LAN firewall configuration.
