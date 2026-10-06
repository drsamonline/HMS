# Client Runtime Resilience

The client distinguishes authentication expiry from transient network/server loss.

- `401` responses clear the session and emit `hhms:auth-expired`.
- Successful API responses emit `hhms:server-state` with `online=true`.
- Network/fetch failures emit `hhms:server-state` with `online=false`.
- Browser `online`/`offline` events update connection state.
- After network recovery, the client performs a health check before hiding the runtime banner.
- The runtime banner is non-blocking and does not discard unsaved UI state by itself.

The backend remains authoritative for authorization.
