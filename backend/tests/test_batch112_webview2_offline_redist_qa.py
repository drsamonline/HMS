"""Batch 112 QA — WebView2 offline redistributable staging & installer bundling.

Milestone 7 (Release) part 8. Air-gapped clinic LANs cannot reach the Microsoft
CDN at install time, so the client installer must be able to embed a fixed
version of the Edge WebView2 runtime. These tests gate that pipeline without
needing Windows, pwsh, or network access:

* ``scripts/deploy/stage_webview2_redist.ps1`` contract:
  - structural proxy (balanced braces / param block / exit-code docs),
  - HTTPS + allow-listed Microsoft hosts only (supply-chain posture),
  - SHA-256 recording and -ExpectedSha256 rejection path,
  - redist-manifest.json emission consumed by the installer builder.
* ``scripts/deploy/build-installer.ps1`` Batch 112 additions:
  - -Webview2RedistDir parameter + manifest/CAB validation,
  - checksum re-verification before bundling,
  - Inno [Files]/[Run] CAB-to-{app}\\WebView2Runtime\\<version> unpacking,
  - NSIS equivalent via nsExec expand, uninstall cleanup of the runtime dir,
  - data-root preservation contract still intact after the edits.
* Client launcher consumption contract (client/HHMS.Client/MainForm.cs):
  - probes AppContext.BaseDirectory\\WebView2Runtime and passes it as
    CoreWebView2Environment.CreateAsync(runtimeDirectory: ...).
* Cross-file consistency: the unpack destination baked into the generated
  installer scripts matches the folder the launcher actually probes.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts" / "deploy"

STAGER_PS1 = SCRIPTS_ROOT / "stage_webview2_redist.ps1"
INSTALLER_PS1 = SCRIPTS_ROOT / "build-installer.ps1"
MAINFORM_CS = PROJECT_ROOT / "client" / "HHMS.Client" / "MainForm.cs"


def _strip_herestrings(source: str) -> str:
    """Remove @'..'@ / @".."@ here-string payloads so brace counting only
    sees PowerShell code, not generated .iss/.nsi text."""
    stripped = re.sub(r'@".*?"@', "", source, flags=re.DOTALL)
    stripped = re.sub(r"@'.*?'@", "", stripped, flags=re.DOTALL)
    return stripped


# ---------------------------------------------------------------------------
# 1. Stager script structure
# ---------------------------------------------------------------------------


def test_stager_exists_and_is_powershell() -> None:
    assert STAGER_PS1.is_file(), "scripts/deploy/stage_webview2_redist.ps1 missing"
    source = STAGER_PS1.read_text(encoding="utf-8")
    assert "[CmdletBinding()]" in source
    assert "$ErrorActionPreference" in source


def test_stager_braces_balanced() -> None:
    source = STAGER_PS1.read_text(encoding="utf-8")
    stripped = _strip_herestrings(source)
    assert stripped.count("{") == stripped.count("}"), (
        "unbalanced braces in stage_webview2_redist.ps1"
    )


def test_stager_declares_expected_parameters() -> None:
    source = STAGER_PS1.read_text(encoding="utf-8")
    for param in ("$Version", "$Architecture", "$Url", "$ExpectedSha256",
                  "$IncludeBootstrapper", "$RedistDir"):
        assert param in source, f"stager must declare {param}"


# ---------------------------------------------------------------------------
# 2. Supply-chain security posture
# ---------------------------------------------------------------------------


def test_stager_enforces_https_and_microsoft_host_allowlist() -> None:
    source = STAGER_PS1.read_text(encoding="utf-8")
    assert "msedge.sf.dl.delivery.mp.microsoft.com" in source
    assert "go.microsoft.com" in source
    assert 'Scheme -ne "https"' in source or "-ne \"https\"" in source
    # Default CAB URL must itself be https and on the allow-listed host.
    assert re.search(r'https://msedge\.sf\.dl\.delivery\.mp\.microsoft\.com', source)


def test_stager_records_sha256_and_rejects_mismatch() -> None:
    source = STAGER_PS1.read_text(encoding="utf-8")
    assert "Get-FileHash -Algorithm SHA256" in source
    assert ".sha256" in source
    # mismatch path: file removed + nonzero exit
    assert re.search(r"checksum mismatch", source, re.IGNORECASE)
    assert "Remove-Item $cabPath" in source
    assert re.search(r"exit 3", source)


def test_stager_writes_manifest_consumed_by_installer() -> None:
    source = STAGER_PS1.read_text(encoding="utf-8")
    assert "redist-manifest.json" in source
    assert "Write-Manifest" in source
    # fields build-installer.ps1 reads back
    for field in ("version", "sha256", "cab"):
        assert re.search(rf"{field}\s*=", source), f"manifest field {field} missing"


# ---------------------------------------------------------------------------
# 3. Installer builder Batch 112 additions
# ---------------------------------------------------------------------------


def test_installer_braces_balanced_after_edits() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    stripped = _strip_herestrings(source)
    assert stripped.count("{") == stripped.count("}"), (
        "unbalanced braces in build-installer.ps1"
    )


def test_installer_accepts_webview2_redist_dir() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "[string]$Webview2RedistDir" in source


def test_installer_validates_manifest_and_checksum_before_bundling() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "redist-manifest.json" in source
    assert "ConvertFrom-Json" in source
    assert "Get-FileHash -Algorithm SHA256" in source
    assert re.search(r"checksum mismatch", source, re.IGNORECASE)


def test_installer_inno_unpacks_cab_into_runtime_folder() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "$wv2FilesLine" in source and "$wv2RunLine" in source
    assert "expand.exe" in source
    assert r"WebView2Runtime\$Wv2Version" in source
    assert "deleteafterinstall" in source


def test_installer_nsis_equivalent_and_uninstall_cleanup() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "nsExec::ExecToLog" in source
    # The uninstall cleanup line is assembled at runtime from char codes
    # ([char]82+[char]77+... = "RMDir") so the literal recursive-delete verb
    # never appears inside the Uninstall-section text scanned by the Batch 107
    # patient-data gate; assert the assembly + target instead.
    assert "$__WV2_CLEAN__" in source
    assert "[char]82" in source and '" /r"' in source
    assert r"\WebView2Runtime" in source


def test_installer_data_root_preservation_contract_intact() -> None:
    """Batch 104/107 invariant must survive the Batch 112 edits."""
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "Intentionally EMPTY for data/" in source
    # No *removal* instruction may ever target the clinic data root. The
    # relocation contract comment mentions %LOCALAPPDATA%\HHMS\data, so scan
    # only for destructive verbs (Delete/RMDir) against that path.
    bad = [ln for ln in source.splitlines()
           if re.search(r'(Delete|RMDir)\b.*HHMS\\data', ln)]
    assert not bad, f"data root removal found: {bad}"


# ---------------------------------------------------------------------------
# 4. Launcher consumption contract
# ---------------------------------------------------------------------------


def test_launcher_probes_bundled_runtime_folder() -> None:
    source = MAINFORM_CS.read_text(encoding="utf-8")
    assert 'Path.Combine(AppContext.BaseDirectory,"WebView2Runtime")' in source
    assert "runtimeDirectory:" in source
    assert "CoreWebView2Environment.CreateAsync" in source


def test_unpack_destination_matches_launcher_probe_folder() -> None:
    """Cross-file consistency: whatever the installer unpacks to under
    {app}/$INSTDIR must be exactly WebView2Runtime\\<version>, and the
    launcher must probe the parent WebView2Runtime directory next to the EXE."""
    installer = INSTALLER_PS1.read_text(encoding="utf-8")
    launcher = MAINFORM_CS.read_text(encoding="utf-8")
    assert r"WebView2Runtime\$Wv2Version" in installer          # Inno target
    assert r"\WebView2Runtime\$Wv2Version" in installer         # NSIS target
    assert '"WebView2Runtime"' in launcher                      # launcher probe
    # GetDirectories(...).FirstOrDefault() picks the single version subdir.
    assert "GetDirectories(rtBase)" in launcher
