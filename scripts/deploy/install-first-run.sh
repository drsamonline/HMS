#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# HHMS first-run installation bootstrap (clean machine) — Batch 105.
#
# Mirrors the prepare_runtime() contract verified by the Batch 104 clean
# install suite, for source-tree deployments (no PyInstaller required):
#   1. create the writable data directory tree (data/, logs, uploads,
#      backups, archive/cold, maintenance, tmp),
#   2. generate/persist the local JWT secret (data/secret.key),
#   3. apply all Alembic migrations to head on a fresh SQLite file DB,
#   4. start the server and wait until GET /health answers 200,
#   5. print the release version reported by the running server.
#
# Usage:  scripts/deploy/install-first-run.sh [runtime-root]
# The runtime root defaults to the repository root; pass an empty temp
# directory to simulate a clean-machine install.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_ROOT="${PROJECT_ROOT}/backend"
RUNTIME_ROOT="${1:-${PROJECT_ROOT}}"
DB_FILE="${RUNTIME_ROOT}/data/hhms.sqlite3"

VERSION="$(cat "${PROJECT_ROOT}/VERSION")"
echo "==> HHMS v${VERSION} first-run install into ${RUNTIME_ROOT}"

export HHMS_APPLICATION_ROOT="${RUNTIME_ROOT}"

# 1. Writable runtime directories (prepare_runtime contract).
mkdir -p "${RUNTIME_ROOT}/data"/{logs,uploads,backups,archive/cold,maintenance,tmp}

# 2. Persistent local JWT secret.
if [ ! -s "${RUNTIME_ROOT}/data/secret.key" ]; then
    python - "$@" <<'PYEOF'
import secrets, pathlib, os
root = pathlib.Path(os.environ["HHMS_APPLICATION_ROOT"]) / "data"
root.mkdir(parents=True, exist_ok=True)
(root / "secret.key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
PYEOF
    chmod 600 "${RUNTIME_ROOT}/data/secret.key"
fi

# 3. Database bootstrap: alembic upgrade head on the fresh file DB.
if [ ! -f "${DB_FILE}" ]; then
    echo "==> Bootstrapping database at ${DB_FILE}"
    (cd "${BACKEND_ROOT}" && alembic upgrade head)
else
    echo "==> Existing database found; applying pending migrations"
    (cd "${BACKEND_ROOT}" && alembic upgrade head)
fi

# 4. Start the server and probe health.
SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
SERVER_PORT="${SERVER_PORT:-8000}"
echo "==> Starting HHMS server on ${SERVER_HOST}:${SERVER_PORT}"
(cd "${BACKEND_ROOT}" && python -m app.server) &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
    if curl -sf "http://${SERVER_HOST}:${SERVER_PORT}/api/v1/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

HEALTH="$(curl -sf "http://${SERVER_HOST}:${SERVER_PORT}/api/v1/health")" || {
    echo "ERROR: server did not become healthy within 30s" >&2
    exit 1
}
echo "==> Health: ${HEALTH}"

# 5. Version handshake: the running server must report VERSION.
if ! printf '%s' "${HEALTH}" | grep -q "\"version\".*\"${VERSION}\""; then
    echo "ERROR: server version does not match VERSION file (${VERSION})" >&2
    exit 1
fi

echo "==> HHMS v${VERSION} installed and healthy. Server PID ${SERVER_PID}."
