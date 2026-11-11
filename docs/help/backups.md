# Backups

A backup nobody has restored is a file, not a backup. The drill is in
`docs/OPERATIONS.md`, section 3, and it takes an afternoon.

Take one by hand before anything risky: a restore, a rollover, an upgrade.

Never restore over a running server. Stop it, restore, start, then check the health
endpoint.
