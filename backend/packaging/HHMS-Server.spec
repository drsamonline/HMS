# PyInstaller specification for the HHMS server executable.
#
# NOTE: PyInstaller exec()s this file without defining __file__, so the spec
# directory is taken from SPECPATH (injected into the spec namespace).
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

_spec_dir = Path(os.path.abspath(SPECPATH))  # noqa: F821
project_root = _spec_dir.parents[1]
backend_root = project_root / "backend"
hidden_app_imports = collect_submodules("app")

# SQLAlchemy (and Alembic) import dialect DBAPIs lazily at engine-creation
# time, so PyInstaller's static analysis cannot see them.  aiosqlite is the
# production async driver; the sync drivers back Alembic env.py and any
# run_sync paths.  Missing entries here produce ModuleNotFoundError only in
# frozen builds on the first DB request, so pin them explicitly.
hidden_driver_imports = [
    "aiosqlite",
    "sqlite3",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.aiosqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "alembic.autogenerate",
    "alembic.runtime.plugins",
    "pwdlib._argon2",
    "pwdlib._bcrypt",
]

a = Analysis(
    [str(backend_root / "app" / "server.py")],
    pathex=[str(backend_root)],
    binaries=[],
    datas=[
        (str(backend_root / "alembic"), "alembic"),
        (str(backend_root / "alembic.ini"), "."),
        # Single-source release version: bundled at the archive root so
        # app.release_version resolves it inside the frozen executable.
        (str(project_root / "VERSION"), "."),
    ],
    hiddenimports=hidden_app_imports + hidden_driver_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(_spec_dir / "hooks" / "runtime_hook_alembic_path.py")],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HHMS-Server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
