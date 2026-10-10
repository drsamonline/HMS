# HHMS Native Client Host

## Purpose

Batch 05 creates the native Windows host required by the LAN client architecture.

```text
HHMS-Client.exe
   |
   +-- WebView2
   |
   +-- frontend/index.html
   |
   +-- native discovery bridge
   |
   +-- HTTP/JSON API client in JavaScript
   v
HHMS-Server.exe
```

## Discovery bridge

The native host listens for JavaScript messages requesting discovery, sends the `HHMS_DISCOVER_V1` UDP broadcast, validates `hhms-lan-v1` responses, and returns the server URL and identity metadata to the web UI.

The browser layer therefore never needs UDP permissions or direct socket access.

## Packaging boundary

The host is configured for self-contained `win-x64` single-file publishing. A later packaging batch will verify the exact WebView2 runtime strategy and produce the deployment bundle for hospital PCs.
