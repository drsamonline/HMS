# Unified Patient History

## Purpose

Provide one patient-history view that combines the live operational record with explicitly selected verified historical archive years.

## Rules

- Patient master data remains live regardless of encounter age.
- The current operational year remains live.
- Years 2–5 are online, read-only archives loaded on demand.
- Years 6–10 are cold archives accessed only when explicitly requested.
- Actual clinical timestamps remain authoritative.
- A renewed case in a new operational year is a new live CaseRecord in the same case family and links to the previous case.
- Historical case data is read-only through this history view.
- The application does not keep all archive databases attached during normal usage.

## Batch 55 correction

The original Batch 55 implementation was incomplete because it only changed the client timeline and did not provide a matching patient-history API. Batch 56 corrects that committed feature by adding the server-side patient-history contract and the client integration.
