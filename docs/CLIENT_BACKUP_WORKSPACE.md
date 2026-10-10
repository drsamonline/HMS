# Client Backup Workspace

The administration client now exposes local SQLite backup management.

## Supported operations

- list existing backups
- create a new SQLite backup
- download a backup
- delete an existing backup

Backups are stored under the server runtime `data/backups` directory.

## Scope boundary

This batch intentionally does not implement live database restoration. Restore requires a controlled server-stop/start workflow and will be added with the deployment/runtime packaging work rather than risking an unsafe in-process database replacement.
