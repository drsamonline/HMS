# HHMS UI Guidelines

## Current UI stack

- HTML5
- CSS
- Vanilla JavaScript
- WebView2 native Windows host

The client is intentionally lightweight. Do not introduce React, Vite, Tailwind, or another UI framework without a new architectural decision.

## Layout

- Dashboard and module shell
- Left navigation for primary modules
- Compact cards and forms
- Responsive grid layouts where useful
- A4-oriented print styles separate from application styles

## UX rules

- Empty data must produce a safe empty state, not an exception.
- Forms should be compact and keyboard-friendly.
- Long narrative clinical fields remain typable text areas.
- Structured fields are used only when they reduce entry time.
- Error messages must be visible and actionable.
- Loading states must not block unrelated navigation.
- Unsaved clinical content must be protected from accidental navigation where practical.

## Print UI

- Keep print controls in `.no-print` containers.
- Use the dedicated print stylesheet.
- Do not assume physical page counts in JavaScript.
- Allow whole-report and selected-section printing.
