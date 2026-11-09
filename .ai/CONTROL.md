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
| Branch | `batch-02-enumeration` (stacked on `batch-01-accountability`) |
| Base commit | `2ee5c83` (v0.0.2, `main`) |
| Head commit | `66e085d` (B15) + the control commit that carries this file |
| Tests | **679 passed, 2 skipped** (569 baseline + 110 new) |
| Wave complete | Waves 0, 1 and 2 (B01–B15); wave 3 next |
| Next batch | **B15a — memoise the permission set** |
| Blocking decision | none |
| Open question | none. Ritual due after B17 (third batch since B14) |

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

Suite counts are cumulative at the end of each commit and reconcile to the 569
test baseline plus 110 new tests. Final: **679 passed, 2 skipped**.

From B14 the suite takes longer than one 300-second call, so it is run in four
file-list chunks and the counts summed. Every file runs exactly once.

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
