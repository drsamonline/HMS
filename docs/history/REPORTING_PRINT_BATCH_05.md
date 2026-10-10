# Reporting / Print Batch 05 — Print Manifest

Adds a backend print manifest so the client can render whole-case or selected-section output without hard-coding report ordering.

## Endpoint

`POST /api/v1/reports/clinical-data/print-manifest`

## Scope modes

- `complete_case` when no sections are specified.
- `selected_sections` when explicit sections are supplied.

## Print blocks

Each block exposes its section key, user-facing label, page group, print order and whether a page break should precede it. Actual pagination remains a client concern because page count depends on renderer, font metrics and printer settings.
