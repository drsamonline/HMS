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
| Branch | `batch-00-quick-wins` |
| Base commit | `2ee5c83` (v0.0.2, `main`) |
| Head commit | `b9d79a1` (code) + the control commit that carries this file |
| Tests | **590 passed, 2 skipped** (569 baseline + 21 new) |
| Wave complete | Wave 0 — quick wins (B01–B06) |
| Next batch | **B07 — audit schema v2** |
| Blocking decision | none |
| Open question | whether to push `batch-00-quick-wins` and open a PR |

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

Suite counts are cumulative at the end of each commit and reconcile to the 569
test baseline plus 21 new tests. Final: **590 passed, 2 skipped**.

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
