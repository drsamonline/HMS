# HHMS Client Native Host

This is the native Windows host for the HHMS HTML/CSS/Vanilla-JavaScript client.

## Responsibilities

- Host the frontend in WebView2.
- Provide the `window.hhms.discovery.discover()` bridge required by the frontend.
- Perform UDP discovery from native Windows code.
- Pass discovered server metadata back to JavaScript.
- Never access the HHMS database directly.

## Build target

The project targets `win-x64`, .NET 8, self-contained single-file publishing.

WebView2 is a client runtime dependency. Fixed-runtime bundling is a later packaging step; this batch intentionally establishes the host/bridge API first.
