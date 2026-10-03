# Client Print Renderer

The client now renders the backend print manifest and report envelope into an A4-oriented HTML print preview.

## Capabilities

- Whole supported report or selected sections.
- Section selection before printing.
- Manifest-controlled section labels and logical page breaks.
- Print-safe HTML/CSS.
- Browser/Windows `window.print()` integration.
- No PDF or printer dependency in the backend.
- Empty report sections render as a non-blocking empty state.

The renderer does not guess physical page counts. Actual pagination remains controlled by the browser's print engine, paper size, margins, installed fonts and printer configuration.

## Flow

```text
Report API
    ↓
Print Manifest + Envelope
    ↓
Client Print Renderer
    ↓
Section Selection
    ↓
HTML Preview
    ↓
window.print()
```
