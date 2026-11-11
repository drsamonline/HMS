# Administrator

You own the installation, not the medicine. When something is broken, missing or
wrong at the level of the software itself, it is yours.

## What you see when you log in

**Hospital Overview**, because your job is the whole hospital rather than one screen.

## Your first hour

1. Open **Administration** and look at who has an account and what role they hold.
2. Open **Settings** and read the configuration. Do not change anything yet.
3. Open **System Health** and check the last backup.

## Your first week

- Read `docs/OPERATIONS.md`. It is written for you and assumes no prior knowledge.
- Run the backup drill in section 3 of that document. Once. Before you need it.
- Learn what the setup code was and confirm it no longer works. If setup was never
  completed, complete it - an installation in setup mode is open to whoever reaches it
  first.
- Learn that a setting which needs a restart says so. The configuration screen shows
  the stored value and, separately, whether the running server has picked it up.

## What you must never do

- **Never share the administrator account.** One account, one person. The audit trail
  is worthless if the administrator login is a shared password.
- **Never disable the audit trail or the hash chain** to make a problem go away. It is
  the one control that makes every other claim checkable.
- **Never restore a backup over a running server.** Stop it, restore, start, then run
  the health check.
- **Never enable a module the hospital has not been licensed for.** The software will
  refuse; the refusal is the licence working, not a fault.

## What the software will not let you do

You cannot delete the audit trail, you cannot shorten a certificate's retention, and
you cannot enable a module outside your edition. Those three refusals are deliberate:
each of them would make a claim the hospital makes unverifiable.
