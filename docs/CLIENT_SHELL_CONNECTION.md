# HHMS Client Shell & Connection

The client provides a compact connection shell before the clinical workspace is loaded.

- LAN discovery is performed by the native C# host.
- JavaScript may fall back to a manually entered HTTP/HTTPS server URL.
- The selected address is persisted locally.
- The existing readiness endpoint is used to validate the server.
- The native host stores WebView2 user data under Local AppData rather than the installation directory.
- The clinical workspace is intentionally separate from the connection screen.
