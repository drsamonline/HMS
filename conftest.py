"""Root conftest: ensure frontend contract tests can resolve relative paths.

Some client-contract tests read files via CWD-relative paths such as
``Path("frontend/js/api.js")``. Anchoring the session to the repository
root keeps those tests independent of the invocation directory.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)
