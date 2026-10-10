# HHMS Administrator Training Manual

Operational handbook for the clinic's HHMS administrator: first-time setup,
day-1 configuration, user/role management, backups, and recovery. Pair this
document with a hands-on walkthrough on the clinic's own hardware.

Audience: internal IT owner or designated clinic administrator. Users of the
system should read [USER_GUIDE.md](USER_GUIDE.md) instead.

Related documents: [SERVER_STARTUP.md](SERVER_STARTUP.md),
[SERVER_PACKAGING.md](SERVER_PACKAGING.md), [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md),
[SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md), [CLIENT_BACKUP_WORKSPACE.md](CLIENT_BACKUP_WORKSPACE.md).

---

## 1. Architecture you are responsible for

```text
HHMS-Server.exe (one Windows PC)  ◄── LAN HTTP/JSON + UDP discovery ──►  HHMS-Client.exe (each workstation)
        │
        └── data/ (SQLite DB, secret.key, uploads, backups, logs — server-owned; nobody else touches it)
```

- The **server** is the only component that opens the database. Clients are thin
  WebView2 shells over the same HTML/CSS/JS UI.
- Data lives under a *user-writable* application root (`%LOCALAPPDATA%\Programs\HHMS\data`
  by default for no-admin installs); the installer never deletes it on uninstall,
  so patient data survives upgrades and reinstalls.

## 2. Installing the server

1. On the host PC, run `HHMS-Setup-<version>.exe` (built by
   `scripts/deploy/build-installer.ps1`; ships the server EXE; add the client
   launcher with the `-IncludeClient` switch at build time). No administrator
   rights are required.
2. Start **HHMS Server** from the Start Menu. First launch runs all database
   migrations automatically (fresh install bootstraps the full chain to head)
   and starts the HTTP listener on the LAN port (default 8000).
3. Verify health: open `http://<server-ip>:8000/api/v1/health` in any browser —
   expect `status: ok` and the release version matching the `VERSION` file.
4. Firewall: allow inbound TCP 8000 (HTTP) and UDP discovery on the private
   network profile only.

### Client workstations
1. Copy/install **HHMS-Client.exe** (bundled frontend content sits beside the EXE).
2. Prerequisite: Microsoft Edge **WebView2 Runtime**. Modern Windows 10/11
   installations include it; otherwise deploy the Evergreen runtime, or use the
   offline CAB redistributable for internet-isolated machines (open item tracked
   in ROADMAP Milestone 7 — until bundled, stage the standalone
   `MicrosoftEdgeWebView2RuntimeInstaller` on the LAN file share).
3. Launch — the client auto-discovers the server via UDP (`HHMS_DISCOVER_V1`);
   manual IP entry is the fallback.

## 3. Day-1 configuration checklist

Work through these before going live (Administration workspace unless noted):

1. **Clinic identity & settings** — hospital name/address (appears on print
   envelopes), date/time conventions, number-sequence prefixes for UHID/tokens/
   invoices.
2. **Departments & designations** — create departments; attach department
   services (consultation/procedure rates feed billing).
3. **Masters** — medicine batch master, investigation catalogue, stock items for
   inventory/pharmacy.
4. **Users & roles** — see §4. Create one account per person; never share.
5. **Printers** — on each workstation set the OS default printer and print one
   test envelope (invoice sample) to confirm layout.
6. **Backup schedule** — configure and verify (§6) on day 1, not week 2.
7. **Secret key** — the server creates `data/secret.key` used to sign session
   tokens. Treat it like a safe combination: never email it, never copy it to
   other machines, keep it out of shared folders. *(For production releases:
   rotate the key if it ever existed in a repository — see SECURITY.md.)*

## 4. Users, roles, and access control

- **Create users** in Administration → Users: username, display name, password
  (argon2-hashed server-side; the admin never sees it back), assign role(s).
- **Roles** carry permissions (`permission.*` strings such as `patients.read`,
  `billing.read`). The client navigation gate consumes the live profile from
  `GET /auth/me`: modules appear only if the role grants them. Roles marked
  inactive stop granting access immediately on next sign-in.
- **Blanket-access roles**: `admin`, `administrator`, `hospital administrator`,
  `super administrator` (case-insensitive) see every module. Reserve these for
  the smallest possible group.
- **Deny-by-default**: a profile that fails to load shows nothing rather than
  everything — safe failure is expected behavior; investigate why the profile
  call failed (expired token, server down).
- Changing someone's role takes effect at their next sign-in (profile is fetched
  live; there is no cached client-side ACL to clear).
- Deactivate (don't delete) accounts of departed staff to preserve audit
  attribution.

## 5. Daily operations

- **Activity log**: every write is attributed; review after incidents or weekly.
- **Dashboards**: outstanding invoices, pending investigations, ward occupancy,
  settlement/refund audits — useful Monday-morning checks.
- **Login throttling**: brute-force protection blocks >10 failed logins/min per
  source (tunable via `LOGIN_RATE_LIMIT_ATTEMPTS` / `LOGIN_RATE_LIMIT_WINDOW_SECONDS`
  environment variables on the server). Repeated legitimate lockouts usually mean
  a misconfigured workstation script, not an attack — check before raising limits.
- **Server updates**: stop the server, run the newer `HHMS-Setup` package over the
  old install (data folder untouched), start again; migrations run automatically.
  Take a manual backup first anyway (§6).

## 6. Backups

Use the **Backups** workspace (admin-only; every verb requires a genuine active
administrator role):

- **Create backup** — point-in-time snapshot of the database into the server's
  backups directory. Do this daily during heavy use, and always before an update.
- **Download** — pull a `.zip`/DB archive byte-exact copy to off-machine storage
  (USB drive rotated weekly, or a LAN share the server process can reach).
- **Import** — place a previously exported archive back into the server. Corrupt
  or non-SQLite uploads are rejected without polluting the backups directory.
- Restores automatically take a pre-restore safety snapshot first (kept out of
  the normal listing).

Retention suggestion: daily × 14, monthly × 12, one copy off the server machine.

## 7. Restore / disaster recovery drill (quarterly)

1. Stop the server app.
2. Start it against its normal data root, sign in as admin.
3. Backups → select the newest verified archive → **Restore**, confirm.
4. Sign in on a client; spot-check: latest registered patient, latest invoice,
   today's OPD tokens.
5. Re-run a fresh **Create backup** once satisfied (post-restore baseline).

Whole-machine loss: reinstall Windows + HHMS setup on new hardware, copy the last
off-machine download into the backups/import location, restore, verify. Patient
data survived because it lived outside the program files and was exported
regularly. Time the drill; a restore you have never practiced is not a backup.

## 8. Troubleshooting escalation matrix

| Symptom | First checks | Escalate when |
|---------|-------------|---------------|
| Clients can't find server | Server running? Same subnet? Firewall on host? | Port reachable but discovery silent → check UDP  broadcast blocking on managed switches |
| Health endpoint slow/errors | Disk space on data volume; antivirus scanning SQLite file | Persistent 500s → capture server console output + time of onset |
| One user sees no modules | Did their role change/inactivate? Sign out/in | Profile API returns 401 despite valid login → forward token expiry details (not the token itself) |
| Restore fails | Is the archive from a compatible version? File intact (re-download)? | Error names missing tables/columns → collect exact message; may indicate version mismatch needing developer help |
| Suspected credential stuffing | Rate limiter already caps attempts; review Activity log | Lockouts continue across many accounts → isolate host, contact security lead |

## 9. Security hygiene (non-negotiable)

- Keep `data/secret.key` and backups encrypted-at-rest where policy allows;
  never commit either to source control.
- Use unique passwords per role; force a change if a workstation is shared out.
- Patch Windows (WebView2 runtime updates ride on Edge servicing).
- Audit-user-list quarterly; deactivate dormant accounts.
- Before any external release of installation media, rotate signing secrets and
  (see `docs/SECRET_ROTATION_RUNBOOK.md` and `scripts/deploy/rotate-secret-key.ps1`)
  strip history containing them (see the standing note in ROADMAP Milestone 7).
