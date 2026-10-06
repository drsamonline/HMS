"""Batch 108 QA — Backup/Restore workflows, client launcher & release cut.

Milestone 7 (Release) part 4 / Milestone 8 (Release Cut).  Covers:

* ``POST /maintenance/backups`` -> ``POST /{name}/restore`` full round-trip
  on a file-backed SQLite runtime (the packaged deployment shape):
  data created after the backup disappears after restore; pre-restore
  snapshots never leak into the backups listing on the happy path.
* Corrupt-upload rejection: ``POST /import`` refuses non-SQLite payloads
  and never writes them into the backups directory.
* Admin gating: every backup endpoint requires an administrator role.
* Client launcher packaging contract: single-file self-contained publish,
  WebView2 SDK pinned, frontend content bundled, version constant in
  lock-step with the root VERSION file.
* Installer script knows how to bundle the client (-IncludeClient) for
  both Inno Setup and NSIS paths while preserving the Batch 104 data
  survival contract.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

import sys

sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from _qa_harness import (  # noqa: E402
    make_file_client,
    seed_number_sequence,
)

from app.auth.jwt import create_access_token  # noqa: E402
from app.config.runtime_paths import backups_directory  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

API = "/api/v1/maintenance/backups"


def _seed_admin(client_factory, db_path: str, username: str = "batch108-admin") -> dict[str, str]:
    """Insert an active admin user directly and return bearer headers."""
    import asyncio

    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username=username,
                password_hash=hash_password("batch108-password"),
                full_name="Batch 108 QA Admin",
                email=None,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            role = Role(role_name="admin", description="QA", is_active=True)
            db.add(role)
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return user.id

    uid = asyncio.run(_seed())
    token = create_access_token(subject=str(uid))
    return {"Authorization": f"Bearer {token}"}


def _count_patients(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM patients").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def _create_patient(client, headers: dict[str, str], name: str) -> None:
    resp = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "first_name": name,
            "last_name": "QA",
            "gender": "male",
            "date_of_birth": "1980-01-01",
            "mobile_number": "9876500000",
        },
    )
    assert resp.status_code in (200, 201), resp.text


# ---------------------------------------------------------------------------
# 1. Full backup -> modify -> restore round-trip on the packaged file DB
# ---------------------------------------------------------------------------


def test_backup_restore_roundtrip_preserves_point_in_time(tmp_path) -> None:
    db_file = tmp_path / "hhms-backup-restore.sqlite3"
    with make_file_client(str(db_file)) as (client_factory, dispose):
        headers = _seed_admin(client_factory, str(db_file))
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        client = client_factory()

        # Seed one patient BEFORE the backup.
        _create_patient(client, headers, "Pre Backup Patient")
        assert _count_patients(str(db_file)) == 1

        # Take the backup through the real API.
        created = client.post(f"{API}", headers=headers, json={"name": "golden"})
        assert created.status_code == 201, created.text
        assert created.json()["name"] == "golden.sqlite3"

        # Mutate live data AFTER the backup point.
        _create_patient(client, headers, "Post Backup Patient")
        assert _count_patients(str(db_file)) == 2

        # Restore the golden snapshot.
        restored = client.post(f"{API}/golden/restore", headers=headers)
        assert restored.status_code == 200, restored.text
        body = restored.json()
        assert body["restored"] == "golden.sqlite3"

        # Live DB is back at the point-in-time state.
        assert _count_patients(str(db_file)) == 1

        dispose()


def test_restore_leaves_no_pre_restore_snapshot_on_success(tmp_path) -> None:
    db_file = tmp_path / "hhms-snapshot-leak.sqlite3"
    with make_file_client(str(db_file)) as (client_factory, dispose):
        headers = _seed_admin(client_factory, str(db_file), username="snap-admin")
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        client = client_factory()

        _create_patient(client, headers, "Snapshot Patient")
        assert client.post(f"{API}", headers=headers, json={"name": "snap"}).status_code == 201

        resp = client.post(f"{API}/snap/restore", headers=headers)
        assert resp.status_code == 200, resp.text

        listing = client.get(API, headers=headers)
        assert listing.status_code == 200
        names = [row["name"] for row in listing.json()]
        # Happy path must clean up its own pre-restore snapshot.
        assert not any(n.startswith("pre-restore-") for n in names), names

        dispose()


# ---------------------------------------------------------------------------
# 2. Import/export integrity gates
# ---------------------------------------------------------------------------


def test_import_rejects_non_sqlite_payload(tmp_path) -> None:
    db_file = tmp_path / "hhms-import-gate.sqlite3"
    with make_file_client(str(db_file)) as (client_factory, dispose):
        headers = _seed_admin(client_factory, str(db_file), username="import-admin")
        client = client_factory()

        bad = client.post(
            f"{API}/import",
            headers=headers,
            files={"file": ("junk.sqlite3", b"this is definitely not a sqlite database", "application/octet-stream")},
        )
        assert bad.status_code >= 400, bad.text

        listing = client.get(API, headers=headers)
        assert all(row["name"] != "junk.sqlite3" for row in listing.json())

        dispose()


def test_download_returns_exact_backup_bytes(tmp_path) -> None:
    db_file = tmp_path / "hhms-download.sqlite3"
    with make_file_client(str(db_file)) as (client_factory, dispose):
        headers = _seed_admin(client_factory, str(db_file), username="dl-admin")
        client = client_factory()

        assert client.post(f"{API}", headers=headers, json={"name": "dl"}).status_code == 201
        on_disk = (backups_directory() / "dl.sqlite3").read_bytes()

        resp = client.get(f"{API}/dl/download", headers=headers)
        assert resp.status_code == 200
        assert resp.content == on_disk

        dispose()


# ---------------------------------------------------------------------------
# 3. Admin gating
# ---------------------------------------------------------------------------


def test_backup_endpoints_require_administrator(tmp_path) -> None:
    db_file = tmp_path / "hhms-gating.sqlite3"
    with make_file_client(str(db_file)) as (client_factory, dispose):
        # Non-admin authenticated user (valid JWT, no admin role).
        import asyncio

        from app.auth.password import hash_password
        from app.db.session import get_session_factory
        from app.models.user import User

        factory = get_session_factory()

        async def _seed_plain() -> int:
            async with factory() as db:
                user = User(
                    username="plain-user",
                    password_hash=hash_password("pw"),
                    full_name="Plain",
                    email=None,
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                return user.id

        uid = asyncio.run(_seed_plain())
        plain_headers = {"Authorization": f"Bearer {create_access_token(subject=str(uid))}"}

        client = client_factory()
        assert client.get(API, headers=plain_headers).status_code >= 400
        assert client.post(API, headers=plain_headers, json={"name": "x"}).status_code >= 400
        assert client.post(f"{API}/anything/restore", headers=plain_headers).status_code >= 400

        dispose()


# ---------------------------------------------------------------------------
# 4. Client launcher packaging contract
# ---------------------------------------------------------------------------


def test_client_project_publishes_single_self_contained_exe() -> None:
    csproj = (PROJECT_ROOT / "client" / "HHMS.Client" / "HHMS.Client.csproj").read_text(encoding="utf-8")
    assert "<PublishSingleFile>true</PublishSingleFile>" in csproj
    assert "<SelfContained>true</SelfContained>" in csproj
    assert "<RuntimeIdentifier>win-x64</RuntimeIdentifier>" in csproj
    assert "<AssemblyName>HHMS-Client</AssemblyName>" in csproj


def test_client_pins_webview2_and_bundles_frontend() -> None:
    csproj = (PROJECT_ROOT / "client" / "HHMS.Client" / "HHMS.Client.csproj").read_text(encoding="utf-8")
    assert "Microsoft.Web.WebView2" in csproj
    match = re.search(r'Include="Microsoft.Web.WebView2" Version="([^"]+)"', csproj)
    assert match, "WebView2 package version must be pinned exactly"
    assert re.fullmatch(r"\d+(\.\d+){3}", match.group(1)), match.group(1)
    # Frontend SPA ships inside the launcher payload.
    assert 'Content Include="..\\..\\frontend\\**\\*"' in csproj


def test_client_version_constant_matches_root_version_file() -> None:
    program = (PROJECT_ROOT / "client" / "HHMS.Client" / "Program.cs").read_text(encoding="utf-8")
    match = re.search(r'public const string Version = "([^"]+)"', program)
    assert match, "Program.Version constant missing"
    root_version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert match.group(1) == root_version, (
        f"client Program.Version {match.group(1)!r} drifted from root VERSION {root_version!r}"
    )


# ---------------------------------------------------------------------------
# 5. Installer bundles the client when asked (both toolsets)
# ---------------------------------------------------------------------------


def test_installer_script_supports_include_client_switch() -> None:
    source = (PROJECT_ROOT / "scripts" / "deploy" / "build-installer.ps1").read_text(encoding="utf-8")
    assert "[switch]$IncludeClient" in source
    assert "HHMS-Client.exe" in source
    # Both generator paths know about the client.
    assert source.count("HHMS-Client.exe") >= 4, "Inno AND NSI sections must reference the client"
    assert "Microsoft.Web.WebView2" in source, "WebView2 assemblies must be bundled fixed-runtime style"


def test_installer_still_preserves_data_with_client_option() -> None:
    source = (PROJECT_ROOT / "scripts" / "deploy" / "build-installer.ps1").read_text(encoding="utf-8")
    # Batch 104 data-survival contract intact after Batch 108 edits.
    assert "Intentionally EMPTY for data/" in source
    assert "patient\n  ; data survives uninstall" in source or "data survives uninstall" in source


# ---------------------------------------------------------------------------
# 6. Release-cut hygiene: VERSION <-> fallback constant lock-step
# ---------------------------------------------------------------------------


def test_release_fallback_version_matches_version_file() -> None:
    from app.release_version import FALLBACK_VERSION

    root_version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert FALLBACK_VERSION == root_version, (
        "release_version.FALLBACK_VERSION must equal root VERSION before the tag is cut"
    )
