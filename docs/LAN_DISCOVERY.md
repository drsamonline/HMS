# HHMS LAN Discovery

HHMS server discovery uses a small native UDP protocol so the client does not require mDNS, Node.js, or third-party discovery services.

## Protocol

- UDP port: `DISCOVERY_PORT` (default `38541`)
- Request payload: `HHMS_DISCOVER_V1`
- Response protocol: `hhms-lan-v1`
- Response contains server ID, server name, HTTP port and API base.

## Security boundary

Discovery exposes connection metadata only. Authentication remains an HTTP/API concern. The client must never treat discovery as authentication or authorization.

## Fallback

Automatic discovery is an optional convenience. The future HHMS client must also support manual server address configuration.
