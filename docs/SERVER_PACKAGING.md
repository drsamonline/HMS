# HHMS Server Packaging Foundation

## Target

`HHMS-Server.exe` is the authoritative LAN server. It owns the SQLite database and exposes the FastAPI API to client workstations.

## Runtime data

The packaged server uses a writable `data/` directory beside the executable by default:

```text
HHMS-Server.exe
data/
├── hhms.sqlite3
├── logs/
├── uploads/
└── backups/
```

The runtime path helper distinguishes source execution from a frozen executable, so the packaged server keeps writable data outside the bundled code. A future configuration setting may relocate the data directory if required by deployment policy.

## Database

SQLite is the portable LAN default using SQLAlchemy's async SQLite driver (`aiosqlite`). PostgreSQL remains supported through an overridden `DATABASE_URL`.

## Packaging

The initial PyInstaller specification is `backend/packaging/HHMS-Server.spec`. The final build milestone must additionally verify migrations, writable data paths, firewall configuration, backup/restore, restart behaviour and a clean machine deployment.

## Dependencies

The backend dependency set now includes `aiosqlite`. PyInstaller is an optional packaging dependency and is not required during ordinary development.
