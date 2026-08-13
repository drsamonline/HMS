# PyInstaller specification for the HHMS server executable.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(__file__).resolve().parents[2]
backend_root = project_root / "backend"
hidden_app_imports = collect_submodules("app")

a = Analysis(
    [str(backend_root / "app" / "server.py")],
    pathex=[str(backend_root)],
    binaries=[],
    datas=[
        (str(backend_root / "alembic"), "alembic"),
        (str(backend_root / "alembic.ini"), "."),
    ],
    hiddenimports=hidden_app_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
