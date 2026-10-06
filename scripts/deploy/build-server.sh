#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# HHMS server build script (Linux/macOS) — Milestone 7 Batch 105.
#
# Produces a PyInstaller one-directory server bundle from
# backend/packaging/HHMS-Server.spec. The Windows EXE build uses the same
# spec via server-launch.ps1 / CI on a windows runner.
#
# Usage:  scripts/deploy/build-server.sh [output-dir]
# Requires: Python 3.12 venv with backend/requirements.txt + pyinstaller.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_ROOT="${PROJECT_ROOT}/backend"
SPEC="${BACKEND_ROOT}/packaging/HHMS-Server.spec"
OUT_DIR="${1:-${PROJECT_ROOT}/build/dist}"

VERSION="$(cat "${PROJECT_ROOT}/VERSION")"
echo "==> Building HHMS Server v${VERSION} from ${SPEC}"

if [ ! -f "${SPEC}" ]; then
    echo "ERROR: spec file not found: ${SPEC}" >&2
    exit 1
fi

python -m PyInstaller --version >/dev/null 2>&1 || {
    echo "ERROR: PyInstaller is not installed in the active environment." >&2
    echo "       Run: pip install pyinstaller" >&2
    exit 1
}

cd "${BACKEND_ROOT}"
python -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath "${OUT_DIR}" \
    --workpath "${PROJECT_ROOT}/build/work" \
    --specpath "${BACKEND_ROOT}/packaging" \
    "${SPEC}"

BUNDLE="${OUT_DIR}/HHMS-Server"
if [ ! -x "${BUNDLE}/HHMS-Server" ] && [ ! -f "${BUNDLE}/HHMS-Server" ]; then
    echo "ERROR: expected bundle executable missing at ${BUNDLE}/HHMS-Server" >&2
    exit 1
fi

# Ship the release VERSION next to the bundle for application-root resolution.
cp "${PROJECT_ROOT}/VERSION" "${BUNDLE}/VERSION"

echo "==> Build complete: ${BUNDLE}"
echo "    Start with: ${BUNDLE}/HHMS-Server   (first run bootstraps data/ and migrations)"
