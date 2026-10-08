# Batch 114 — Cross-Module Client Integration Polish & QA (Milestone 7, part 10)

**Scope:** wire the IPD Management workspace end-to-end into the desktop client, fix the
Pharmacy authenticated-user context, and lock every headlessly-verifiable invariant of the
cross-module integration with an automated contract suite. This closes the last open
functional Milestone 7 code item ("cross-module client integration polish").

## Product changes

### IPD Management workspace (new nav module)
- `frontend/index.html` — sidebar gains **IPD Management** (`data-app-view="ipd-management"`,
  `data-access="ipd-management"`), placed after OPD Queue.
- `frontend/js/rbac.js` — ACCESS vocabulary gains the `ipd-management` key:
  `beds.manage, bed.manage, wards.manage, ward.manage, admission.manage, ipd.manage`.
  Blanket-access roles (admin/administrator/hospital administrator/super administrator) see
  it automatically; other roles need one matching permission.
- `frontend/js/ipd_management.js` (new module) — bed census list with ward/status filters,
  create-bed form, admissions list, admit-patient form (patient ID, bed, datetime, case type,
  reason, status), and a discharge form that closes an active admission and releases its bed.
  All rendered values are HTML-escaped before entering `innerHTML` (XSS-on-screen guard).
- `frontend/js/app.js` — imports `openIPDManagementWorkspace` from `./ipd_management.js` and
  routes `appView==="ipd-management"` to it with the current user profile.
- `frontend/js/api.js` — fetchers for the exact backend routes the workspace calls:
  `listBeds`, `createBed`, `updateBed`, `listAllAdmissions`, `createAdmission`,
  `updateAdmission`, `getDischargeByAdmission`, `createDischarge`.

### Pharmacy user-context fix
- `frontend/js/pharmacy.js` — dispensing actions now extract the authenticated user id from
  the same session context as the rest of the client (aligned with the Batch 110 `/auth/me`
  contract), replacing the previously broken local assumption.

## QA suite
`backend/tests/test_batch114_cross_module_integration_qa.py` — **13 tests**, three layers:

1. **Static frontend contracts** — nav button registration (exactly one), RBAC access map
   defines `ipd-management` with the expected permissions, app.js routing/import, api.js has
   all eight fetchers, XSS escaping in every rendered template, and a syntax check of all
   touched ES modules via `node --check`.
2. **Backend round-trips over the exact routes the workspace calls** — bed census
   create/list/filter/PATCH round trip, admission create with bed-occupancy side effects
   (occupied bed rejected), discharge releases the bed, unknown-patient admission rejected
   (404).
3. **RBAC gating semantics** — executed through real `node` against `rbac.js`: administrator
   blanket access, explicit `beds.manage` grant passes, unrelated permission denied, null
   profile denied. Plus the cross-file contract that every `data-access` key in index.html
   (including `ipd-management`) has an ACCESS vocabulary entry.

## Fixes discovered during verification
- **Batch 110 regression (product):** `rbac.js` had gained an `"ipd-management"` entry but the
  Batch 110 test's vocabulary regex (`^\s+(\w+):\s*\[`) only matched bare identifiers, so
  quoted keys were invisible → `test_every_nav_access_key_has_rbac_vocabulary` failed. The
  Batch 110 regex was widened to accept both bare and quoted keys
  (`^\s*(?:"([\w-]+)"|(\w+))\s*:\s*\[`), matching the Batch 114 harness.
- **Harness churn:** an intermediate attempt to normalize hyphenated module keys inside
  `canAccess` broke explicit-grant lookups (the map is keyed by the raw `data-access` value);
  reverted — lookups stay direct.
- **Hygiene regression (fourth occurrence):** the Batch 114 code commits emptied `.gitignore`
  and re-committed 448 `.pyc` files + `data/logs/hhms.log`. Reverted at close: `.gitignore`
  restored from `2e2cd1c`, all artifacts untracked (files remain on disk, ignored). The
  staged-tree hygiene check before every commit is mandatory.

## Test results
- Batch 114 suite: **13 passed**.
- Full backend suite at close: **516 passed, 2 skipped** (503 prior + 13 Batch 114; skips
  remain the opt-in tier-2 EXE-build tests).

## Remaining Milestone 7 scope
- Physical printer field-checklist execution on target hardware (operational, non-code).
- Production release gated on secret-key rotation (`data/secret.key` persists in git history
  through Batch 104-era commits).
