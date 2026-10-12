# PyInstaller specification for the HHMS server executable.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# NOTE: .spec files are exec()'d by PyInstaller without a __file__ global;
# SPECPATH is the documented substitute (absolute dir containing the spec).
_spec_dir = Path(SPECPATH).resolve()  # noqa: F821  (injected by PyInstaller)
project_root = _spec_dir.parents[1]
backend_root = project_root / "backend"
hidden_app_imports = collect_submodules("app")

# Lazy-loaded database drivers: SQLAlchemy imports the DBAPI module named by
# the DATABASE_URL scheme only at engine-creation time (dialect.import_dbapi),
# so PyInstaller's static analysis cannot see them.  aiosqlite (async app
# runtime) and sqlite3 (sync Alembic migrations) must be listed explicitly or
# the frozen server bootstraps the schema but 500s on every request.
hidden_app_imports += ["aiosqlite", "sqlite3"]

# Desktop console (app/desktop_console.py) imports tkinter lazily and pystray/
# PIL inside try/except, so PyInstaller's static analysis misses them; collect
# them explicitly or the packaged tray + live-log window silently disappears.
hidden_app_imports += ["tkinter", "pystray", "PIL", "PIL.Image", "PIL.ImageDraw"]

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
        # HHMS browser GUI served by the server itself ("/" -> index.html)
        # so portable builds are usable without any separate client launch.
        (str(project_root / "frontend"), "frontend"),
    ],
    hiddenimports=hidden_app_imports,
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
