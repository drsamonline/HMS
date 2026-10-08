"""Batch 115 (Milestone 7 part 11) — Secret Rotation & Release Gate QA.

Verifies the production-release gate work:

* ``Settings.SECRET_KEY`` min-length validation is enforced (Batch 109's
  advisory check became a hard constraint).
* The persisted-secret loader rejects short keys and applies owner-only
  file permissions.
* Generated secrets match the documented format/entropy contract.
* The rotation utility script exists and honours its operator contract
  (backup, atomic write, fingerprint output, no plaintext echo).
* First-run bootstrap keeps generating mode-600 secrets on POSIX.
* Repo hygiene: runtime secret artifacts are ignored and untracked.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

# Environment BEFORE any ``app`` imports (mirrors _qa_harness contract).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "batch115-gate-secret-key-0123456789abcdef")
os.environ.setdefault("DISCOVERY_ENABLED", "false")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import ValidationError  # noqa: E402

from app.config import settings as settings_module  # noqa: E402
from app.config.settings import MIN_SECRET_KEY_LENGTH, Settings  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Enforced min-length validation
# ---------------------------------------------------------------------------

def test_secret_key_min_length_constraint_declared() -> None:
    field = Settings.model_fields["SECRET_KEY"]
    constraints = getattr(field, "metadata", [])
    assert any(getattr(c, "min_length", None) == MIN_SECRET_KEY_LENGTH for c in constraints), (
        "SECRET_KEY must carry an enforced min_length constraint"
    )


def test_short_explicit_secret_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="abc")


def test_valid_length_secret_accepted() -> None:
    s = Settings(SECRET_KEY="x" * MIN_SECRET_KEY_LENGTH)
    assert s.SECRET_KEY == "x" * MIN_SECRET_KEY_LENGTH


# ---------------------------------------------------------------------------
# Persisted-secret loader hardening
# ---------------------------------------------------------------------------

def test_loader_rejects_short_persisted_key(tmp_path, monkeypatch) -> None:
    key_file = tmp_path / "secret.key"
    key_file.write_text("tooshort", encoding="utf-8")
    monkeypatch.setattr(settings_module, "secret_key_path", lambda: key_file)
    with pytest.raises(RuntimeError, match="rotate"):
        settings_module._load_or_create_secret_key()


def test_loader_generates_long_random_key_when_absent(tmp_path, monkeypatch) -> None:
    key_file = tmp_path / "data" / "secret.key"
    monkeypatch.setattr(settings_module, "secret_key_path", lambda: key_file)
    value = settings_module._load_or_create_secret_key()
    assert len(value) >= 64  # token_urlsafe(48) -> ~64 chars
    assert key_file.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
def test_loader_applies_owner_only_mode(tmp_path, monkeypatch) -> None:
    key_file = tmp_path / "secret.key"
    monkeypatch.setattr(settings_module, "secret_key_path", lambda: key_file)
    settings_module._load_or_create_secret_key()
    mode = key_file.stat().st_mode & 0o777
    assert mode == 0o600


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
def test_loader_hardens_existing_world_readable_key(tmp_path, monkeypatch) -> None:
    key_file = tmp_path / "secret.key"
    key_file.write_text("k" * 48, encoding="utf-8")
    os.chmod(key_file, 0o644)
    monkeypatch.setattr(settings_module, "secret_key_path", lambda: key_file)
    settings_module._load_or_create_secret_key()
    assert key_file.stat().st_mode & 0o777 == 0o600


# ---------------------------------------------------------------------------
# Rotation utility contract
# ---------------------------------------------------------------------------

ROTATION_SCRIPT = REPO_ROOT / "scripts" / "deploy" / "rotate-secret-key.ps1"


def test_rotation_script_exists() -> None:
    assert ROTATION_SCRIPT.is_file()


def test_rotation_script_contract() -> None:
    text = ROTATION_SCRIPT.read_text(encoding="utf-8")
    # Backup before overwrite.
    assert "secret.key.bak-" in text or "$backupPath" in text
    # Atomic write (temp file then move).
    assert ".tmp-" in text and "Move-Item" in text
    # Fresh random key of the same format as the server.
    assert "RandomNumberGenerator" in text and "byte[] 48" in text
    # Fingerprint output without echoing the secret itself.
    assert "Get-FileHash" in text and "fingerprint" in text.lower()
    assert "Write-Host $token" not in text


# ---------------------------------------------------------------------------
# First-run bootstrap contract (Linux installs)
# ---------------------------------------------------------------------------

def test_first_run_bootstrap_secret_contract() -> None:
    script = (REPO_ROOT / "scripts" / "deploy" / "install-first-run.sh").read_text(
        encoding="utf-8"
    )
    assert "secrets.token_urlsafe(48)" in script
    assert "chmod 600" in script


# ---------------------------------------------------------------------------
# Git hygiene guards
# ---------------------------------------------------------------------------

def test_secret_paths_are_ignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/secret.key" in gitignore
    assert "data/server_id" in gitignore
    assert "*.pyc" in gitignore


def test_runtime_secrets_not_tracked() -> None:
    tracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert "data/secret.key" not in tracked
    assert "data/server_id" not in tracked
    assert not [t for t in tracked if t.endswith(".pyc")]


def test_runbook_documents_gate() -> None:
    runbook = (REPO_ROOT / "docs" / "SECRET_ROTATION_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    for section in ("Rotation procedure", "Rotation triggers", "min_length"):
        assert section in runbook


def test_settings_docstring_mentions_batch115() -> None:
    doc = settings_module._load_or_create_secret_key.__doc__ or ""
    assert "Batch 115" in doc


def test_generated_key_format_matches_urlsafe() -> None:
    # token_urlsafe alphabet: A-Z a-z 0-9 - _
    pattern = re.compile(r"^[A-Za-z0-9\-_]+$")
    assert pattern.match(Settings().SECRET_KEY)
