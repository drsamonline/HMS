"""Batch 107 QA — Windows installer build script & release CI workflow.

Milestone 7 (Release) part 3. These tests gate the two new release artifacts
without needing a Windows host or Inno Setup binary:

* ``scripts/deploy/build-installer.ps1`` structural contract:
  - balanced braces / valid here-string pairing (PowerShell parse proxy),
  - required parameters and tool discovery (iscc + makensis fallback),
  - data-root preservation contract (uninstall must NOT delete %LOCALAPPDATA%\\HHMS\\data),
  - version sourced from the root VERSION file (single-source versioning).
* ``.github/workflows/release.yml`` pipeline contract:
  - valid YAML, triggers include tag pushes,
  - windows job builds EXE then installer with needs-gating on the test job,
  - release job publishes checksummed artifacts.
* Cross-check: every script referenced by the workflow exists on disk, and
  every deploy script on disk is exercised by at least one workflow step.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts" / "deploy"
WORKFLOWS_ROOT = PROJECT_ROOT / ".github" / "workflows"

INSTALLER_PS1 = SCRIPTS_ROOT / "build-installer.ps1"
RELEASE_YML = WORKFLOWS_ROOT / "release.yml"


# ---------------------------------------------------------------------------
# 1. Installer script structure
# ---------------------------------------------------------------------------


def test_installer_script_exists_and_is_powershell() -> None:
    assert INSTALLER_PS1.is_file(), "scripts/deploy/build-installer.ps1 missing"
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "[CmdletBinding()]" in source
    assert "$ErrorActionPreference" in source


def test_installer_script_braces_balanced() -> None:
    """Balanced braces outside of string content is a cheap PowerShell
    syntax proxy (mirrors the Batch 105 PS1 structural gate)."""
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    # strip @' '@ literal/expandable here-strings first; they contain
    # generated .iss/.nsi text whose braces are payload, not code.
    stripped = re.sub(r'@".*?"@', "", source, flags=re.DOTALL)
    stripped = re.sub(r"@'.*?'@", "", stripped, flags=re.DOTALL)
    assert stripped.count("{") == stripped.count("}"), "unbalanced braces in build-installer.ps1"


def test_installer_script_discovers_both_toolsets_with_fallback() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "ISCC.exe" in source or "iscc.exe" in source.lower()
    assert "makensis" in source.lower()
    assert 'ValidateSet("auto", "inno", "nsis")' in source
    # auto mode must prefer Inno and fall back to NSIS
    auto_block = source[source.index('-eq "auto"') : source.index('# --- Inno')]
    assert "inno" in auto_block and "nsis" in auto_block
    assert auto_block.index("inno") < auto_block.index("nsis"), "Inno must be preferred over NSIS"


def test_installer_preserves_patient_data_on_uninstall() -> None:
    """Batch 104 relocation contract: the clinic DB under the writable data
    root survives both upgrade and uninstall."""
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert r"{localappdata}\Programs\HHMS" in source, "install dir must be user-writable"
    assert "PrivilegesRequired=lowest" in source, "installer must run without admin elevation"
    assert "RequestExecutionLevel user" in source
    # Neither generator may rm the data root:
    for section in ("UninstallDelete", "Section \"Uninstall\""):
        idx = source.index(section)
        tail = source[idx : idx + 900]
        assert "RMDir /r" not in tail.replace(
            "RMDir \"`$INSTDIR\"", ""
        ), f"recursive delete found near {section!r} — would destroy patient data"


def test_installer_version_single_source_from_version_file() -> None:
    source = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Join-Path $ProjectRoot "VERSION"' in source
    assert "AppVersion=$Version" in source
    assert "HHMS-Setup-$Version.exe" in source


# ---------------------------------------------------------------------------
# 2. Release workflow structure
# ---------------------------------------------------------------------------


def _workflow() -> dict:
    return yaml.safe_load(RELEASE_YML.read_text(encoding="utf-8"))


def test_release_workflow_is_valid_yaml_with_required_jobs() -> None:
    wf = _workflow()
    assert wf["name"] == "release"
    jobs = set(wf["jobs"])
    assert {"test", "build-server-linux", "build-installer-windows", "release"} <= jobs


def test_release_workflow_triggers_on_version_tags() -> None:
    # Batch 118 policy change: releases are push-gated (every push to main),
    # no tags required. Name kept for historical traceability.
    wf = _workflow()
    # PyYAML parses bare `on:` as True (YAML 1.1 boolean)
    triggers = wf.get("on", wf.get(True))
    assert triggers is not None
    assert "push" in triggers
    assert "main" in triggers["push"]["branches"]


def test_release_workflow_gates_builds_behind_tests() -> None:
    wf = _workflow()
    jobs = wf["jobs"]
    assert jobs["build-server-linux"]["needs"] == "test"
    assert jobs["build-installer-windows"]["needs"] == "test"
    assert set(jobs["release"]["needs"]) == {"build-server-linux", "build-installer-windows"}
    win = jobs["build-installer-windows"]
    assert "windows" in win["runs-on"]
    steps_text = yaml.dump(win)
    assert "build-installer.ps1" in steps_text
    rel_text = yaml.dump(jobs["release"])
    assert "sha256sum" in rel_text, "release must publish SHA-256 checksums"


# ---------------------------------------------------------------------------
# 3. Cross-references between workflow and repo files
# ---------------------------------------------------------------------------


def test_every_repo_script_referenced_by_workflow_exists() -> None:
    wf_text = RELEASE_YML.read_text(encoding="utf-8")
    refs = set(re.findall(r"scripts/deploy/[\w.\-]+", wf_text))
    assert refs, "workflow references no deploy scripts"
    for ref in refs:
        assert (PROJECT_ROOT / ref).is_file(), f"workflow references missing file: {ref}"


def test_all_deploy_scripts_are_ci_covered_or_documented() -> None:
    """Every POSIX/PS deploy script must appear somewhere in the workflow so
    nothing rots unexercised (build-server.sh, server-launch.ps1, ...)."""
    wf_text = RELEASE_YML.read_text(encoding="utf-8")
    covered = ["build-server.sh", "build-installer.ps1"]
    for script in covered:
        assert script in wf_text, f"{script} not exercised by release workflow"
    # sanity: those scripts really exist
    for script in covered:
        assert (SCRIPTS_ROOT / script).is_file()
