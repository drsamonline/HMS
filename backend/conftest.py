"""Backend test session bootstrap.

Anchors the working directory to the repository root so client-contract
tests that read frontend files via CWD-relative paths (e.g.
``Path("frontend/js/app.js")``) work regardless of invocation directory.
"""
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
