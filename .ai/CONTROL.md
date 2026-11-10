# HHMS Control

**This file is the memory of the project.** It survives sessions, sandboxes and
tool changes. If everything else is lost, this file plus the branch is enough to
resume without re-litigating a single decision.

It replaces `.ai/PROJECT_STATE.md`, which had grown to 451 lines, referenced a
`HMS(5).zip` that no longer exists, and described batch 102 and batch 104 as the
latest milestone in the same paragraph.

---

## 1. State

| Field | Value |
|-------|-------|
| Date | 2026-11-09 |
| Branch | `batch-40-tutorial` (stacked on `batch-39-apiref`) |
| Base commit | `2ee5c83` (v0.0.2, `main`) |
| Head commit | `b24-commit` (B24) + the control commit that carries this file |
| Tests | **1065 passed, 2 skipped, 1067 collected** (569 baseline + 496 new) |
| Wave complete | **Waves 0–8 complete (B01–B45)**; wave 9 five of six |
| Next batch | **B51 — the handover pack, closing wave 9** |
| Blocking decision | none |
| Open question | **Suite runtime is now the top operational problem** — see the note below |

---

## 2. What is authoritative for what

Three sources, and they never overlap:

| Question | Answer lives in |
|----------|-----------------|
| What should be built, and in what order? | `HHMS_BUILD_PLAN.md` — the 40 batches |
| Why that order, and what is the design? | `HHMS_Build_Plan.pdf` |
| What has actually happened? | **this file** |
| What does the code do right now? | the code, and `SECURITY.md` |
| What are we aiming at? | `docs/SECURITY_ARCHITECTURE.md`, `docs/MASTER_SPECIFICATION.md` |

When two documents disagree: this file wins on history, the build plan wins on
the future, and the code wins on fact. Never resolve a disagreement by rewriting
history.

---

## 3. The ritual — consolidate after every third batch

The plan stays flexible only if it is periodically re-read rather than only
appended to. Run this after B09, B12, B15, and at the end of every wave.

It is a **cleanup pass, not a feature pass**. It may delete code. It may reorder
the queue. It may not add scope.

### The nine steps

1. **Prove the state.** Run the full suite. Record the number here. A number
   that moved without a batch explaining it is a finding.
2. **Re-run each of the last three gates by name.** The suite passing is not the
   same as the gate passing; a gate can be satisfied by a test that another
   batch quietly weakened.
3. **Prune.** For each of the last three batches: is there a leftover flag, a
   dead helper, a TODO, a commented-out branch, a doc paragraph describing
   something that changed? Delete it. The constitution bans placeholders; the
   ritual is where that ban gets enforced.
4. **Reconcile the documents.** Does `SECURITY.md`, the README, or any file in
   `docs/` still describe the code? Where a claim is now wrong, either fix the
   code or move the claim to the "Not yet built" table. Never leave a doc
   asserting something untrue — that is exactly how this project drifted the
   first time.
5. **Re-rank the next three.** Is the next batch still the highest value? The
   plan is a queue, not a contract. Move things freely, and record the move in
   the decision log with one line of reasoning.
6. **Never cite this file's own commit.** An amended commit changes its hash, so a self-reference is stale the moment it is written. Record everything up to this document; describe its own commit as "this commit".
7. **Split anything that grew.** A batch that took more than twice its size
   estimate was two batches. Split it, and say where the seam was.
8. **Append.** One row in the batch log, one row in the decision log if a
   decision was made.
9. **Close** with `chore(control): consolidate after Bxx-Bxx`.

### What the ritual is not

- It is not a redesign. Architecture is frozen (constitution rule 11).
- It is not a release. Versioning stays with the release workflow.
- It is not a place to sneak in the batch you were told not to do.

---

## 4. Drift guards

Six specific failures, each observed in this repository, each with the guard
that stops it recurring. Read this before starting any batch.

| # | Failure | How it looked last time | Guard |
|---|---------|-------------------------|-------|
| G1 | Building the visible surface before the spine | 119 batches, 16 print envelopes, 0 module flags, 0 audit writes | No reporting or packaging work until B15 is green. A wave's gate closes the wave; nothing starts early |
| G2 | Fleet sweep contamination | A block titled "the four things every app here should have" injected into the served GUI shell; a page sweep deleted `frontend/index.html` | No cross-repository tooling runs against this repo. `PAGES.json` carries the do-not-touch list. B04 removed the block |
| G3 | Documents asserting intentions as facts | `SECURITY.md` claimed encryption at rest, encryption in transit, enforced RBAC and audit logging; none existed | Every claim in a document names the batch that implements it, or sits in "Not yet built" |
| G4 | Scope creep by batch | Features arriving in numbered batches that were never in the specification | A batch not in the plan needs a decision-log entry **before** the code, not after |
| G5 | Re-litigating settled decisions | Reworking the same design across batches | The decision log is append-only. A decision reopens only with new evidence, and the evidence is named in the entry |
| G6 | Session amnesia | A rebuild-from-memory after every break | This file. Never rely on chat history as the record |

---

## 5. Document index

| File | Status | Purpose |
|------|--------|---------|
| `.ai/CONTROL.md` | **authoritative** | This file. State, ritual, guards, logs |
| `.ai/PROJECT_CONSTITUTION.md` | **authoritative, locked** | Twelve immutable rules |
| `.ai/CODING_RULES.md` | authoritative | Style and structure |
| `.ai/DECISIONS.md` | authoritative, append-only | Architectural decisions |
| `.ai/REVIEW_CHECKLIST.md` | authoritative | Pre-merge checks |
| `.ai/PROJECT_INDEX.md` | reference | Map of the docs folder |
| `.ai/PROJECT_STATE.md` | **superseded** | Replaced by this file; kept for history only |
| `docs/MASTER_SPECIFICATION.md` | authoritative | v1.0 scope, frozen |
| `docs/SECURITY_ARCHITECTURE.md` | authoritative | Target state |
| `SECURITY.md` | authoritative | Current state, honest about gaps |
| `HHMS_BUILD_PLAN.md` | **authoritative** | The 40 batches, gates, sizes |
| `HHMS_Build_Plan.pdf` | reference | Rationale, dashboard design, reuse table |
| `SETUP_WIZARD_SPEC.md` | authoritative for wave 4 | Ten steps, catalogue, acceptance tests |
| `NABH_MODULE_SPEC.md` | authoritative for the NABH module | Schema, indicators, sub-modules |
| `HHMS_Design_Recovery.pdf` | historical | The drift diagnosis that produced the plan |
| `docs/cleanroom/` | to be created at B16 | Behaviour specs for reimplemented workflows |

---

## 6. Decision log

Append-only. Newest at the bottom. Reopening an entry requires new evidence,
named in the new entry.

**D-001 — Foreign keys before the audit trail.**
B03 ships before B07. Enabling enforcement on a database that already contains
orphans would start rejecting writes a hospital depends on, so the sweep script
ships with the pragma and is run first. Evidence: `scripts/orphan_sweep.py`.

**D-002 — The client fails closed before permissions are seeded.**
B05 makes `rbac.js` deny an account with no permission codes, but only the
`admin` role exists today and it holds all-access, so nothing regresses in the
demo. Consequence, stated plainly: until B12 seeds permission codes onto roles,
any non-admin account will see an empty navigation and the notice added in B05.
That is the correct behaviour and it is temporary.

**D-003 — `SECURITY.md` splits current state from target state.**
The file described the architecture document's intentions as shipped behaviour.
It now states what ships, and carries a "Not yet built" table naming the batch
that closes each gap. The alternative — deleting the claims — would have hidden
the gaps instead of scheduling them.

**D-004 — B04 and B05 share one commit.**
Both edit `frontend/index.html` and `frontend/rbac.js` in the same regions. A
split commit would have required staging hunks, which makes the diff harder to
review than the combined change. The plan's rule is one batch per commit series;
this is one series of two batches, and the commit message names both.

**D-005 — The content security policy permits inline script and style.**
A nonce-based policy is correct but the current GUI renders inline blocks; a
policy the UI cannot satisfy would be reverted by the first person who hit a
blank page. Tightening it is part of B27/B28, and the docstring says so.

**D-006 — Three columns from the plan were not added.**
B07 named `actor_id`, `action` and `occurred_at`. Each duplicates a column that
already exists: `user_id` is the actor, `activity` is the action and
`action_timestamp` is the time. Adding them would have created two sources of
truth for the same fact, and the one that drifts is always the one somebody
forgot to populate. The gate test asserts they are absent, so the decision is
enforced rather than merely recorded.

**D-007 — `user_id` is nullable and `actor_username` is denormalised.**
Neither was in the B07 text. Without the first, a failed authentication for a
username that does not exist cannot be recorded at all, and
`SECURITY_ARCHITECTURE.md` section 9 names failed authentication as an event
that must be. Without the second, an audit entry stops naming the person the
moment their account is renamed or deactivated. A foreign key cannot promise
that, so the name is stored as it stood.

**D-008 — Stacked branches, not one long branch.**
Wave 1 sits on `batch-01-accountability`, branched from `batch-00-quick-wins`
rather than from `main`, because wave 0 is still open as PR #80. A PR for wave 1
targets the wave 0 branch and retargets to `main` automatically when #80 merges.
The alternative - one branch for everything - would have made the wave 0 review
grow with each batch, which is how a review stops being a review.

**D-009 — The token carries username and roles.**
An audit row must say what authority the caller held **when they acted**. Reading
it from the token records the role at login, which for a 30-minute token is close
enough and is arguably the more accurate fact; a database lookup would report
their role today, which is a different and less useful answer. Cost: a role change
takes effect in the audit trail at the next login. Accepted.

**D-010 — An audit failure rolls back the business change.**
If the audit row cannot be written, `record()` raises and the caller's transaction
rolls back. The alternative - log the failure and continue - means the system
silently performs changes it cannot account for. The risk is that an audit-table
problem becomes an outage rather than a degradation. That trade is deliberate: an
unaudited write in a hospital record is worse than a refused one, and the table
has no external dependencies that could make it fail independently.

**D-011 — The request context is a ContextVar, reset in a `finally`.**
Not a module global: one process serves concurrent requests, and a global would
hand one client's address to another client's audit row. Reset in `finally` so a
raised handler cannot leave a context bound for the next request. Proven by a test
that drives a real `POST /patients` through the full stack and compares the row's
`request_id` with the `X-Request-ID` the client was given.

**D-012 — The actor is bound to the request, not passed to the service.**
B08 took `actor` as a parameter; carrying that across 42 services and every
endpoint that calls them would have been a signature change in hundreds of places
for no extra safety. The authentication dependency now binds the actor to the
request context and `record()` reads it, so a service call is one line. An
explicit actor still wins, so B08's patient paths are untouched.

**D-013 — B09 is a ratchet, not a claim.**
The batch text said "every write path in every module". In practice eight
services record and 34 do not, and saying otherwise would be the exact failure
this project already made once (documents asserting intentions as facts). The
coverage test freezes the 34 in a list that may only shrink, fails on any new
service that writes without recording, and states its own two limits in its
docstring. The gap is now visible and measured rather than absent from the plan.

**D-014 — Invoice status changes get their own audit row.**
A payment that moves an invoice from unpaid to paid writes two rows: the payment,
and the invoice's status transition. One row would have described the cause and
buried the effect; an auditor sampling an invoice wants its status history, and an
auditor sampling a receipt wants the payment. Cheap, and both questions answer
themselves.

**D-015 — The chain excludes `id` from the hash.**
The hash has to be computable before the insert assigns the id, so `id` is not
covered. The consequence: a row renumbered in place would not be detected by its
own hash. It would be detected at the next row, whose `prev_hash` points at the
old value. Accepted, because the alternative is a second UPDATE after insert,
which the append-only trigger forbids.

**D-016 — The migration duplicates the canonicaliser rather than importing it.**
A migration must keep working after the application code moves on. Importing
`app.services.audit._jsonable` would mean a future change to that function
silently invalidates every historical hash. The duplicate is deliberate and
documented; if the two drift, the verifier reports every backfilled row as
edited, which is loud and correct.

**D-017 — Triggers block UPDATE as well as DELETE.**
The plan specified DELETE. Blocking UPDATE too means the tamper tests must drop
the trigger before editing, which is exactly the realistic bypass and makes the
test honest rather than decorative. Someone who can drop a trigger can also drop
the table, so the chain - not the trigger - is the control that survives a
determined insider.

**D-018 — The export records itself, in its own commit.**
The export handler commits the audit row before returning the file. It cannot
join the caller's transaction because there is no business change to join - the
response is the only side effect - and a failed export should still be visible as
an attempt. Consequence: an export that fails after recording leaves a row saying
it happened. Acceptable, because the row records the act of exporting, not the
delivery.

**D-019 — The review list omits before and after; the detail and the export carry them.**
A patient update row can hold a changed clinical field. Putting that in a list of
200 rows would put patient data on a screen whose purpose is to show who did what,
not what they saw. The detail view is a deliberate second click.

**D-020 — The catalogue lives in code, and the migration duplicates it.**
A permission is a fact about the software, so the source of truth is
`app/core/permissions.py`: the guard in B13 checks against it and the tests assert
against it. The migration carries a copy because a migration must keep working
when the application code moves on. The duplication is safe only because a test
compares the two and fails the build on drift - the same trade as D-016.

**D-021 — Module labels equal the code prefix.**
The first draft filed `users.read` under module `administration`, which makes the
administration screen group correctly and makes the catalogue unsearchable by
resource. The label now equals the first segment of the code, and one endpoint
file may map to several modules instead (administration serves users, roles,
settings and masters). The test asserts the mapping in both directions.

**D-022 — Enforcement is staged, and the default is `warn`.**
A guard that refuses every route the moment it lands would have turned the
application off between B13 and B14. `PERMISSION_ENFORCEMENT` has three values;
B13 ships `warn` (explicit guards apply, unguarded routes log), and B14 flips it
to `enforce` once every route declares a guard. A declared guard is enforced in
every mode except `off`, so the protection arrives with the code, not with the
switch.

**D-023 — Permissions are resolved per request, from the database.**
Not from the token. A role revoked at 10:00 should refuse a request at 10:01, not
at the next login. The cost is one join per protected request; the alternative is
an authorisation decision that lags a permission change, which is the wrong trade
for a control whose whole purpose is to stop something happening now.

**D-024 — Migration 0033 exists because the demo seed and the catalogue disagreed.**
The demo seeds a role called `admin`; the catalogue in 0032 created
`administrator`. Both mean the same thing to a hospital, and only one received
grants - so the guard would have locked the administrator out of their own
installation. 0033 grants every code to the four role names the client has always
treated as all-access, so the database and the client now agree.

**D-025 — Codes are chosen per module and per verb, not per file.**
GET takes the read code, POST/PATCH/PUT the write code, DELETE the specific code
where one exists (`patients.deactivate`, `billing.void`). One file may therefore
carry three different codes. The alternative - one code per file - would have made
`billing.read` and `billing.write` indistinguishable on the invoice-item delete,
which is exactly the route an auditor asks about.

**D-026 — `masters.read` was added because the guards revealed it was missing.**
Applying the guards is what showed that a GET on a master table had no code to
check. The catalogue had been written from the write side only. Recorded because
it is the argument for applying a control rather than reasoning about it.

**D-027 — The QA harness now creates a real administrator.**
`auth_headers()` used to mint a token whose subject was the string
"qa-batch103" and belonged to no user. That was harmless while nothing checked
permissions and became a 401 the moment the guard resolved them from the
database. Every harness helper that creates a user now grants the administrator
role, because an end-to-end suite needs an actor the guard admits.

**D-028 — A disabled module answers 404, not 403.**
The resource does not exist for a hospital that never bought the module. 403 would
tell the caller the route exists and they merely lack a grant, which is
information a hospital has no reason to disclose.

**D-029 — Routers stay mounted; the gate refuses per request.**
Module state is data and changes while the server runs. Omitting routers at
startup would mean a restart after every switch, and an administrator who toggles
pharmacy off and sees it still working until Tuesday. The cost is one cached query
per request, memoised on `request.state` like the permission set.

**D-034 — A batch write is all-or-nothing.**
Every value is validated before any is stored, so a wizard step that sets six
things lands or fails together. The alternative - partial application with an error
list - leaves a hospital configured halfway through a step, and nobody can tell
which half.

**D-035 — Export writes overrides, never all values.**
A provisioning file containing all forty-four values looks like a record of
decisions and is a record of whatever the defaults happened to be that day. It
would pin them forever, silently.

**D-039 — A wizard step writes settings or creates rows, never both.**
The two validate differently, and a step that did both would have to interleave
them. Dispatch on the step keeps each path honest.

**D-040 — Wizard steps are idempotent, always.**
A second click tops up a ward rather than creating a second ward with the same
name and different numbering, and never resets a sequence that has been issuing
numbers for a year. A wizard is a thing people click twice.

**D-044 — A compliance rule follows the model's vocabulary, not an invented one.**
The first version of the reason-for-change rule compared `decision` against
"continue", which is not one of its values. The model offers wait, repeat,
change_remedy and stop_reassess; two continue and two change. Reading the schema
first would have saved a cycle.

**D-045 — A readiness report names the duty it cannot check.**
Pharmacovigilance is not implemented, and the report says so rather than omitting
it. A report that quietly covers two of three duties reads as a clean bill of health.

---

## 7. Batch log

| Batch | Date | Commit | Gate | Suite | Note |
|-------|------|--------|------|-------|------|
| B01 | 2026-11-09 | `6947f1c` | 10 tests | 579 | Security headers on every response, including 404 and 401 |
| B02 | 2026-11-09 | `9c3c20a` | 2 tests | 581 | CORS default empty; `.env.example` no longer advertises localhost |
| B03 | 2026-11-09 | `6351789` | 5 tests | 586 | `PRAGMA foreign_keys=ON`; sweep script ships with it |
| B04 + B05 | 2026-11-09 | `ef719ad` | 4 tests | 590 | Fleet block removed (3,745 bytes); client fails closed with a notice. One commit, two batches, per D-004 |
| B06 | 2026-11-09 | `b9d79a1` | review only | 590 | `SECURITY.md` now separates shipped from planned |
| — | 2026-11-09 | this commit | — | 590 | This document; `PROJECT_STATE.md` marked superseded |
| B07 | 2026-11-09 | `72f23d5` | 9 tests | 599 | Evidence columns, nullable actor, three indexes. Two defects found by the gate: a missing server default on `outcome`, and a test fixture that silently measured an empty database |
| B08 | 2026-11-09 | `055c010` | 13 tests | 612 | Write path live for patients. ContextVar for request facts; token now carries username and roles. One defect found: `getattr(user, "roles", [])` would have returned an empty list forever, because User has no roles relationship |
| B09 | 2026-11-09 | `0cf0ed6` | 5 tests | 617 | Money, stock, admission, discharge and prescription wired; 34 services frozen as pending. Two defects: `record()` had no default for `actor`, and a scripted insertion broke an if/else |
| B10 | 2026-11-09 | `69c0f3a` | 9 tests | 626 | Append-only triggers, SHA-256 chain, verifier, nightly pass. One defect: hashing `isoformat()` never matched on read-back because SQLite returns naive datetimes - every row would have read as edited |
| B11 | 2026-11-09 | `66d0f3c` | 14 tests | 640 | Review filters, detail, CSV and PDF export, role gate, self-recording export. Two defects: `Depends()` used as a bare default instead of `Annotated`, and a client contract test still constructing the pre-B07 schema |
| B12 | 2026-11-09 | `7ad9f53` | 16 tests | 656 | 39 codes, 20 modules, 10 role templates, seeded by migration. Two defects: module labels disagreed with code prefixes, and the migration's id/code map was inverted so the administrator got no grants |
| B13 | 2026-11-09 | `8d0a0e2` | 12 tests | 668 | `require(code)`, router-level default deny, staged enforcement, migration 0033 for the `admin` role alias |
| B14 | 2026-11-09 | `2d8fbe6` | 7 tests | 675 | 238 of 244 routes guarded, enforcement flipped to `enforce`, B11's role gate removed, harness given a real actor. Two self-inflicted defects: a broad regex damaged 31 test files, and the first pass emitted bare functions instead of `Depends(...)` |
| B15 | 2026-11-09 | `66e085d` | 6 tests | 679 | Enumeration gate that names the unguarded route; proven to fail by planting one. Supersedes the lighter copy inside B14's gate |
| B15a | 2026-11-09 | `8205f1d` | 4 tests | 683 | Permission set memoised on `request.state`; suite 470 s to 337 s, twelve files 102 s to 75 s. First attempt with a ContextVar failed its own test |
| B16 | 2026-11-09 | `fdd0eae` | 11 tests | 696 | Eight modules with dependencies and permission sets; `ModuleState` derived from existing records by migration. The B09 ratchet caught the new service for not auditing, and it was wired rather than exempted |
| B17 | 2026-11-09 | `60ffc8e` | 7 tests | 701 | Routers grouped by module; a disabled module answers 404 and keeps its records. Three suite findings: the harness needed module rows, an unmigrated database now degrades to core, and two tests asserted a source literal instead of a mount |
| B18 | 2026-11-09 | `f7d6412` | 9 tests | 711 | One navigation manifest; the server filters the menu by enabled modules and held permissions; the static fallback is tested against it. Added `AUTHENTICATED_ONLY_PATHS` as a third route category |
| B19 | 2026-11-09 | `79e192b` | 18 tests | 729 | 44 settings described once with type, group, default and restart flag; precedence db > env > default returned with the value; six bootstrap keys refused by the store. The B09 ratchet caught the new service and it was wired, not exempted |
| B20 | 2026-11-09 | `771ebe2` | 15 tests | 744 | Configuration API with all-or-nothing batch writes, export of overrides only, secrets never echoed, and a matching CLI |
| B21 | 2026-11-09 | `cc5435d` | 9 tests | 753 | Spine cross-check: routes, modules, navigation and settings agree with each other. Proven to fail by planting a fictional permission. **Closes wave 3** |
| B22 | 2026-11-09 | `02886b1` | 10 tests | 763 | Setup state, six-digit code issued to the log and stored hashed, lockout after five failures, `scope=setup` token that is neither a login nor accepted as one. Four self-inflicted defects caught by the gate |
| B23 | 2026-11-09 | `15027e9` | 9 tests | 772 | Wards, departments, numbering and money steps, all idempotent. Found that Bed's model and migration disagreed about timestamps |
| B24 | 2026-11-09 | see `git log` | 9 tests | 781 | The handover: the first administrator who can log in and open screens. Network values staged for the restart rather than stored |
| B25 | 2026-11-09 | see `git log` | 9 tests | 790 | Review of all ten steps before commit, export of the answers, and finish writing the staged network values into a marked block in `.env` |
| B26 | 2026-11-09 | see `git log` | 9 tests | 799 | Restart status naming stored-vs-running differences; headless setup CLI; modules step de-duplicated into a handler. **Closes wave 4** |
| B33 | 2026-11-09 | see `git log` | 9 tests | 808 | NCH 7(2) registration number on the practitioner, 31(1) reason for change enforced on the follow-up, readiness report for both plus the unimplemented third. Harness now drops the schema before creating it |
| B34 | 2026-11-09 | see `git log` | 10 tests | 818 | Pharmacovigilance register with two timestamps per event, idempotent reporting, free-text product name. Readiness now checks all three duties |
| B17 | 2026-11-09 | `1849d8f` | none | 818 | Test-runtime pass: measured (2-3 s per block, ~60 tables × 800 tests), attempted, reverted. Finding and a four-step plan recorded |
| B35 | 2026-11-09 | see `git log` | 9 tests | 827 | Certificate register with retention computed at issue, referral case statement enforced, fourth readiness duty. **Closes wave 5** |
| B27 | 2026-11-09 | see `git log` | 7 tests | 834 | Design tokens: every colour, space and size named once; app.css carries no literal colour; contrast asserted against WCAG AA. **Opens wave 6** |
| B28 | 2026-11-09 | see `git log` | 11 tests | 845 | Component kit: form and confirm dialogs, toasts, four honest states, one worklist table, the patient header strip. No browser dialogs remain |
| B29 | 2026-11-10 | see `git log` | 9 tests | 854 | Navigation: fourteen flat buttons become six ordered groups; group metadata travels with each item; empty groups are removed client-side |
| B30 | 2026-11-10 | see `git log` | 10 tests | 864 | Nine role homes plus a default, precedence for multi-role users, panels filtered to what the caller can open, client renders the server's answer |
| NABH | 2026-11-10 | `batch-23` | 7 tests | 875 | `docs/NABH-MAPPING.md` (25 rows, every citation checked by a test) and the specimen accession (migration 0040) |
| B31 | 2026-11-10 | see `git log` | 6 tests | 881 | Prescriber name and registration number reach the prescription header. Found two pre-existing defects: a GET that called a method that does not exist, and a read model built from `__dict__` |
| B32 | 2026-11-10 | see `git log` | 9 tests | 890 | The prescription as a print document, previewed and printed from the same markup. **Closes wave 6** |
| B36 | 2026-11-10 | see `git log` | 15 tests | 905 | Indicator spine: nine indicators declared with numerator, denominator and standard, computed by one engine, `None` not zero when there is nothing to divide by. **Opens wave 7** |
| B37 | 2026-11-10 | see `git log` | 12 tests | 917 | The dashboard: grouped cards with definition, standard and an inline-SVG trend that breaks at a gap instead of drawing a false zero |
| B38 | 2026-11-10 | see `git log` | 12 tests | 929 | PSQ.3 coverage by family, served by the API and documented; three families fully reportable, six with a stated gap. Mapping row moves absent → partial |
| B39 | 2026-11-10 | see `git log` | 11 tests | 940 | Discharge outcome (migration 0041) unlocks mortality and DAMA; length of stay and re-admission came free once the right table was read. B38's assessment corrected in place |
| B40 | 2026-11-10 | see `git log` | 10 tests | 950 | The NCH monthly return as one printable document, with the QCI section stated rather than omitted. **Closes wave 7** |
| B41 | 2026-11-10 | see `git log` | 13 tests | 963 | Provenance marks in CSS, JS and Python, a public claim endpoint, and a detector. **Opens wave 8** |
| B42 | 2026-11-10 | see `git log` | 12 tests | 975 | The detector as a tool: directory, zip or URL in; a written finding with a verdict out, including 'marks stripped' |
| B43 | 2026-11-10 | see `git log` | 11 tests | 986 | Build sealing: a deterministic manifest of hashes, with verify reporting modified, added and missing files |
| B44 | 2026-11-10 | see `git log` | 14 tests | 1001 | Four editions enforced server-side; the free personal tier is OPD-only with case and bill printing. Public edition endpoint names what is not included |
| B45 | 2026-11-10 | see `git log` | 11 tests | 1012 | The takedown evidence pack: finding, seal comparison, licence position and a tamper-evident manifest, all reproducible by a third party. **Closes wave 8** |
| B46 | 2026-11-10 | see `git log` | 8 tests | 1020 | The operations runbook: install, LAN, the backup drill, maintenance, troubleshooting, handover. **Opens wave 9** |
| B47 | 2026-11-10 | see `git log` | 8 tests | 1028 | Ten role guides with a fixed five-section shape, each naming the home screen its role lands on and the screens it cannot open |
| B48 | 2026-11-10 | see `git log` | 15 tests | 1043 | Fourteen screen topics served by the API and shown in a drawer, in the same voice as the guides |
| B49 | 2026-11-10 | see `git log` | 10 tests | 1053 | The API reference, generated from the mounted routes with a drift gate that fails the build when it goes stale |
| B50 | 2026-11-10 | see `git log` | 12 tests | 1065 | The guided first run: five steps in the order a day happens, progress read from the database, never touching a real patient |

Suite counts are cumulative at the end of each commit and reconcile to the 569
test baseline plus 496 new tests. Final: **1065 passed, 2 skipped, 1067 collected**.

From B14 the suite takes longer than one 300-second call, so it is run in four
file-list chunks of 12, 23, 35 and 61 files and the counts summed. **Reconcile the
sum against `pytest --collect-only -q` before recording it** - at B17 the first
attempt silently skipped the 35-file chunk and reported a number 87 short. The
collect-only count is the check that the chunks actually cover everything.

### Ritual after B07–B09 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 617 passed, 2 skipped; reconciles to 569 + 48 |
| 2. Gates by name | B07, B08, B09 re-run together: 27 passed |
| 3. Prune | No TODO, FIXME or dead code introduced; the one stray line in `audit.py` (`audit_service = None`) was removed during B08 |
| 4. Docs reconciled | `SECURITY.md` gained an "Audit trail" section stating what is recorded and that coverage is partial, and its gap table now separates coverage from immutability |
| 5. Queue re-ranked | Unchanged. B10 next: an audit trail anyone with database access can delete is not evidence, and B11 (review UI) is worthless until B10 makes the rows trustworthy |
| 6. Split | B09 was two batches wearing one name: the wiring, and the coverage ratchet. They shipped together because the test is what makes the partial wiring honest |
| 7. Logged | D-012, D-013, D-014; batch log row added |

### Ritual after B11 (end of wave 1, 2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 640 passed, 2 skipped; reconciles to 569 + 71 |
| 2. Gates by name | B09, B10, B11 re-run together: 28 passed |
| 3. Prune | No TODO, FIXME or placeholder in the wave 1 modules; no unused imports in the three new or rewritten files |
| 4. Docs reconciled | `SECURITY.md` carries audit trail and audit integrity sections; the read schema changed, so the client contract test was updated rather than the schema softened |
| 5. Queue re-ranked | Unchanged. B12 next. Wave 2 is the last structural wave and it unblocks B30's role homes |
| 6. Split | None. B11 was one batch |
| 7. Logged | D-018, D-019; batch log row added |

**Wave 1 closed.** The trail records, cannot be deleted or edited, can be verified,
can be read by an auditor and can be exported - and the export records itself.

### Ritual after B14 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 675 passed, 2 skipped across four chunks; every file ran once |
| 2. Gates by name | B12, B13, B14 re-run: 35 passed |
| 3. Prune | No dead code in the new modules; `audit_logs.py` lost 47 lines of superseded role gate |
| 4. Docs reconciled | `SECURITY.md`'s authorisation row is now true: the client fails closed *and* the server refuses |
| 5. Queue re-ranked | Unchanged. B15 next, and it is small |
| 6. Split | B14 was one batch, but it was the largest so far and it broke the suite in ways that took four passes to settle |
| 7. Logged | D-025, D-026, D-027; batch log row added |

**A note for future waves.** B14 is the batch where regex-driven editing of 48
files went wrong twice. The fix was to revert wholesale and redo precisely. Any
future batch touching more than about ten files should be done file by file, or
with a script that is checked against a single file before it runs on all of them.


---

## 7a. Replan after wave 2 (2026-11-09)

The audit of B01–B14 changed three things in the queue and confirmed the rest.
The original `HHMS_BUILD_PLAN.md` remains the reference; this section is the
delta, and it wins where the two disagree.

### What the audit found

| Finding | Evidence | Consequence |
|---------|----------|-------------|
| Permission resolution costs a query per request | Suite went from 290 s to over 450 s after B14; it no longer fits one 300 s call | Insert **B15a**, a per-request memo for the permission set |
| Audit coverage is 7 of 42 services (17%) | `grep -l "audit.record("` versus services that write | The NABH evidence pack would be built on a third of the trail. **B09b** finishes the ratchet before wave 7 |
| The catalogue was written from the write side | `masters.read` had to be added during B14 | No action; recorded so the next catalogue is written from both sides |
| Two regex-driven edits across 48 files went wrong | B14, reverted wholesale once | Batches over ten files are done file by file |
| B11's role gate overlapped B14's guard | Removed in B14, 47 lines | None; the sequence absorbed it |

### Reordered queue

| Order | Batch | Change from the plan | Why |
|-------|-------|----------------------|-----|
| 1 | B15 | unchanged | Closes wave 2; makes the route guard regression-proof |
| 2 | **B15a** | **new** | The suite and every API response pay for a permission join. Memoise it per request |
| 3 | B16–B21 | unchanged | Config spine. The wizard cannot exist without it |
| 4 | B22–B26 | unchanged | The wizard. This is the answer to "anyone can configure it" |
| 5 | **B33–B35** | **moved up from wave 6** | NCH duties need nothing from waves 3–5, take six days, and give the product a claim no competitor can make. Shipping them before the interface puts a differentiator in a release earlier |
| 6 | B27–B32 | unchanged, now after the wizard | Role homes read the navigation manifest, which B18 creates |
| 7 | **B09b** | **new** | Finish the audit ratchet: the remaining 34 services |
| 8 | B36–B40 | unchanged | Indicators and the quality board |
| 9 | NABH module | unchanged | Six batches per `NABH_MODULE_SPEC.md` |

### Effort to v1.0, after the replan

| Block | Batches | Days |
|-------|---------|------|
| Done (B01–B14) | 14 | 14 |
| Close wave 2 (B15, B15a) | 2 | 2 |
| Config spine (B16–B21) | 6 | 8 |
| Wizard (B22–B26) | 5 | 11 |
| NCH duties (B33–B35) | 3 | 6 |
| Interface (B27–B32) | 6 | 12 |
| Audit ratchet (B09b) | 1 | 4 |
| Indicators (B36–B40) | 5 | 13 |
| NABH module | 6 | 16 |
| **Total** | **48** | **86** |

Eighty-six development days, against the sixty-four the original plan estimated
for forty batches. The difference is not scope creep: it is the two new batches,
the NABH module being costed separately rather than implied, and B14 taking four
passes instead of one.


---

## 7b. Requirement carried forward: IP protection and provenance

Recorded 2026-11-09 at the owner's instruction, to be built once the product
works. Not scheduled yet; it becomes **wave 8 (B41–B45)**.

The requirement: lock and guard the code, watermark it, and be able to tell when
it has been taken. Plus whatever else the owner adds before the wave is planned.

### Three constraints that shape the design before any of it is built

1. **Passive, never active.** A watermark must be discoverable *in the artefact* -
   a string in a binary, an identifier in a PDF, a licence record in a database.
   It must never transmit anything. HHMS is sold on being offline and
   LAN-only; a component that phones home would break that promise, would be a
   privacy problem under the DPDP Act, and would put patient data in the path of
   an IP dispute. If a licensee identifier has to travel, it travels in a file the
   customer chooses to send.

2. **Nothing may disable a hospital.** A licence check that can stop the software
   is a clinical safety hazard in a product used during an emergency. Expiry may
   warn, may restrict a non-clinical surface, may refuse a new installation - it
   must never stop a running system from recording a patient. This is not a
   preference; it is the difference between a licence and a liability.

3. **Disclosed in the licence.** A covert trace in medical software invites a
   regulator question. The EULA says the build carries a licensee identifier and
   why. Concealed from a competitor, disclosed to the customer.

### What the wave is likely to contain

| Batch | Idea | Notes |
|-------|------|-------|
| B41 | Provenance headers and SPDX identifiers on every source file | Cheap, and it is what a lawyer asks for first |
| B42 | Per-licensee build watermark: identifier embedded at build time in the binary, the PDF metadata and the database | One build per licensee, reproducible from a seed |
| B43 | Canary strings: unique, inert markers in the source and in the compiled output | Detectable in a leaked copy; harmless in a running one |
| B44 | Signed commits, SBOM and a published hash manifest per release | Proves what shipped, and when |
| B45 | Detection playbook: given a suspected copy, how to establish whether it derives from this code | The part that is actually used in a dispute |

Deliberately absent: anything that reports usage, anything that revokes a
function remotely, and any obfuscation of the clinical logic. Obfuscation would
make the code unauditable by the hospital that is buying it, which is the
opposite of the "no lock-in" argument the product is sold on.


---

## 7c. Requirement carried forward: documentation, tutorials and user guides

Recorded 2026-11-09 at the owner's instruction. Becomes **wave 9 (B46–B51)**,
after the product works, because documentation written before the behaviour
settles is the exact failure this repository already made once: `SECURITY.md`
asserted four controls that did not exist.

### The state of the documentation today

| Measure | Value |
|---------|-------|
| Markdown files in `docs/` | 119 |
| Markdown files repo-wide | 155 |
| Written before the audit | almost all of them |
| Known to be wrong now | `SECURITY.md` (fixed at B06), the RBAC claims, the route inventory, anything naming 242 routes |

So the wave does not start by writing. It starts by **auditing what is true**,
deleting or rewriting the rest, and then writing only what a person needs at the
moment they need it.

### The rule that makes it different from a pile of prose

Every claim a document makes about the software is checked by a test, or the
document says plainly that it is describing intent rather than behaviour:

| Document | What a test can verify |
|----------|------------------------|
| API reference | Every route in the OpenAPI schema exists and every documented route is mounted |
| User guide | Every menu item it tells the reader to click exists in the navigation manifest |
| Operations guide | Every command it names exists in the CLI, and the backup path it describes is the one the code uses |
| Setup guide | The ten wizard steps match `SETUP_WIZARD_SPEC.md`, field for field |
| Tutorial | The walkthrough runs against a seeded database and the screenshots come from that run |

### What the wave contains

| Batch | Deliverable | Audience |
|-------|-------------|----------|
| B46 | Documentation audit: mark every one of the 119 files true, stale or obsolete; delete the obsolete | You |
| B47 | Server operations guide: install, first run, backup, restore, secret rotation, upgrade, troubleshooting | The hospital's IT person |
| B48 | Role guides, one per role, written from that role's worklist and tested against the navigation manifest | Registration, doctor, pharmacist, laboratory, billing, records, stores, administrator |
| B49 | The tutorial: one end-to-end walkthrough - register, consult, prescribe, dispense, bill, discharge - with screenshots taken from a seeded run | A new user on day one |
| B50 | In-app help: a help panel on every screen, a first-run tour of the ten setup steps, and searchable help that works offline | Everyone |
| B51 | API reference generated from the OpenAPI schema, with a worked example per resource | An integrator, and your own next developer |

### Two decisions already made

1. **Offline.** The help ships inside the application. A hospital with no internet
   cannot reach a website, and a help system that needs one is a help system that
   does not exist on the ward.
2. **Screenshots are generated, not captured by hand.** A screenshot taken once is
   wrong after the next interface batch. The tutorial renders its images from a
   seeded database at build time, so it cannot silently drift.

### Ritual after B17 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 701 passed, 2 skipped, **703 collected**; the four chunks sum exactly to the collected count |
| 2. Gates by name | B15a, B16, B17 re-run: 22 passed |
| 3. Prune | No TODO or dead code in the new modules |
| 4. Docs reconciled | Nothing to change: `SECURITY.md` describes access control, and module gating is a product feature rather than a security claim |
| 5. Queue re-ranked | Unchanged. B18 next: the navigation manifest is what makes module state visible to the user |
| 6. Split | None |
| 7. Logged | D-028, D-029; batch log rows added |

**A counting error worth recording.** At B16 the four chunks were summed without
reconciling against the collected total, and 87 tests in one chunk were never run.
The number recorded was plausible and wrong. The ritual now requires the sum to
match `pytest --collect-only`.

**D-030 — The client filters the markup it has; it does not rebuild it.**
The click handlers are bound in `app.js` before the navigation request returns,
and a hospital whose request fails must still get a usable sidebar. So the static
list stays as the fallback and a test asserts it matches the manifest exactly. A
rebuild would have been cleaner and would have broken both of those.

**D-031 — There are three route categories, not two.**
Public (no token), authenticated-only (a token, no permission), and guarded (a
token and a permission). The navigation endpoint is the second: it returns the
caller's own menu. `AUTHENTICATED_ONLY_PATHS` names it, and a test keeps the list
to three entries so it cannot quietly become a back door.

**D-032 — Bootstrap settings cannot be stored in the database.**
Six values are read before the database is open: the port, three discovery keys,
the signing secret and the database address. Storing them would be a lie - the
server would never read the row - so `set_value` refuses them and the list is
asserted exactly, because it should not grow quietly.

**D-033 — Every read returns the source, not just the value.**
Database, environment, or catalogue default. The settings screen can then say where
a number came from, which is the difference between a page an administrator trusts
and one they distrust after the first unexplained value.

### Ritual after B20 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 744 passed, 2 skipped, **746 collected**; five chunks sum exactly to the collected count |
| 2. Gates by name | B18, B19, B20 re-run green |
| 3. Prune | No dead code; the CLI and API share the service rather than duplicating validation |
| 4. Docs reconciled | Nothing to change yet; the operations guide in wave 9 will document `config` |
| 5. Queue re-ranked | Unchanged. B21 closes wave 3, then the wizard |
| 6. Split | None |
| 7. Logged | D-034, D-035; batch log rows added |

**A harness quirk worth knowing.** Two tests in one file share an in-memory
database when both call `make_client()`: the second sees the first's writes. It
caught a test of mine that assumed isolation, and the fix was to use a key no
neighbour touches rather than to weaken the assertion. Worth remembering before
writing two tests that depend on the same setting.

### Wave 3 closed (2026-11-09)

| Batch | Delivered |
|-------|-----------|
| B16 | Eight modules, dependencies, permission sets; state derived from existing records |
| B17 | Routers grouped by module; a disabled module answers 404 and keeps its records |
| B18 | One navigation manifest, filtered server-side |
| B19 | 44 settings described once, with precedence returned alongside the value |
| B20 | Configuration API and CLI, all-or-nothing writes |
| B21 | The spine cross-check that holds the other five together |

The configuration spine is done. A hospital can now be described - which modules it
runs, who may open what, and how it is set up - and every one of those three is a
catalogue the code checks rather than a list in a template. Wave 4 builds the
wizard on top of it.

**D-036 — The setup wizard is gated by a code, not by a permission.**
It runs before any user exists. A six-digit code, issued to the server log, stored
as a hash, expiring in an hour and locked out after five failures, is what stands
between a freshly installed server and the first person on the LAN claiming it.

**D-037 — A setup token is not a login, and a login is not a setup token.**
The token carries `scope: setup`; `get_current_user` refuses it and
`require_setup_token` refuses anything without it. Both directions are tested,
because the failure that matters is one of them quietly accepting the other.

**D-038 — The setup code is delivered through the log, not the response.**
The log is the one channel a LAN user cannot read. A test asserting this must spy
on the logger rather than use `caplog`: an earlier test in the suite configures
logging, after which propagation is off and `caplog` stops seeing records. The
property under test is that the code is emitted, not that pytest can observe it.

### Ritual after B23 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 772 passed, 2 skipped, **774 collected**; five chunks sum exactly |
| 2. Gates by name | B22, B23 re-run green |
| 3. Prune | No dead code; the wizard's data steps share one dispatch rather than four branches |
| 4. Docs reconciled | Nothing to change yet |
| 5. Queue re-ranked | Unchanged. B24 completes the steps, B25 the review, B26 nerd mode |
| 6. Split | None |
| 7. Logged | D-039, D-040; batch log row added |

**A model/migration disagreement, found by the wizard.** `Bed` declares its
timestamps `NOT NULL` with no model-side default, while the migration gives them
`CURRENT_TIMESTAMP`. A schema built by `create_all` therefore rejects an insert the
migrated one accepts - a difference that appears only under test, which is the
worst place for one to hide. The model now declares the same default and the
handler sets the times explicitly. Worth checking the other models the same way
before wave 6 adds more writes.

**D-041 — Finish writes only a marked block in `.env`.**
The staged network values have to reach the environment file, but an operator may
have their own lines there. A block between two markers can be replaced on every
run; appending cannot, and neither can editing the file wholesale.

### Wave 4 closed (2026-11-09)

| Batch | Delivered |
|-------|-----------|
| B22 | Setup state, the six-digit code, a token that is not a login |
| B23 | Wards, departments, numbering, money - all idempotent |
| B24 | The handover to a real administrator; network values staged |
| B25 | Review before commit, export, finish writing `.env` |
| B26 | Restart status, headless CLI, modules de-duplicated |

The wizard is complete end to end: install, open a browser, read the code from the
server log, walk ten steps, log in as yourself - or do the same four flags from a
shell. That was the request that opened this work.

**D-042 — The headless CLI calls the wizard's services, not a copy of them.**
Two implementations of "create the first administrator" would drift, and the drift
would show up as a script-built hospital that behaves differently from a
browser-built one.

**D-043 — The administrator password comes from an environment variable.**
A flag lands in shell history and in the process list. Worth knowing: argparse
accepts an unambiguous prefix, so `--admin-password` is read as
`--admin-password-env` and silently consumes the secret as a variable name.

### Ritual after B24–B26 and B33 (2026-11-09)

| Step | Result |
|------|--------|
| 1. Suite | 808 passed, 2 skipped, **810 collected**; eight slices sum exactly |
| 2. Gates by name | B24, B25, B26, B33 re-run green |
| 3. Prune | No dead code; the modules step's inline logic in the endpoint was removed when its handler landed |
| 4. Docs reconciled | `SECURITY.md` unchanged; the NCH duties are a product claim, not a security one |
| 5. Queue re-ranked | **The suite is now the problem.** See below |
| 6. Split | B33 covered two duties and a report; the pharmacovigilance register is its own batch (B34) |
| 7. Logged | D-044, D-045; batch log rows added |

**The suite has become the bottleneck.** It now takes about 12 minutes across eight
slices, against one 300-second call for the whole thing at B14. Two causes, both
mine: the permission join on every request (mitigated at B15a but not removed), and
the harness dropping and recreating the schema for every block since B33. The next
batch that touches nothing else should be a test-runtime pass, or the verification
cost will keep growing faster than the feature work.

**D-046 — Recording an event and reporting it are separate acts.**
One field cannot hold both. A clinician records in the consulting room; the hospital
reports weeks later; the gap between the two timestamps is the evidence a hospital
is asked for.

**D-047 — A superseded test is pointed at the new truth, not deleted.**
B33 asserted that the pharmacovigilance duty was reported as unimplemented. B34
implemented it. The test now asserts that all three named duties carry a count,
which is the property that mattered all along.


---

## 7d. The test-runtime pass (B17, 2026-11-09) — measured, attempted, reverted

The suite had grown to about fourteen minutes across six slices. This batch set out
to fix that. It measured the cost, tried the obvious remedy, and reverted it when
the remedy broke five tests. The measurement and the reason are recorded here so
the next attempt starts where this one stopped.

### What the measurement says

| Observation | Value |
|---|---|
| Cost of one `make_client()` block | 2 to 3 seconds |
| What dominates it | Creating about sixty tables for each block |
| Slowest single test | 11.3 s (`test_patient_visit_token_chain_end_to_end`) |
| Total for three representative files | 37 s for 24 tests |

Every one of the eight hundred tests that uses the harness pays that 2–3 seconds.
That is the whole problem: not one slow test, but a fixed cost multiplied eight
hundred times.

### What was tried

Share one in-memory engine across the process and empty the tables between blocks
instead of dropping and recreating the schema. Deleting rows is far cheaper than
DDL, and the block still starts empty.

**It broke five tests**, all with `no such table: ModuleState`. The cause is that
other harness helpers — `make_file_client` and the various cache-clearing fixtures —
still clear the cached engine and session factory and point them at their own
database. The application then talks to a database the shared engine never created.

### Why it was reverted rather than fixed

Making one engine work means making *every* helper agree on it: `make_file_client`,
the per-test fixtures that call `get_engine.cache_clear()`, and the app's own
`get_db` dependency all have to stop fighting over the same process-wide cache. That
is a real refactor of the test rig, and doing it at the end of a long session, with
the whole suite needing a run after each step, is how a rig gets broken rather than
fixed.

### What the next attempt should do

1. One engine, owned by the harness, created once. No helper clears the caches.
2. `make_file_client` gets its own engine explicitly, passed rather than set through
   the environment.
3. Empty tables between blocks, in reverse dependency order.
4. Run the full suite after **each** of those three steps, not after all of them.

Expected: the fixed cost drops from 2–3 seconds to well under 100 milliseconds per
block, which is where the fourteen minutes goes.

### Wave 5 closed (2026-11-09)

| Batch | Delivered |
|-------|-----------|
| B33 | Registration number on the practitioner; reason for change enforced on the follow-up |
| B34 | Pharmacovigilance register, two timestamps per event |
| B35 | Certificate register with retention at issue; referral case statement |

Four NCH duties are now checkable, and the readiness report names all four. That is
a claim no homoeopathy product on the market makes, and it cost nine days.

**D-048 — A certificate stores the text as issued, never regenerated.**
A certificate is a statement made on a date. Regenerating it from current records
would produce a document that says what the hospital wishes it had said.

**D-049 — Past retention means archivable, never removable.**
Three years is a floor. The report says what may be archived and never what may be
deleted, because a hospital deleting a certificate at three years and a day has
misread the regulation.

### Wave 6 opened (2026-11-09)

| Batch | Delivered |
|-------|-----------|
| B27 | Design tokens; app.css carries no literal colour; contrast asserted |

**D-050 — Tokens are named for what they are for, not what they look like.**
`--ink` rather than `--grey-800`. A token named for its appearance tells you nothing
about whether it is safe to change; one named for its role survives a redesign.

**D-051 — Contrast is measured, not eyeballed.**
Every foreground/background pair the interface renders is checked against WCAG AA,
and the measuring helper is itself checked against known values. Grey-on-grey is how
a hospital interface becomes unreadable on a ward monitor.

**D-052 — The spacing and type scales are defined before they are used.**
Colour is fully tokenised and asserted. Space, type, radius and shadow are defined
now and applied as the interface is rebuilt in B28–B32; the test says so rather than
quietly exempting them.

**D-053 — A cancelled dialog resolves null, never undefined.**
`undefined` is falsy, so `if (!values) return` looks correct - and it is, until a
caller destructures the result before checking. Null is explicit and survives being
passed around; Escape counts as cancel because that is what the user meant.

**D-054 — Empty, no-results, loading and error are four states, not one.**
They all used to render "No data." A list that is empty because there is nothing yet
and a list that failed to load are not the same thing to somebody standing at a desk
wondering whether the system is broken.

**D-055 — The kit escapes plain values and trusts render functions.**
A column with a `render` function escapes its own content; a plain value is escaped
by the table. That is the distinction that keeps user data out of the markup while
letting a cell draw a badge.

**D-056 — Group metadata travels with each item, not in a second payload.**
The client already receives a list, and a list cannot carry metadata without
changing the shape every caller depends on. The alternative was a second request or
a breaking change; neither was worth the tidiness.

**D-057 — The client moves buttons into groups, never rebuilds them.**
Click handlers are bound in app.js before the navigation renders. Rebuilding the
markup would silently unbind every screen in the product, and it would look like a
routing bug rather than a rendering one.

**D-058 — A home is not a permission.**
The permissions decide what a role *may* open; the home decides what it *should*
open first. Conflating them would mean a role could not be given a nicer starting
point without changing what it is allowed to do.

**D-059 — A role with no declared home gets the default, never a blank screen.**
A blank screen reads as a broken system, and the account most likely to see one is
the one with the fewest options - the least able to work out that it is fine.

**D-060 — A home panel is dropped when the caller cannot open its screen.**
A shortcut that leads to a refusal is worse than no shortcut.

**D-061 — A field that never reaches the paper is not a compliance claim.**
The registration number was stored from B33 and sent to nobody. Moving MOM.4 from
partial to evidenced required the read model, the client component and the mapping
row to change together, which is the rule the mapping states.

**D-062 — A read model is built from named fields, not `__dict__`.**
`__dict__` carries `_sa_instance_state`. It survived only because the instance was
usually expired when it was read; one query earlier in the request changed that and
turned a working endpoint into a 500.

### Wave 6 closed (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B27 | Design tokens; no literal colour in the application stylesheet |
| B28 | Component kit: dialogs, toasts, four states, one table, patient strip |
| B29 | Navigation: fourteen buttons become six ordered groups |
| B30 | Nine role homes plus a default |
| B31 | The prescriber's registration number reaches the prescription |
| B32 | The prescription as a document, previewed and printed from one markup |

The interface work the request opened with - "clean professional GUI", "wizard-like
configuration so anyone can use" - is done. What remains is what the same request
called the main thing hospitals ask for: the dashboards, graphs and statistics for
NCH, NABH and QCI.

**D-063 — The preview is the printed document, not a picture of one.**
One markup, one path. A second builder for the printed version is how the two drift,
and a prescription that prints differently from what was reviewed is worse than one
that cannot print at all.

### Wave 7 opened (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B36 | The indicator spine: nine declared indicators, one engine, one endpoint |

**D-064 — A ratio with an empty denominator is `None`, never zero.**
"No admissions this month" and "0% of admissions were discharged" are different
statements. A dashboard that shows the second when it means the first teaches people
to distrust it, and the distrust is correct.

**D-065 — The contract is held in both directions.**
Every declared indicator must have a computer, and no computer may be undeclared. A
number computed but not described is a number nobody can argue with; a number
described but not computed is a promise.

**D-066 — A missing month is a gap in the line, not a zero in it.**
The path breaks at every unavailable point rather than joining across it. A missing
month plotted as zero draws a plunge that never happened, and the reader has no way
to tell it from a real one.

**D-067 — A trend is drawn in calendar months, not rolling thirty days.**
Adjacent rolling windows share most of their data, which draws a smooth line that
hides every real change.

**D-068 — One point is not a trend.**
Fewer than two months of data renders as a sentence saying so, not as a flat line.

**D-069 — Do not enumerate a standard from memory.**
The 32 PSQ.3 indicators are not listed in this repository because the authoritative
list is in the NABH standard document. A list written from memory would be one a
hospital could not rely on, and it would look exactly as authoritative as a correct
one.

**D-070 — Coverage is reported by family, with the gap stated.**
Eleven families, three fully reportable, two partly, six not at all - each with what
is missing. A hospital can see, before buying, which numbers this product can produce.

**D-071 — A discharge timestamp is a decision, not a commit.**
One nullable column on `Admission` would unlock length of stay, mortality,
re-admission and discharge against medical advice. It changes the clinical model,
which is frozen; so it is raised as a decision for the owner rather than taken.

**D-072 — A gap analysis that reads one table will report gaps that are not there.**
B38 said length of stay was uncomputable because `Admission` has no discharge
timestamp. `Discharge` has one. The lesson is recorded in the document rather than
tidied away, because the next assessment will face the same temptation.

**D-073 — An unclassified episode has an unknown outcome, not a good one.**
`discharge_outcome` is nullable and existing rows stay null. The mortality
denominator counts only episodes with a recorded outcome, so mortality cannot fall
simply because record-keeping got worse.

### Wave 7 closed (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B36 | The indicator spine: thirteen declared indicators, one engine |
| B37 | The dashboard: definitions, standards and a trend that breaks at a gap |
| B38 | PSQ.3 coverage by family, served by the API |
| B39 | The discharge outcome, and a correction to B38 |
| B40 | The NCH monthly return, with QCI stated rather than skipped |

**D-074 — A missing section looks like a passing section.**
QCI measures patient experience, complaints and safety culture, none of which HHMS
records. The return shows the section with a reason against each gap, because
omitting it would read as a clean result.

**D-075 — A count of zero is a fact; a ratio with no denominator is a gap.**
No certificates issued is a true zero. No discharges means mortality is unavailable,
not 0%. The two must not be rendered the same way, and a test asserts it.

### Wave 8 opened (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B41 | Provenance marks in four kinds of file, a public claim, and a detector |

**D-076 — A mark that changes per build cannot be tied to a release.**
`HHMS-PROV-<release>-<digest>`, stable for a release. A copy found in the wild can be
tied to the version it came from; a per-commit mark could be tied to nothing.

**D-077 — Say what the mark does not do.**
The module docstring states plainly that this is evidence and deterrence, not a
control. Claiming more would be the kind of overstatement the rest of this estate
avoids.

**D-078 — A detector that finds its own fixtures always succeeds.**
The first version of the mismatch test wrote the fake marker literally in the test
file the detector scans, so the "not found" assertion passed for the wrong reason. The
fake is now built by concatenation.

**D-079 — Absence of a mark in something that is otherwise this software is evidence.**
The fingerprint list exists so a stripped copy is not reported as clean. It is
deliberately narrow: a fingerprint list that matches everything makes every tree look
stripped.

**D-080 — A finding states what it does not prove.**
The clean verdict says in its own text that a sufficiently rewritten copy would
produce the same result. A report that overstates its own reach is worse than no
report.

**D-081 — A seal kept beside the code proves nothing against someone who can edit both.**
The seal records where it must be published - the release page and the signed tag -
and says so in its own payload. A seal trusted beyond its reach is worse than none.

**D-082 — A seal excludes what changes without the source changing.**
Caches, build output, databases and the seal itself. A seal that changes when nothing
changed is noise, and noise gets ignored.

**D-083 — Free to use is not free to copy.**
The personal edition is PolyForm Noncommercial: free for a personal practice,
forbidding redistribution. That distinction is what makes a free tier compatible with
a proprietary codebase, and it has to be in the licence, not only in the price list.

**D-084 — A tier enforced only by a licence paragraph is not a tier.**
Editions are enforced in `module_state.enable`, which every path goes through - the
wizard, the configuration API, the headless CLI and a crafted request.

**D-085 — The free edition ships the same code, switched off.**
Build-time stripping is a packaging step, not yet written. Until it exists the honest
description of the free tier is a licensed restriction, not a technical impossibility,
and the module docstring says so.

### Wave 8 closed (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B41 | Provenance marks in four kinds of file, a public claim, a detector |
| B42 | The detector as a tool: directory, zip or URL in; a finding out |
| B43 | Build sealing: a deterministic manifest of hashes |
| B44 | Four editions, enforced server-side |
| B45 | The takedown evidence pack |

**D-086 — The pack does not embed the material.**
A pack that carried a copy would be a redistribution, and the copy inside the evidence
could be altered afterwards. It records where the material was and what it hashed to.

**D-087 — The absence of a finding is not a finding of absence.**
A sufficiently rewritten copy produces a clean result. The pack says so in its own
text, because a report that overstates its reach is worse than no report.

### Wave 9 opened (2026-11-10)

| Batch | Delivered |
|-------|-----------|
| B46 | `docs/OPERATIONS.md`, the operator runbook, with its citations under test |

**D-088 — A runbook points at documents; it does not copy them.**
Two copies of an instruction is how one goes stale, and the runbook is the last
document that should go stale.

**D-089 — A backup nobody has restored is a file, not a backup.**
The backup section is a six-step drill with a written record, not a schedule.

**D-090 — Every command in a runbook is under test.**
If a script is renamed, the document fails the build rather than misleading the next
operator.

**D-091 — A guide has the same shape as every other guide.**
Five sections, always. A guide that invents its own shape is a guide nobody reads
twice.

**D-092 — The 'what the software will not let you do' section earns its place.**
A refusal is alarming when it is unexpected and unremarkable when it is written down.
A registration clerk who knows she cannot edit a clinical record does not file a ticket
about it.

**D-093 — Help is a drawer, not a page.**
Leaving a screen to read about the screen is how somebody loses the patient they were
registering.

**D-094 — Help topics live in the repository, not the database.**
They are part of the release and reviewed like code. A help text that changes without
a release is one nobody has read before it shipped.

**D-095 — A path parameter needs a prefix, not a set entry.**
Third time this has bitten: setup (B22), and now help. `AUTHENTICATED_ONLY_PREFIXES`
exists so the next one has somewhere to go.

**D-096 — A generated document cannot lie, but only if the build compares it.**
The reference is deterministic so a test can regenerate and diff it. Without the diff,
generation is a habit rather than a control.

**D-097 — A check that has never failed is not a check.**
The drift test exercises `--check` against a deliberately stale file, so the failing
path is known to work.

**D-098 — The tutorial never touches a real patient.**
It asks for a Tutorial Patient and the checks look only at whether the step has been
done, not at which record was used. A tutorial that damages the record is not a
tutorial.

**D-099 — Progress is read from the database, not tracked in the browser.**
A step is done when the hospital has done it, whoever did it. Closing the laptop does
not reset it and the person can continue on another machine.

**D-100 — A ratchet moves deliberately or not at all.**
B15's cap on login-only routes went from three to four, and the test now names all four
and what each returns about the caller. The next addition has to justify itself in the
same place.

---

## 8. Resuming after a break

1. Read section 1. If the branch and head commit differ from what is listed, the
   world moved: find out why before writing code.
2. Run the suite. If the number differs from section 1, something changed
   without a batch — treat that as a finding, not a nuisance.
3. Read the last three rows of the batch log and the last two decisions.
4. Read `HHMS_BUILD_PLAN.md` for the next batch only. Do not read the whole
   plan; that is how you start redesigning wave 7 while wave 1 is unfinished.
5. Run the ritual if three or more batches have landed since the last one.

---

## 9. What "done" means for v1.0

Seven conditions, from the build plan, repeated here because they are the thing
the ritual must not erode:

1. A stranger installs an OPD-only clinic in under fifteen minutes without
   editing a file, and the first prescription prints the hospital name and the
   doctor's NCH registration number.
2. Every module switches off and on from the interface, and switching one off
   never deletes a record or breaks another module.
3. Every write is attributable: who, what, before, after, when, from where.
4. Every route refuses a user who lacks its permission, and an unguarded route
   fails closed.
5. Pharmacist, laboratory, billing and records each land on a worklist of their
   own work.
6. The quality board shows 32 indicators with targets, validation states and
   twelve months of trend, and exports the QCI evidence structure.
7. The suite passes, the docs match the code, and no claim in `SECURITY.md` or
   the README is untrue.

---

**End of Document — HHMS Control**
