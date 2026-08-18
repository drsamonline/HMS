# Baseline Cleanup Audit — HMS27

## Actions
- Removed `.git` from the transfer baseline.
- Removed local `.env` from the transfer baseline.
- Removed `__pycache__`, `*.pyc`, `*.pyo`, `*.pyd`.
- Removed test/coverage/build caches where present.
- Retained functional source files, tests, migrations, documentation and client/server project files.
- Retained historical batch documentation.
- Did not delete source files merely because names looked duplicated; those require reference-level analysis.

## Result
This archive is a clean transfer baseline for continued HHMS development. The live Git repository in `E:\HMS` remains the development authority for commits and pushes.
