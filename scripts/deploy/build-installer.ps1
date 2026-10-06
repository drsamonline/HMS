# ---------------------------------------------------------------------------
# HHMS Windows installer builder — Milestone 7 Batch 107.
#
# Packages the PyInstaller one-file server bundle (build/dist/HHMS-Server.exe,
# produced by CI or by scripts/deploy/build-server.sh on that platform) into a
# distributable installer using whichever toolset is available:
#
#   1. Inno Setup 6  (iscc.exe)     -> dist/installer/HHMS-Setup-<version>.exe
#   2. NSIS fallback (makensis.exe) -> dist/installer/HHMS-Setup-<version>.exe
#
# The generated Inno script installs to %LOCALAPPDATA%\Programs\HHMS, creates
# Start Menu shortcuts, registers an uninstall entry, and — critically — never
# touches the writable data root (%LOCALAPPDATA%\HHMS\data), so upgrades and
# uninstalls preserve the clinic database, mirroring the prepare_runtime()
# relocation contract from Batch 104/105.
#
# Usage:
#   .\build-installer.ps1                       # auto-detect toolset
#   .\build-installer.ps1 -SourceDir D:\out     # alternate exe dir
#   .\build-installer.ps1 -Tool inno|nsis       # force a toolset
#
# Exit codes: 0 success, 1 missing inputs, 2 no toolset, 3 tool failure.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$SourceDir = "",
    [string]$OutDir = "",
    [ValidateSet("auto", "inno", "nsis")]
    [string]$Tool = "auto",
    [switch]$IncludeClient
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

if ($SourceDir -eq "") { $SourceDir = Join-Path $ProjectRoot "build\dist" }
if ($OutDir -eq "")    { $OutDir = Join-Path $ProjectRoot "dist\installer" }

$ServerExe = Join-Path $SourceDir "HHMS-Server.exe"
$ClientExe = Join-Path $SourceDir "HHMS-Client.exe"
$WebView2BootStrapper = Join-Path $SourceDir "Microsoft.Web.WebView2.Core.dll"
$VersionFile = Join-Path $ProjectRoot "VERSION"
$LicenseFile = Join-Path $ProjectRoot "LICENSE"

if (-not (Test-Path $ServerExe)) {
    Write-Host "ERROR: server executable not found: $ServerExe" -ForegroundColor Red
    Write-Host "       Build it first (scripts/deploy/build-server.sh on POSIX," -ForegroundColor Yellow
    Write-Host "       or the windows PyInstaller job in .github/workflows/release.yml)." -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $VersionFile)) {
    Write-Host "ERROR: VERSION file not found at repo root." -ForegroundColor Red
    exit 1
}

# Client launcher is optional per-invocation (Batch 108): pass -IncludeClient
# to require and bundle HHMS-Client.exe from the same source dir.
$IncludeClientSwitch = if ($IncludeClient) { $true } else { $false }
if ($IncludeClientSwitch) {
    if (-not (Test-Path $ClientExe)) {
        Write-Host "ERROR: client executable not found: $ClientExe" -ForegroundColor Red
        Write-Host "       Publish it first: dotnet publish client/HHMS.Client -c Release" -ForegroundColor Yellow
        exit 1
    }
    # WebView2 SDK assemblies shipped next to the launcher (fixed-runtime
    # style; the Evergreen loader falls back to the system runtime).
    $HasWebView2RuntimeFiles = Test-Path $WebView2BootStrapper
} else {
    $HasWebView2RuntimeFiles = $false
}

$Version = (Get-Content $VersionFile -Raw).Trim()
Write-Host "==> Packaging HHMS Server v$Version"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "build\installer") | Out-Null

# --- tool discovery ---------------------------------------------------------
function Find-InnoCompiler {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    $cmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-Makensis {
    $cmd = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = "$env:ProgramFiles\NSIS\makensis.exe"
    if (Test-Path $fallback) { return $fallback }
    return $null
}

$Inno = Find-InnoCompiler
$Nsis = Find-Makensis

$selected = $Tool
if ($selected -eq "auto") {
    if ($Inno) { $selected = "inno" }
    elseif ($Nsis) { $selected = "nsis" }
    else {
        Write-Host "ERROR: neither Inno Setup 6 (iscc.exe) nor NSIS (makensis.exe) found." -ForegroundColor Red
        Write-Host "       Install one, e.g.: choco install innosetup -y" -ForegroundColor Yellow
        exit 2
    }
}

# --- Inno Setup path --------------------------------------------------------
if ($selected -eq "inno") {
    if (-not $Inno) { Write-Host "ERROR: Inno Setup requested but iscc.exe not found." -ForegroundColor Red; exit 2 }

    $issPath = Join-Path $ProjectRoot "build\installer\HHMS-Setup.iss"
    $license = if (Test-Path $LicenseFile) { $LicenseFile } else { '""' }

    $clientFiles = ""
    $clientIcons = ""
    if ($IncludeClientSwitch) {
        $clientFiles = 'Source: "HHMS-Client.exe"; DestDir: "{app}"; Flags: ignoreversion'
        if ($HasWebView2RuntimeFiles) {
            $clientFiles += "`nSource: `"Microsoft.Web.WebView2.*`"; DestDir: `"{app}`"; Flags: ignoreversion"
        }
        $clientIcons = 'Name: "{userprograms}\HHMS Client"; Filename: "{app}\HHMS-Client.exe"' + "`n" +
                        'Name: "{userdesktop}\HHMS Client"; Filename: "{app}\HHMS-Client.exe"; Tasks: desktopicon'
    }

    $iss = @"
; Auto-generated by scripts/deploy/build-installer.ps1 — do not edit by hand.
[Setup]
AppName=HHMS Server
AppVersion=$Version
AppPublisher=HHMS
DefaultDirName={localappdata}\Programs\HHMS
DisableProgramGroupPage=yes
OutputDir=$OutDir
OutputBaseFilename=HHMS-Setup-$Version
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=HHMS Server $Version
PrivilegesRequired=lowest
SourceDir=$SourceDir

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "HHMS-Server.exe"; DestDir: "{app}"; Flags: ignoreversion
$clientFiles
Source: "VERSION"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
$(if (Test-Path $LicenseFile) { 'Source: "' + $LicenseFile + '"; DestName: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion' })

[Icons]
Name: "{userprograms}\HHMS Server"; Filename: "{app}\HHMS-Server.exe"
Name: "{userdesktop}\HHMS Server"; Filename: "{app}\HHMS-Server.exe"; Tasks: desktopicon
$clientIcons

[Run]
Filename: "{app}\HHMS-Server.exe"; Description: "Launch HHMS Server"; Flags: nowait postinstall skipifsilent
$(if ($IncludeClientSwitch) { 'Filename: "{app}\HHMS-Client.exe"; Description: "Launch HHMS Client"; Flags: nowait postinstall skipifsilent' })

[UninstallDelete]
; Intentionally EMPTY for data/: the clinic database lives under
; %LOCALAPPDATA%\HHMS\data and must survive uninstall (Batch 104 contract).
"@
    Set-Content -Path $issPath -Value $iss -Encoding UTF8

    Write-Host "==> Compiling installer with Inno Setup: $Inno"
    & $Inno $issPath
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: iscc failed ($LASTEXITCODE)" -ForegroundColor Red; exit 3 }

    $artifact = Join-Path $OutDir "HHMS-Setup-$Version.exe"
    if (-not (Test-Path $artifact)) { Write-Host "ERROR: expected artifact missing: $artifact" -ForegroundColor Red; exit 3 }
    Write-Host "==> Installer created: $artifact"
    exit 0
}

# --- NSIS fallback ------------------------------------------------------------
if (-not $Nsis) { Write-Host "ERROR: NSIS requested but makensis.exe not found." -ForegroundColor Red; exit 2 }

$nsiPath = Join-Path $ProjectRoot "build\installer\HHMS-Setup.nsi"
$nsi = @"
; Auto-generated by scripts/deploy/build-installer.ps1 — do not edit by hand.
Unicode true
!define APPNAME "HHMS Server"
!define VERSION "$Version"
Name "`${APPNAME}"
OutFile "$OutDir\HHMS-Setup-`$Version.exe"
InstallDir "`$LOCALAPPDATA\Programs\HHMS"
RequestExecutionLevel user

Page directory
Page instfiles

Section "Install"
  SetOutPath "`$INSTDIR"
  File "$SourceDir\HHMS-Server.exe"
$(if ($IncludeClientSwitch) { "  File `"$SourceDir\HHMS-Client.exe`"" + $(if ($HasWebView2RuntimeFiles) { "`n  File `"$SourceDir\Microsoft.Web.WebView2.*`"" }) })
  File /oname=LICENSE.txt "$LicenseFile"
  CreateDirectory "`$SMPROGRAMS\HHMS"
  CreateShortCut "`$SMPROGRAMS\HHMS\HHMS Server.lnk" "`$INSTDIR\HHMS-Server.exe"
$(if ($IncludeClientSwitch) { '  CreateShortCut "$SMPROGRAMS\HHMS\HHMS Client.lnk" "$INSTDIR\HHMS-Client.exe"' })
  WriteUninstaller "`$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HHMS" "DisplayName" "`${APPNAME} `${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HHMS" "UninstallString" "`$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "`$INSTDIR\HHMS-Server.exe"
$(if ($IncludeClientSwitch) { '  Delete "$INSTDIR\HHMS-Client.exe"' + $(if ($HasWebView2RuntimeFiles) { "`n  Delete `"$INSTDIR\Microsoft.Web.WebView2.*`"" }) })
  Delete "`$INSTDIR\LICENSE.txt"
  Delete "`$INSTDIR\uninstall.exe"
  RMDir "`$INSTDIR"
  Delete "`$SMPROGRAMS\HHMS\HHMS Server.lnk"
$(if ($IncludeClientSwitch) { '  Delete "$SMPROGRAMS\HHMS\HHMS Client.lnk"' })
  RMDir "`$SMPROGRAMS\HHMS"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HHMS"
  ; NOTE: `%LOCALAPPDATA%\HHMS\data` intentionally NOT removed — patient
  ; data survives uninstall (Batch 104 relocation contract).
SectionEnd
"@
Set-Content -Path $nsiPath -Value $nsi -Encoding UTF8

Write-Host "==> Compiling installer with NSIS: $Nsis"
& $Nsis /V2 $nsiPath
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: makensis failed ($LASTEXITCODE)" -ForegroundColor Red; exit 3 }

$artifact = Join-Path $OutDir "HHMS-Setup-$Version.exe"
if (-not (Test-Path $artifact)) { Write-Host "ERROR: expected artifact missing: $artifact" -ForegroundColor Red; exit 3 }
Write-Host "==> Installer created: $artifact"
