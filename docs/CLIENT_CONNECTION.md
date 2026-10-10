# HHMS Client Connection Foundation

## Scope

This batch establishes the lightweight HTML/CSS/JavaScript connection layer used by the future `HHMS-Client.exe`.

The frontend does not open SQLite and does not contain database credentials.

## Connection order

1. Load a saved manual server URL, if configured.
2. Otherwise ask the native client host for LAN discovery through the optional `window.hhms.discovery` bridge.
3. If no discovery result is available, show a clear server-not-found state.
4. When a server URL is available, call `GET /api/v1/health/ready`.
5. Persist the selected server URL for the current client.

## LAN discovery boundary

Browser JavaScript cannot perform the HHMS UDP discovery protocol directly. The future native Windows host provides the bridge:

```text
window.hhms.discovery.discover()
```

The bridge should return an object containing at least:

```json
{
  "baseUrl": "http://192.168.1.10:8000/api/v1"
}
```

The server-side UDP responder remains the discovery authority.

## Manual fallback

The client must expose a manual server-address setting later in the UI. The connection module already supports a persisted `manualServerUrl`.

## Health check

The first connection check is the existing:

`GET /api/v1/health/ready`

The client treats discovery as connection metadata only. Authentication remains an API concern.

## Packaging

This batch intentionally does not choose a final WebView2 packaging implementation. The next client-host milestone can embed this frontend and expose the discovery bridge while preserving this API contract.
