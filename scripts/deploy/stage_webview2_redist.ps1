# ---------------------------------------------------------------------------
# HHMS WebView2 offline redistributable stager — Milestone 7 Batch 112.
#
# Downloads the official Microsoft Edge WebView2 *fixed version* runtime CAB
# into the repo's redist cache so that build-installer.ps1 can bundle a fully
# offline-capable client installer (air-gapped clinic LANs cannot reach
# https://msedge.sf.dl.delivery.mp.microsoft.com at install time).
#
# What this produces (under -RedistDir, default build/redist/webview2):
#   MicrosoftEdgeWebView2Runtime-<version>-x64.cab     (runtime payload)
#   MicrosoftEdgeWebView2Runtime-<version>-x64.cab.sha256
#   EvergreenBootstrapper.exe                          (optional, -IncludeBootstrapper)
#   EvergreenBootstrapper.exe.sha256                   (optional)
#
# The fixed-version CAB is unpacked by Inno Setup/NSIS at install time into
# %LOCALAPPDATA%\Programs\HHMS\WebView2Runtime and registered via the
# EBWebViewEnvOverride / launcher --webview-runtime-folder contract from
# Batch 108 (client/HHMS.Client reads the folder next to HHMS-Client.exe).
#
# Security posture:
#   * Only the two allow-listed Microsoft CDN hosts are accepted.
#   * Transport must be HTTPS.
#   * SHA-256 of every downloaded file is recorded; when -ExpectedSha256 is
#     supplied the download is REJECTED on mismatch (supply-chain gate).
#
# Usage:
#   .\stage_webview2_redist.ps1 -Version 130.0.2848.99
#   .\stage_webview2_redist.ps1 -Version 130.0.2848.99 -IncludeBootstrapper
#   .\stage_webview2_redist.ps1 -Url <full-cab-url> -ExpectedSha256 <hex>
#
# Exit codes: 0 success, 1 invalid arguments, 2 download failure,
#              3 checksum mismatch / host not allowed.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$Version = "",
    [string]$Architecture = "x64",
    [string]$Url = "",
    [string]$ExpectedSha256 = "",
    [switch]$IncludeBootstrapper,
    [string]$RedistDir = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
if ($RedistDir -eq "") { $RedistDir = Join-Path $ProjectRoot "build\redist\webview2" }

# Allow-listed Microsoft download hosts (fixed-version CAB + bootstrapper).
$AllowedHosts = @(
    "msedge.sf.dl.delivery.mp.microsoft.com",
    "go.microsoft.com",
    "download.microsoft.com"
)

function Test-AllowedUrl([string]$TargetUrl) {
    $parsed = [System.Uri]$TargetUrl
    if ($parsed.Scheme -ne "https") { return $false }
    return ($AllowedHosts -contains $parsed.Host.ToLowerInvariant())
}

function Get-Sha256([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

if ($Architecture -notin @("x64", "x86", "arm64")) {
    Write-Host "ERROR: architecture must be x64, x86 or arm64." -ForegroundColor Red
    exit 1
}

# --- resolve the fixed-version CAB URL --------------------------------------
if ($Url -eq "") {
    if ($Version -eq "") {
        Write-Host "ERROR: provide -Version <fixed-runtime-version> or an explicit -Url." -ForegroundColor Red
        Write-Host "       See https://learn.microsoft.com/microsoft-edge/webview2/concepts/downloads" -ForegroundColor Yellow
        exit 1
    }
    # Official fixed-version CAB pattern (Evergreen distribution docs).
    $Url = "https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/" +
           "MicrosoftEdgeWebview2Setup-$Version-$Architecture.cab"
}

if (-not (Test-AllowedUrl $Url)) {
    Write-Host "ERROR: refusing non-HTTPS or non-Microsoft URL: $Url" -ForegroundColor Red
    exit 3
}

New-Item -ItemType Directory -Force -Path $RedistDir | Out-Null

# --- download helper ---------------------------------------------------------
function Save-File([string]$SourceUrl, [string]$DestPath, [string]$Label) {
    Write-Host "==> Downloading $Label`: $SourceUrl"
    try {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            Invoke-WebRequest -Uri $SourceUrl -OutFile $DestPath -UseBasicParsing
        } else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $SourceUrl -OutFile $DestPath -UseBasicParsing
        }
    } catch {
        Write-Host "ERROR: download failed for $Label`: $($_.Exception.Message)" -ForegroundColor Red
        exit 2
    }
    $hash = Get-Sha256 $DestPath
    "$hash  $(Split-Path -Leaf $DestPath)" | Set-Content -Path "$DestPath.sha256" -Encoding ASCII
    Write-Host "    SHA-256: $hash"
    return $hash
}

# --- redist manifest ----------------------------------------------------------
# build-installer.ps1 -Webview2RedistDir requires redist-manifest.json; record
# version/arch/source/sha so the bundle is reproducible and auditable.
function Write-Manifest {
    param([string]$CabPath, [string]$FileHash, [string]$SourceUrl, [string]$RuntimeVersion)
    $m = [ordered]@{
        schema    = "hhms.webview2-redist/1"
        version   = $RuntimeVersion
        architecture = $Architecture
        cab       = Split-Path -Leaf $CabPath
        sha256    = $FileHash
        source_url = $SourceUrl
        staged_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    $manifestPath = Join-Path $RedistDir "redist-manifest.json"
    $m | ConvertTo-Json | Set-Content -Path $manifestPath -Encoding ASCII
    Write-Host "==> Manifest written: $manifestPath"
}

$cabName = "MicrosoftEdgeWebView2Runtime-$Version-$Architecture.cab"
if ($Version -eq "") { $cabName = Split-Path -Leaf ([System.Uri]$Url).AbsolutePath }
$cabPath = Join-Path $RedistDir $cabName

$cabHash = Save-File $Url $cabPath "fixed-version CAB"
if ($ExpectedSha256 -ne "") {
    if ($cabHash -ne $ExpectedSha256.ToLowerInvariant()) {
        Remove-Item $cabPath -Force
        Remove-Item "$cabPath.sha256" -Force
        Write-Host "ERROR: CAB checksum mismatch — expected $ExpectedSha256, got $cabHash" -ForegroundColor Red
        Write-Host "       File removed. Supply chain gate FAILED; nothing staged." -ForegroundColor Yellow
        exit 3
    }
    Write-Host "==> Checksum matches expected value."
}

$rtVersion = if ($Version -ne "") { $Version } else { "unknown" }
Write-Manifest -CabPath $cabPath -FileHash $cabHash -SourceUrl $Url -RuntimeVersion $rtVersion

if ($IncludeBootstrapper) {
    $bootUrl = "https://go.microsoft.com/fwlink/p/?linkid=2124701&arch=$Architecture"
    if (-not (Test-AllowedUrl $bootUrl)) { Write-Host "ERROR: bootstrapper URL not allowed." -ForegroundColor Red; exit 3 }
    $bootPath = Join-Path $RedistDir "EvergreenBootstrapper.exe"
    Save-File $bootUrl $bootPath "evergreen bootstrapper" | Out-Null
}

Write-Host ""
Write-Host "==> WebView2 redist staged in: $RedistDir"
Write-Host "    Bundle it with: .\build-installer.ps1 -IncludeClient -Webview2RedistDir `"$RedistDir`""
exit 0
