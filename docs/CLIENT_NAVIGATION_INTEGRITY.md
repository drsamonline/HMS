# Client Navigation Integrity — Batch 21

## Purpose

This batch extends the RBAC work from top-level navigation to patient-record tabs.

### Record-level access

Clinical, IPD, Investigations, Billing, MRD and Reports/Print tabs carry permission keys and are hidden/disabled when the authenticated profile does not have access.

The server remains authoritative for authorization. Client-side RBAC controls navigation and reduces accidental access attempts.

### Markup cleanup

The application shell previously loaded `dashboard.js` twice and contained duplicate body/script markup. Batch 21 leaves a single application bootstrap and a single dashboard module load.

### Empty and denied states

A denied record section produces a harmless client-side message instead of attempting the protected module. Missing clinical data continues to be a valid empty state.
