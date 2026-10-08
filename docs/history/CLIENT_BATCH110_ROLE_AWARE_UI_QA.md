# Batch 110 — Role-Aware UI & Cross-Module Navigation QA

**Milestone 7 · Release (part 6)** — closes the Milestone 3 open item
"Role-aware UI" and locks the cross-module navigation contract between
the backend profile API and the client RBAC gate.

---

## Scope

The client hides, disables, and `aria-hidden`s every navigation surface a
user is not entitled to, driven entirely by the live server profile
(`GET /api/v1/auth/me`) — never by a stale client-side guess. This batch
locks that contract end-to-end with a 10-test QA suite
(`backend/tests/test_batch110_role_aware_ui_qa.py`).

## Backend: profile payload contract

| Invariant | Enforcement |
|-----------|-------------|
| Profile answers with sorted `roles` + `permissions` derived live from `UserRole` → `RolePermission` → `Permission` joins | `auth_service.get_current_user_profile` single grouped select |
| **Inactive roles never leak** — only `Role.is_active = TRUE` rows appear | join filter `Role.is_active.is_(True)` (QA-proved with an active + inactive role seed) |
| Inactive/deleted users fail closed (`AuthenticationException` → 401) | `not user.is_active` guard |
| Non-numeric JWT `sub` yields a clean **401**, never a 500 crash | new `try/int(...)/except ValueError → AuthenticationException` in `endpoints/auth.py` (product fix found by this batch's QA) |
| Missing bearer / forged token → 401 | existing JWT dependency (Batch 109 invariants) |

## Client: RBAC navigation gate (`frontend/js/rbac.js`)

- **Vocabulary completeness** — every `data-access="…"` key present in
  `frontend/index.html` (14 nav keys: opd, patients, clinical, ipd,
  investigations, billing, mrd, statistics, reports, inventory,
  procurement, activity, pharmacy, administration) has a matching
  permission-candidate list in the `ACCESS` map. A new nav marker without
  vocabulary fails QA.
- **Blanket administrator access** — `ALL_ACCESS_ROLES`
  (`admin`, `administrator`, `hospital administrator`,
  `super administrator`) short-circuits `canAccess` before permission
  matching; role names are normalized case-insensitively.
- **Deny-by-default** — `canAccess(null, …)` returns `false`; the
  logged-out shell calls `applyNavigationAccess(null)` so no module is
  visible pre-login.
- **Three-fold denial effect** — denied nav items get `hidden` class,
  `disabled = true`, and `aria-hidden="true"` (invisible, unclickable,
  invisible to assistive tech).
- **Record-tab fallback** — if the active record tab is denied, focus
  moves to the first allowed tab (`applyRecordAccess`).
- **Wiring** — `app.js` feeds the fetched profile into both gates and
  persists it via `sessionStorage("hhms.current_user")`; `api.js` exposes
  `getCurrentUserProfile()` against `/api/v1/auth/me`.

## QA matrix (`test_batch110_role_aware_ui_qa.py`, 10 tests)

| # | Test | Locks |
|---|------|-------|
| 1 | `test_auth_me_profile_payload` | 200; roles/permissions live-derived; inactive role excluded |
| 2 | `test_auth_me_rejects_nonexistent_user` | valid numeric sub, no User row → fail closed |
| 3 | `test_auth_me_refuses_malformed_subject` | non-numeric sub → 401 (regression on the fixed 500) |
| 4 | `test_every_nav_access_key_has_rbac_vocabulary` | index.html ↔ ACCESS map completeness |
| 5 | `test_administrator_roles_grant_blanket_access` | ALL_ACCESS_ROLES + normalization |
| 6 | `test_can_access_denies_without_profile` | deny-by-default |
| 7 | `test_navigation_gate_hides_and_disables_denied_items` | hidden/disabled/aria-hidden triple |
| 8 | `test_app_wires_profile_to_navigation_gate` | app.js wiring incl. null-shell |
| 9 | `test_api_exposes_current_user_profile_endpoint` | api.js ↔ /auth/me binding |
| 10 | `test_backend_profile_service_filters_inactive_roles` | service-level SQL guards |

## Product fix shipped with this batch

`GET /api/v1/auth/me` previously crashed with an unhandled `ValueError`
whenever a syntactically valid JWT carried a non-numeric `sub`
(reachable via any future token-issuing path or harness-style tokens).
The endpoint now converts the parse failure into a structured
`AuthenticationException` → HTTP 401 `AUTHENTICATION_ERROR`, keeping the
fail-closed authentication invariant uniform across the surface.

## Verification

- New suite: **10 passed**.
- Full backend suite after the change: **478 passed, 2 skipped**
  (468 prior + 10 Batch 110; skips remain the opt-in tier-2 EXE-build
  tests). No regressions in the Batch 103–109 auth/e2e suites.

## Remaining Milestone 7 scope

WebView2 offline redistributable CAB bundling, final print/printer QA on
target hardware, documentation/training material beyond this page, and
production release gated on secret-key rotation (`data/secret.key`
persists in git history through Batch 104-era commits).
