# Client Unsaved Changes

The client keeps an in-memory dirty flag for editable forms.

- Form input/change events mark the workspace dirty.
- Successful clinical saves clear the flag.
- Browser/WebView2 close/navigation receives the native before-unload warning when possible.
- Internal client navigation asks for confirmation before discarding dirty input.
- The flag is never persisted as clinical data.
- Network loss does not automatically discard the form.
