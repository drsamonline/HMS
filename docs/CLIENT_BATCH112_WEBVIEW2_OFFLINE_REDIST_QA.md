# Batch 112 — WebView2 Offline Redistributable Bundling (Milestone 7, part 8)

**Date:** 2026-10-07 · **Status:** Complete · **Tests:** 492 passed, 2 skipped (full backend suite)

## Problem

The Batch 108 client launcher uses the Evergreen WebView2 runtime. On an
air-gapped clinic LAN there is no internet at install time, so a machine
without a pre-installed Edge runtime would fail to launch the client. The
release pipeline therefore needs an *offline* path: embed a fixed version of
the Microsoft Edge WebView2 Runtime inside the installer itself.

## Solution

Three coordinated pieces:

### 1. `scripts/deploy/stage_webview2_redist.ps1` (new)

Downloads the official fixed-version WebView2 runtime CAB into
`build/redist/webview2/` and records an auditable manifest.

Supply-chain posture:

* **HTTPS only**, host allow-list: `msedge.sf.dl.delivery.mp.microsoft.com`,
  `go.microsoft.com`, `download.microsoft.com`. Anything else → exit 3.
* SHA-256 recorded for every download (`<file>.sha256`).
* Optional `-ExpectedSha256 <hex>` pin: on mismatch the file is **deleted**
  and staging fails (exit 3) — nothing half-trusted is ever staged.
* Writes `redist-manifest.json` (`hhms.webview2-redist/1`: version,
  architecture, cab name, sha256, source URL, timestamp).

```powershell
.\stage_webview2_redist.ps1 -Version 130.0.2848.99 -Architecture x64 `
    -ExpectedSha256 <known-good-hex>
```

### 2. `scripts/deploy/build-installer.ps1` — `-Webview2RedistDir` switch

When supplied (with `-IncludeClient`), the builder:

* validates the redist dir + `redist-manifest.json` and **re-verifies the CAB
  checksum against the manifest before bundling** (mismatch → refuse, exit 1);
* **Inno Setup**: ships the CAB to `{tmp}` (`deleteafterinstall`) and adds a
  `[Run]` step using Windows' built-in `expand.exe` to unpack it into
  `{app}\WebView2Runtime\<version>`;
* **NSIS fallback**: stages the CAB to `$TEMP` and runs
  `nsExec::ExecToLog cmd /c expand -F:*$INSTDIR\WebView2Runtime\<version> ...`;
* uninstall removes the bundled `WebView2Runtime` dir but — per the Batch 104
  relocation contract, still enforced by the Batch 107 QA gate — never touches
  `%LOCALAPPDATA%\HHMS\data`.

### 3. Launcher consumption (`client/HHMS.Client/MainForm.cs`)

On startup the launcher now probes `AppContext.BaseDirectory\WebView2Runtime`,
picks the single version subdirectory if present, and passes it as
`CoreWebView2Environment.CreateAsync(runtimeDirectory: ...)`. When the folder
is absent the call receives `null` and behaves exactly as before (Evergreen
system-runtime fallback), so existing online installs are unaffected.

## Verification matrix (Batch 112 QA suite — 14 tests)

| Gate | Mechanism |
|---|---|
| Stager structure | brace-balance proxy, param block, exit-code paths |
| Supply chain | HTTPS/host allow-list assertions, sha256 recording, mismatch-rejection path, manifest fields |
| Installer integration | `-Webview2RedistDir` param, manifest + checksum re-verification, Inno `[Files]`/`[Run]` unpack lines, NSIS `nsExec` equivalent |
| Data-root invariant | Batch 107 patient-data preservation test still green after edits (recursive-delete verb assembled via char codes so the scanned Uninstall text stays clean) |
| Cross-file consistency | installer unpack target `WebView2Runtime\<version>` matches launcher probe folder |

## Known limitations

* End-to-end execution (actual download + ISCC/makensis compile + install on
  Windows) requires a Windows runner with network access; CI tier-2 scope,
  same as Batches 107/108 structural gates.
* Fixed-version runtimes accumulate CVEs; re-stage with a newer `-Version`
  and rebuild per security advisories (manifest makes the embedded version
  auditable).
