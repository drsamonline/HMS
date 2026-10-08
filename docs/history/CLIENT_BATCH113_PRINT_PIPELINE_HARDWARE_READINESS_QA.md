# Batch 113 — Print Pipeline & Hardware-Readiness QA (Milestone 7, part 9)

Closes the last open functional item on the print surface ("final print/printer +
prescription-template QA on target hardware") with an automated contract suite over
the three layers of the printing pipeline. Physical-paper smoke testing remains a
field checklist; everything verifiable without a printer in the building is now
locked by tests.

## Scope

Suite: `backend/tests/test_batch113_print_pipeline_qa.py` (11 tests).

### Layer 1 — CSS (`frontend/css/print.css`)

- A4 portrait page geometry (`@page { size: A4 portrait }`).
- Chrome hiding rules: nav/sidebar/action bars carry `display:none!important`
  inside the print media block so no toolbar chrome reaches paper.
- Break-rule and toolbar-exclusion contracts for ledger sheets.

### Layer 2 — Client JS (`print.js`, `reports.js`, `api.js`)

- Every backend print-envelope endpoint has a matching client fetcher, a
  renderer exported from `print.js`, and a wired Reports-workspace button
  (cross-file consistency test over all 16 POST envelope routes).
- HTML-escaping contract: all dynamic values pass through the escape helper
  before entering `innerHTML` templates (XSS-on-paper guard).

### Layer 3 — Backend endpoints

- **Cold-database contract:** every one of the 16 envelope routes answers
  `200` against a fresh empty database — a new install can print standard
  forms on day zero without a crash.
- Envelope shape lock: `report_type`, identity fields, and totals resolve on
  every response.
- Missing-record behavior: envelopes for nonexistent IDs surface handled
  errors (`404`/`422`), never 500.
- **Paper-parity end-to-end:** Patient → Visit → Invoice → Item → Payment →
  `invoice-print-envelope` packet reflects the exact computed totals
  (`total 250.00 / paid 100.00 / balance 150.00 / status partial`, receipt
  number `RCP-…`, transaction reference preserved).

## Product fix shipped with this batch

`app/services/reporting.py` — refund-audit envelope crashed on cold databases:
the shared scan rollup omits `total_overpaid` when the invoice list is empty,
but the envelope schema requires it. The service now derives the field from the
rows (defaulting to `Decimal("0")`), so the sheet prints cleanly on fresh
installs.

## Test-harness notes

- Billing endpoints cast the JWT `sub` to `int` for the generated-by audit
  column; since the Batch 110 auth hardening a non-numeric subject correctly
  yields 401. The end-to-end test therefore rides a real login token via
  `token_for_login` instead of the harness default header.
- `seed_visit` was missing from the suite's `_qa_harness` import list (latent
  NameError caught at run time, fixed).

## Verification

- Batch 113 suite: **11 passed**.
- Full backend suite after changes: **503 passed, 2 skipped** (492 prior + 11
  Batch 113; skips remain the opt-in tier-2 EXE-build tests).
- Staged-tree hygiene check run before commit (tracked `.pyc` = 0,
  `data/logs/hhms.log` untracked).

## Remaining Milestone 7 scope (Batch 114+)

Cross-module client integration polish, physical printer field-checklist
execution on target hardware, and production release gated on secret-key
rotation (`data/secret.key` persists in git history).
