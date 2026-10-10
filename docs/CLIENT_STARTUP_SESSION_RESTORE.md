# Client Startup and Session Restore — Batch 24

The client startup path now prefers a saved manual server address before launching LAN discovery. If the saved server is unavailable, discovery remains the fallback.

When an access token exists in the current WebView2 session and a server can be reached, the existing `/auth/me` profile is restored and the workspace can reopen without forcing unnecessary rediscovery.

No long-lived credential is introduced. The JWT remains session-scoped. This is a startup/reconnection improvement, not persistent authentication.
