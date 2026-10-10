# Batch 108 — Backup/Restore Workflows, Client Launcher Packaging Contract & Release QA

> Milestone 7 (Release), part 4. Closes two open release-work items: verified
> backup/restore/recovery workflows and the client launcher (`HHMS-Client.exe`)
> packaging contract with pinned WebView2 runtime support, locked in by an
> 11-test QA suite.

## Scope

1. **Backup / restore / recovery workflows** exercised end-to-end against the
   packaged deployment shape (file-backed SQLite DB under a real ASGI stack).
2. **Client launcher packaging verification** — `client/HHMS.Client`
   (`HHMS-Client.exe`) publish contract: single-file self-contained win-x64
   executable, pinned WebView2 SDK, bundled frontend content, version constant
   in lock-step with the root `VERSION` file.
3. **Installer integration** — `scripts/deploy/build-installer.ps1` learned an
   optional `-IncludeClient` switch that bundles the launcher for both the Inno
   Setup and NSIS paths without weakening the Batch 104 patient-data survival
   contract.

## Backup / restore endpoints

The maintenance router exposes the full backup surface under
`/api/v1/maintenance/backups` (`backend/app/api/v1/endpoints/backups.py`,
service in `backend/app/services/backup.py`, schemas in
`backend/app/schemas/backup.py`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/maintenance/backups` | List backup archives (`name`, `size_bytes`, `modified_at`) |
| POST | `/maintenance/backups` | Create a consistent backup of the live database (`BackupCreate.name` optional) |
| POST | `/maintenance/backups/import` | Import an externally supplied archive; payload is validated as a real SQLite database before it is ever written into the backups directory |
| GET | `/maintenance/backups/{name}/download` | Stream the exact archived bytes (`FileResponse`) |
| POST | `/maintenance/backups/{name}/restore` | Point-in-time restore (`BackupRestoreResult`: `restored`, `database`, `restored_at`) |
| DELETE | `/maintenance/backups/{name}` | Remove an archive |

Every endpoint is gated by `_require_admin`: the caller must carry an active
role in `{admin, administrator, superuser}` joined through `UserRole`. Raw JWT
subjects without a real admin role assignment are correctly rejected — the QA
harness therefore seeds genuine admin users rather than trusting token claims.

## Restore semantics verified by QA

- **Point-in-time fidelity**: rows created *after* a backup disappear after
  `POST /{name}/restore`; pre-backup data survives intact.
- **No snapshot leakage**: the pre-restore safety snapshot taken during a
  successful restore never appears in the `GET /maintenance/backups` listing.
- **Corrupt-upload rejection**: `POST /import` refuses non-SQLite payloads and
  leaves the backups directory untouched (no partial/foreign files).
- **Download integrity**: `GET /{name}/download` returns byte-for-byte the
  archive that was created.
- **Administrator gating**: each verb above returns 403/401-class rejection for
  non-admin authenticated users on a file-backed runtime.

## Client launcher packaging contract

`client/HHMS.Client/HHMS.Client.csproj` is locked by static-analysis QA tests:

- `Microsoft.NET.Sdk.WindowsDesktop`, `net8.0-windows`, WinForms, x64.
- `<RuntimeIdentifier>win-x64</RuntimeIdentifier>` +
  `<SelfContained>true</SelfContained>` + `<PublishSingleFile>true</PublishSingleFile>`
  → one drop-in `HHMS-Client.exe` (`dotnet publish client/HHMS.Client -c Release`).
- `IncludeNativeLibrariesForSelfExtract` + `EnableCompressionInSingleFile` for
  clean single-file extraction and small artifact size.
- **WebView2 pinned**: `PackageReference Microsoft.Web.WebView2` at an exact
  version (`1.0.3856.49`) — no floating SDK on the release path. The launcher
  creates its own `CoreWebView2Environment` with a per-user userData folder
  (`%LOCALAPPDATA%\HHMS\WebView2`), maps the bundled frontend through
  `SetVirtualHostNameToFolderMapping("app.hhms.local", …/frontend)` and
  navigates to `https://app.hhms.local/index.html`.
- **Frontend bundled**: `<Content Include="..\..\frontend\**\*" LinkBase="frontend" CopyToOutputDirectory="PreserveNewest" />`.
- **LAN discovery bridge**: `Bridge/DiscoveryBridge.cs` answers the UDP
  `HHMS_DISCOVER_V1` handshake (same protocol verified server-side in Batch
  104); injected via WebMessageReceived so the web layer calls
  `window.hhms.discovery.discover()` without any native dialog.
- **Version lock-step**: the client's version constant must equal the root
  `VERSION` file (single-source versioning from Batch 105); the backend
  fallback release version is asserted against the same file.

Offline redistributable note: the WebView2 *Evergreen* runtime is probed at
server-launch time (`scripts/deploy/server-launch.ps1`, Batch 105) and the SDK
loader ships inside the single-file EXE; bundling the full offline
redistributable CAB into the installer remains an explicit open item (tracked
in ROADMAP).

## Installer `-IncludeClient` switch

`build-installer.ps1` (Batch 107) gained an opt-in `-IncludeClient` parameter:

- Requires `HHMS-Client.exe` beside the server bundle (`SourceDir`) and fails
  fast with the publish hint if missing.
- Adds the launcher to both generated toolsets — Inno `.iss` `[Files]` entry
  and NSIS `.nsi` `File` line — plus a client Start Menu/desktop shortcut.
- Default builds stay server-only, so existing CI jobs are unaffected.
- The Batch 104 data-survival contract is re-asserted with the option enabled:
  neither toolset may recursively delete the writable data root.

## QA suite

`backend/tests/test_batch108_backup_restore_release_qa.py` — 11 tests:

| Test | Locks in |
|---|---|
| `test_backup_restore_roundtrip_preserves_point_in_time` | create → mutate → restore → post-backup rows gone, pre-backup rows intact |
| `test_restore_leaves_no_pre_restore_snapshot_on_success` | snapshot hygiene in the listing |
| `test_import_rejects_non_sqlite_payload` | corrupt upload refused, backups dir clean |
| `test_download_returns_exact_backup_bytes` | byte-exact download |
| `test_backup_endpoints_require_administrator` | role gating on every verb |
| `test_client_project_publishes_single_self_contained_exe` | csproj publish contract |
| `test_client_pins_webview2_and_bundles_frontend` | exact WebView2 version + frontend content glob |
| `test_client_version_constant_matches_root_version_file` | client/backend ↔ VERSION lock-step |
| `test_installer_script_supports_include_client_switch` | switch present on Inno + NSIS paths |
| `test_installer_still_preserves_data_with_client_option` | data-survival contract with client bundled |
| `test_release_fallback_version_matches_version_file` | fallback version drift guard |

## Fixes surfaced during verification

- Missing `import time` in `backend/tests/test_batch104_multi_client_lan_qa.py`
  (latent NameError once timing assertions executed).
- Missing top-level `import asyncio` in the Batch 108 suite's module scope.

## Suite status

Full backend suite at close: **448 passed, 2 skipped** (437 at Batch 107 + 11
new Batch 108 tests; the 2 skips are the opt-in tier-2 EXE-build tests from
Batch 106).

## Remaining Milestone 7 scope

Performance & security audit pass, documentation/training finalization, WebView2
offline redistributable CAB bundling, production release (gated on secret-key
rotation — `data/secret.key` persists in git history).
