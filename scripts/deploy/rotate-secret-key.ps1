# ---------------------------------------------------------------------------
# HHMS JWT secret-key rotation utility — Batch 115.
#
# Rotates the persisted signing secret (data/secret.key) on a deployed
# runtime root. All previously issued access tokens become invalid
# immediately; every client must log in again after rotation.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\deploy\rotate-secret-key.ps1 `
#       [-RuntimeRoot <path>] [-WhatIf]
#
# -RuntimeRoot defaults to the repository root (the directory two levels
# above this script). Pass the installed runtime root for packaged
# deployments (e.g. C:\Program Files\HHMS or the data root used by
# server-launch.ps1).
#
# Behaviour (mirrors docs/SECRET_ROTATION_RUNBOOK.md):
#   1. Verifies the runtime data directory exists.
#   2. Backs up the current secret.key to secret.key.bak-<UTCtimestamp>.
#   3. Generates a fresh 48-byte url-safe random key (same format the
#      server's _load_or_create_secret_key() produces).
#   4. Writes it atomically and applies owner-only read/write permissions.
#   5. Prints the fingerprint (SHA-256, first 12 hex chars) of the new key
#      so operators can confirm rotation without exposing the secret.
# ---------------------------------------------------------------------------
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RuntimeRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $RuntimeRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RuntimeRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
}

$dataDir = Join-Path $RuntimeRoot "data"
$keyPath = Join-Path $dataDir "secret.key"

if (-not (Test-Path $dataDir)) {
    throw "Runtime data directory not found: $dataDir (pass -RuntimeRoot)"
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$backupPath = "$keyPath.bak-$stamp"

if (Test-Path $keyPath) {
    if ($PSCmdlet.ShouldProcess($keyPath, "back up before rotation")) {
        Copy-Item -Path $keyPath -Destination $backupPath -Force
        Write-Host "==> Previous secret backed up to $backupPath"
    }
} else {
    Write-Host "==> No existing secret.key found; a fresh one will be created."
}

if ($PSCmdlet.ShouldProcess($keyPath, "rotate")) {
    # 48 random bytes, base64url — identical format to Python's
    # secrets.token_urlsafe(48).
    $bytes = New-Object byte[] 48
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')

    $tmpPath = "$keyPath.tmp-$PID"
    Set-Content -Path $tmpPath -Value $token -Encoding ASCII -NoNewline
    Move-Item -Path $tmpPath -Destination $keyPath -Force

    # Owner-only ACL: strip inherited access, grant current user RW only.
    try {
        $acl = Get-Acl $keyPath
        $acl.SetAccessRuleProtection($true, $false)
        $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $identity, "Modify", "Allow")
        $acl.SetAccessRule($rule)
        Set-Acl -Path $keyPath -AclObject $acl
    } catch {
        Write-Warning "Could not tighten ACLs on $keyPath`: $_"
    }

    $sha = (Get-FileHash -Algorithm SHA256 -Path $keyPath).Hash
    Write-Host "==> Secret rotated. New key fingerprint: $($sha.Substring(0, 12))"
    Write-Host "==> All existing access tokens are now invalid; clients must re-login."
}
