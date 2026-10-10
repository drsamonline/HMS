# Client Statistics and Reports / Printing — Batch 14

Adds authenticated client integration for hospital statistics and the existing backend report/print-data APIs.

## Statistics
- Inclusive date filters.
- Optional department/service filters.
- Unique patient totals remain distinct from activity totals.
- Department and service breakdowns are displayed.

## Reports / Printing
- Report catalog is loaded from the backend.
- Complete or selected report sections can be prepared.
- Print manifests and report envelopes are shown as structured preview data.
- Date-range case reports are supported.
- Actual rendering, pagination and Windows printing remain client-rendering concerns.

Empty result sets are displayed as valid no-data states.
