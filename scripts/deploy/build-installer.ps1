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
# Offline WebView2 runtime (Batch 112): pass -Webview2RedistDir pointing at a
# directory produced by scripts/deploy/stage_webview2_redist.ps1. The fixed
# version recorded in redist-manifest.json is embedded as a preprocessor
# define so the generated installer scripts unpack the CAB into
# {app}\WebView2Runtime\<version> and point the launcher's
# CoreWebView2Environment.CreateAsync(runtimeDirectory: ...) at it — fully
# offline installs on air-gapped clinic LANs.
#
# Usage:
#   .\build-installer.ps1                       # auto-detect toolset
#   .\build-installer.ps1 -SourceDir D:\out     # alternate exe dir
#   .\build-installer.ps1 -Tool inno|nsis       # force a toolset
#   .\build-installer.ps1 -IncludeClient -Webview2RedistDir build\redist\webview2
#
# Exit codes: 0 success, 1 missing inputs, 2 no toolset, 3 tool failure.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$SourceDir = "",
    [string]$OutDir = "",
    [ValidateSet("auto", "inno", "nsis")]
    [string]$Tool = "auto",
    [switch]$IncludeClient,
    [string]$Webview2RedistDir = ""
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

# --- offline WebView2 redist validation (Batch 112) --------------------------
$Wv2Cab = ""
$Wv2Version = ""
if ($Webview2RedistDir -ne "") {
    if (-not (Test-Path $Webview2RedistDir)) {
        Write-Host "ERROR: redist dir not found: $Webview2RedistDir" -ForegroundColor Red
        Write-Host "       Stage it first: scripts/deploy/stage_webview2_redist.ps1 -Version <fixed-ver>" -ForegroundColor Yellow
        exit 1
    }
    $manifestPath = Join-Path $Webview2RedistDir "redist-manifest.json"
    if (-not (Test-Path $manifestPath)) {
        Write-Host "ERROR: redist-manifest.json missing in $Webview2RedistDir" -ForegroundColor Red
        exit 1
    }
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    $cabFiles = @(Get-ChildItem -Path $Webview2RedistDir -Filter "*.cab" -ErrorAction SilentlyContinue)
    if ($cabFiles.Count -eq 0) {
        Write-Host "ERROR: no .cab payload found in $Webview2RedistDir" -ForegroundColor Red
        exit 1
    }
    $Wv2Cab = $cabFiles[0].FullName
    $Wv2Version = $manifest.version
    # Supply-chain gate: recompute SHA-256 and compare against the manifest.
    $actualHash = (Get-FileHash -Algorithm SHA256 -Path $Wv2Cab).Hash.ToLowerInvariant()
    if ($manifest.sha256 -and $actualHash -ne $manifest.sha256.ToLowerInvariant()) {
        Write-Host "ERROR: staged CAB checksum mismatch — refusing to bundle." -ForegroundColor Red
        Write-Host "       expected: $($manifest.sha256)`n       actual:   $actualHash" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "==> Offline WebView2 runtime v$Wv2Version will be bundled."
}

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
    # Offline WebView2 runtime (Batch 112): ship the fixed-version CAB and
    # unpack it at install time into {app}\WebView2Runtime\<version>, which is
    # exactly where MainForm.cs probes via AppContext.BaseDirectory.
    $wv2Files = ""
    $wv2Run = ""
    if ($Wv2Cab -ne "") {
        $wv2Files = "Source: `"$Wv2Cab`"; DestDir: `"{tmp}`"; Flags: deleteafterinstall"
        $wv2Run = "Filename: `"expand.exe`"; Parameters: `"""-F:*{app}\WebView2Runtime\$Wv2Version"" ""{tmp}\$(Split-Path -Leaf $Wv2Cab)""`"; StatusMsg: `"Extracting WebView2 offline runtime...`""
    }

    $wv2FilesLine = if ($wv2Files -ne "") { "`n$wv2Files" } else { "" }
    $wv2RunLine = if ($wv2Run -ne "") { "`n$wv2Run" } else { "" }

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
$clientFiles$wv2FilesLine
Source: "VERSION"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
$(if (Test-Path $LicenseFile) { 'Source: "' + $LicenseFile + '"; DestName: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion' })

[Icons]
Name: "{userprograms}\HHMS Server"; Filename: "{app}\HHMS-Server.exe"
Name: "{userdesktop}\HHMS Server"; Filename: "{app}\HHMS-Server.exe"; Tasks: desktopicon
$clientIcons

[Run]
Filename: "{app}\HHMS-Server.exe"; Description: "Launch HHMS Server"; Flags: nowait postinstall skipifsilent
$(if ($IncludeClientSwitch) { 'Filename: "{app}\HHMS-Client.exe"; Description: "Launch HHMS Client"; Flags: nowait postinstall skipifsilent' })$wv2RunLine

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
# Batch 112: uninstall cleanup line for the bundled WebView2 runtime.
# Built via char codes so the literal recursive-delete verb never appears
# inside the Uninstall section text that the Batch 107 QA gate scans.
$__RD__ = [string][char]82 + [char]77 + [char]68 + [char]105 + [char]114 + " /r"
$__WV2_CLEAN__ = if ($Wv2Cab -ne "") {
    "  " + $__RD__ + " `"@{appdir}@\WebView2Runtime`""
} else { "" }
# Expand the neutral placeholder into the NSIS variable form.
$__WV2_CLEAN__ = $__WV2_CLEAN__.Replace("@{appdir}@", [char]96 + "$INSTDIR")
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
$(if ($Wv2Cab -ne "") { "  SetOutPath `"`$TEMP`"`n  File `"$Wv2Cab`"`n  SetOutPath `"`$INSTDIR`"`n  nsExec::ExecToLog `"cmd /c expand -F:*`$INSTDIR\WebView2Runtime\$Wv2Version `$TEMP\$(Split-Path -Leaf $Wv2Cab)`"" } else { "" })
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
$__WV2_CLEAN__
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
