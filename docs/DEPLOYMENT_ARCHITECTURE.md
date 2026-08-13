# HHMS Deployment Architecture

## 1. Purpose

This document defines the deployment architecture for the HHMS LAN client/server application.

## 2. Target Deployment

```text
Hospital LAN

          +----------------------+
          |   Server Computer    |
          |   HHMS-Server.exe    |
          |   FastAPI + SQLite   |
          +----------+-----------+
                     |
                  LAN HTTP
                     |
        +------------+------------+
        |                         |
+-------+-------+         +-------+-------+
| Client PC 1   |         | Client PC 2   |
| HHMS-Client   |   ...   | HHMS-Client   |
+---------------+         +---------------+
```

## 3. Server

HHMS-Server.exe is responsible for:

- FastAPI application
- database access
- migrations
- authentication
- business services
- reporting
- file/document management
- audit logging

The server is the only component that opens the database.

## 4. Client

HHMS-Client.exe provides the application UI.

The client contains:

- native Windows host
- embedded HTML/CSS/JavaScript frontend
- API client
- LAN server discovery/configuration

The client never accesses SQLite directly.

## 5. Database

SQLite is the primary database for the portable LAN deployment.

The database shall live on the server computer in an application-data location rather than inside source code.

PostgreSQL compatibility may remain available for future deployments, but PostgreSQL is not required for the portable LAN release.

## 6. LAN Discovery

The client shall attempt automatic discovery of the HHMS server on the local network.

A manual server address and port configuration shall be available as a fallback.

## 7. Offline / Network Behaviour

HHMS is offline-first with respect to internet connectivity: normal hospital operation must not require cloud services.

A client requires the HHMS server to be reachable for shared hospital data operations. The client must clearly report server-unavailable conditions and must not silently create a second database.

## 8. Packaging

The final deployment target is:

- one server executable/bundle
- one client executable/bundle

Application dependencies must be packaged with the appropriate executable/bundle so that end users do not need a separate Python, Node.js, or development environment.

The WebView2 runtime packaging strategy will be finalized during the client packaging milestone.

## 9. Configuration

Environment-specific settings must not be hard-coded.

Server configuration includes:

- database location
- server bind address
- server port
- JWT secret
- logging level
- uploads/documents location
- backup location

Client configuration includes:

- discovered/configured server address
- server port
- client-specific preferences

## 10. Backup

The server is responsible for database and uploaded-document backups.

Backups must be stored outside the active database location and periodically verified.

## 11. Startup

The production release shall provide a simple server startup mechanism suitable for a hospital server PC.

Whether this is a desktop process or Windows service will be finalized during the packaging milestone.

## 12. Security

LAN communication must use authenticated API access.

Database credentials are never exposed to clients.

Secrets are never embedded in source code or the client executable.
