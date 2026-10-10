# ---------------------------------------------------------------------------
# HHMS Windows server launcher — Milestone 7 Batch 105.
#
# Launches the packaged HHMS-Server executable (or the source entry point
# when no bundle is present), mirroring the prepare_runtime() contract:
#   - relocates the writable data root via HHMS_APPLICATION_ROOT when the
#     -DataRoot parameter is supplied,
#   - waits for GET /api/v1/health to answer before exiting successfully,
#   - verifies the reported version matches the bundled VERSION file.
#
# Usage:
#   .\server-launch.ps1                          # auto-detect bundle/source
#   .\server-launch.ps1 -DataRoot D:\HHMSData    # external data directory
#   .\server-launch.ps1 -Port 8000 -WaitForHealth
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$DataRoot = "",
    [int]$Port = 8000,
    [string]$Host_ = "127.0.0.1",
    [switch]$WaitForHealth
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

if ($DataRoot -ne "") {
    $env:HHMS_APPLICATION_ROOT = $DataRoot
    New-Item -ItemType Directory -Force -Path (Join-Path $DataRoot "data") | Out-Null
}

$BundleExe = Join-Path $ProjectRoot "build\dist\HHMS-Server\HHMS-Server.exe"
if (Test-Path $BundleExe) {
    Write-Host "==> Starting packaged HHMS server: $BundleExe"
    Start-Process -FilePath $BundleExe -WindowStyle Minimized
} else {
    Write-Host "==> Starting HHMS server from source (backend/app/server.py)"
    Push-Location (Join-Path $ProjectRoot "backend")
    try {
        Start-Process -FilePath "python" -ArgumentList "-m","app.server" -WindowStyle Minimized
    } finally {
        Pop-Location
    }
}

if (-not $WaitForHealth) {
    Write-Host "==> HHMS server launched."
    exit 0
}

$HealthUrl = "http://${Host_}:${Port}/api/v1/health"
Write-Host "==> Waiting for health at $HealthUrl"
$deadline = (Get-Date).AddSeconds(30)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
        $healthy = $true
        break
    } catch {
        Start-Sleep -Milliseconds 1000
    }
}

if (-not $healthy) {
    Write-Error "HHMS server did not become healthy within 30 seconds."
    exit 1
}

$VersionFile = Join-Path $ProjectRoot "VERSION"
if (Test-Path $VersionFile) {
    $expected = (Get-Content $VersionFile -Raw).Trim()
    if ($resp.version -ne $expected) {
        Write-Error "Version mismatch: server reports $($resp.version), VERSION file says $expected"
        exit 1
    }
    Write-Host "==> HHMS v$($resp.version) is healthy (version handshake OK)."
} else {
    Write-Host "==> HHMS server is healthy (version $($resp.version))."
}
exit 0
