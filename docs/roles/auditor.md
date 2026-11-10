# Auditor

You read. You do not write. Everything you need is a record somebody else created, and
your job is to say whether it holds together.

## What you see when you log in

**Audit.** What happened, when, and by whom.

## Your first hour

1. Open **Audit / Activity** and read the last twenty entries. Note that each carries
   an actor, an action, before and after values, and a request id.
2. Filter to one user and read a day of their work.
3. Open **Statistics** and see the indicators with their definitions attached.

## Your first week

- Learn that the audit trail is append-only and hash-chained. A break in the chain is
  not a display problem; it means the trail was altered outside the application.
- Learn that every indicator names what it counts and what it divides by. If a number
  cannot be explained from its own definition, that is a finding.
- Learn which duties the hospital must evidence, and which it cannot yet. The mapping
  is in `docs/NABH-MAPPING.md` and it is deliberately harsh.

## What you must never do

- **Never accept a number you cannot trace to a definition.** "It comes from the
  system" is not an answer an assessor accepts, and it should not satisfy you.
- **Never ask for a record to be corrected before you have read it.** A correction is
  itself evidence.
- **Never treat a missing indicator as a zero.** The software reports "no data"
  separately from "0" for exactly this reason.

## What the software will not let you do

You cannot change a record, prescribe, dispense or bill. Your role is read and export,
which is why you can be given access to everything without being able to alter any of
it.
