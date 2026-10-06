# IPD Bed Occupancy Concurrency

Admission and discharge operations lock the affected bed/admission rows and the database adds a partial unique index preventing two active admissions from occupying one bed.

Normal workflow:
1. Lock bed.
2. Verify bed state.
3. Verify no active admission.
4. Create admission and mark bed occupied in one transaction.
5. On discharge, lock admission and bed, create discharge, mark admission discharged, and release bed in one transaction.

This prevents double-allocation at the application layer and adds a database-level guard.
