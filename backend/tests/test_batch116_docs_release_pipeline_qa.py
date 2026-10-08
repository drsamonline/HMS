"""Batch 116 (Milestone 7 part 12) — Docs Consolidation & Automatic Dual-Platform Release QA.

Two deliverables are locked in by this suite:

1. Documentation tidy-up — per-batch historical pages live under
   ``docs/history/`` and every cross-reference resolves (no dangling links).
2. The GitHub release pipeline builds AND posts BOTH platform artifacts
   automatically on ``v*`` tags: Linux server bundle and Windows EXE +
   installer, each smoke-tested via the packaged server's ``--smoke-test``
   flag before upload, with a checksummed GitHub Release publishing both.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Docs consolidation
# ---------------------------------------------------------------------------

HISTORICAL_PATTERNS = re.compile(
    r"^(CLIENT_BATCH(?:5[0-9]|10[0-9]|11[0-4])|BATCH_5\d|REPORTING_PRINT_BATCH_0\d)"
)


def test_history_directory_exists_with_moved_pages() -> None:
    hist = DOCS / "history"
    assert hist.is_dir(), "docs/history/ must exist"
    pages = list(hist.glob("*.md"))
    assert len(pages) >= 20, f"expected the batch-history corpus moved, found {len(pages)}"


def test_no_historical_batch_pages_remain_in_docs_root() -> None:
    strays = [p.name for p in DOCS.glob("*.md") if HISTORICAL_PATTERNS.match(p.name)]
    assert not strays, f"historical batch pages still cluttering docs/: {strays}"


def test_index_links_all_resolve() -> None:
    text = (DOCS / "INDEX.md").read_text(encoding="utf-8")
    missing = []
    for m in re.finditer(r"\]\(([^)#]+\.md)\)", text):
        target = m.group(1)
        if target.startswith(("http", "mailto")):
            continue
        if not (DOCS / target).exists():
            missing.append(target)
    assert not missing, f"docs/INDEX.md has dangling links: {missing}"


@pytest.mark.parametrize(
    "root_doc", ["README.md", "CHANGELOG.md", "ROADMAP.md", ".ai/PROJECT_STATE.md"]
)
def test_bookkeeping_links_all_resolve(root_doc: str) -> None:
    path = REPO_ROOT / root_doc
    base = path.parent
    missing = []
    for m in re.finditer(r"\]\(([^)#]+\.md)\)", path.read_text(encoding="utf-8")):
        target = m.group(1)
        if target.startswith(("http", "mailto")):
            continue
        resolved = (base / target) if not target.startswith("/") else (REPO_ROOT / target.lstrip("/"))
        if not resolved.exists():
            missing.append(target)
    assert not missing, f"{root_doc} has dangling links: {missing}"


# ---------------------------------------------------------------------------
# 2. Server --smoke-test contract (used by both CI build jobs)
# ---------------------------------------------------------------------------


def test_server_entrypoint_supports_smoke_test_flag() -> None:
    src = (REPO_ROOT / "backend" / "app" / "server.py").read_text(encoding="utf-8")
    assert "--smoke-test" in src
    assert "prepare_runtime()" in src.split("_smoke_test")[1], (
        "smoke path must bootstrap the runtime (dirs + migrations) like a real first run"
    )
    assert "/api/v1/health" in src, "smoke path must probe the health endpoint"
    assert "release_version()" in src, "smoke path must verify the bundled VERSION handshake"


def test_smoke_module_compiles() -> None:
    import py_compile

    py_compile.compile(
        str(REPO_ROOT / "backend" / "app" / "server.py"), doraise=True
    )


# ---------------------------------------------------------------------------
# 3. Release workflow — automatic dual-platform build + publish
# ---------------------------------------------------------------------------


def test_workflow_yaml_valid_and_jobs_present() -> None:
    wf = _workflow()
    assert wf["name"] == "release"
    assert {"test", "build-server-linux", "build-installer-windows", "release"} <= set(wf["jobs"])


def test_both_platform_builds_run_on_tag_pushes() -> None:
    wf = _workflow()
    triggers = wf.get("on", wf.get(True))
    assert "v*" in triggers["push"]["tags"]
    # Release builds must fire ONLY on v* tags (or manual dispatch) — plain
    # branch pushes run the test gate but never build/post artifacts.
    assert "branches" not in triggers["push"], (
        "push trigger must not include branches; releases are tag-gated only"
    )
    for job in ("build-server-linux", "build-installer-windows"):
        cond = wf["jobs"][job]["if"]
        assert "startsWith(github.ref, 'refs/tags/v')" in cond, (
            f"{job} must run automatically on v* tag pushes"
        )
    assert wf["jobs"]["build-server-linux"]["runs-on"] == "ubuntu-latest"
    assert "windows" in wf["jobs"]["build-installer-windows"]["runs-on"]


def test_release_job_publishes_both_platform_artifacts() -> None:
    wf = _workflow()
    rel = wf["jobs"]["release"]
    assert set(rel["needs"]) == {"build-server-linux", "build-installer-windows"}
    assert "startsWith(github.ref, 'refs/tags/v')" in rel["if"]
    text = yaml.dump(rel)
    assert "sha256sum" in text, "checksums required"
    assert "softprops/action-gh-release" in text, "GitHub Release auto-publish required"


def test_linux_job_uploads_bundle_after_smoke_gate() -> None:
    wf = _workflow()
    steps = wf["jobs"]["build-server-linux"]["steps"]
    names = [str(s.get("name", "")) for s in steps]
    uses = [str(s.get("uses", "")) for s in steps]
    smoke_idx = next(i for i, n in enumerate(names) if "Smoke-test" in n)
    upload_idx = next(i for i, u in enumerate(uses) if "upload-artifact" in u)
    assert smoke_idx < upload_idx, "bundle must be smoke-tested before it is uploaded"
    run = "\n".join(str(s.get("run", "")) for s in steps)
    assert "./build/dist/HHMS-Server --smoke-test" in run, (
        "Linux smoke gate must invoke the packaged --smoke-test entry point"
    )


def test_windows_job_smoke_tests_exe_and_uploads_installer_plus_server() -> None:
    wf = _workflow()
    steps = wf["jobs"]["build-installer-windows"]["steps"]
    run = "\n".join(str(s.get("run", "")) for s in steps)
    assert "HHMS-Server.exe --smoke-test" in run, (
        "Windows server EXE must pass the same first-run smoke gate"
    )
    uploads = [s for s in steps if "upload-artifact" in str(s.get("uses", ""))]
    artifact_names = {u["with"]["name"] for u in uploads}
    assert {"hhms-windows-installer", "hhms-server-windows"} <= artifact_names, (
        "both the setup installer and the standalone server EXE must ship to the release"
    )


def test_referenced_scripts_exist() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for script in re.findall(r"scripts/deploy/[\w.\-]+", text):
        assert (REPO_ROOT / script).exists(), f"workflow references missing script {script}"
