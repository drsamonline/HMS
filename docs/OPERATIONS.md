# Operating an HHMS server

This is the runbook for the person who owns the machine, not the person who uses the
software. It assumes Windows unless a step says otherwise, because that is what
hospitals buy.

It does not repeat what is already written down. Each section points at the document
that owns its subject, so there is one place to change when something changes:

| Subject | Document |
|---|---|
| Deployment scripts and frozen runtime | `scripts/deploy/README.md` |
| Rotating the signing key | `docs/SECRET_ROTATION_RUNBOOK.md` |
| Archive and retention tiers | `docs/ARCHIVE_RETENTION_TIERS.md` |
| Annual case rollover | `docs/ANNUAL_CASE_ROLLOVER.md` |
| Backup workspace in the client | `docs/CLIENT_BACKUP_WORKSPACE.md` |
| Staff-facing training | `docs/ADMIN_TRAINING.md` |
| What NABH can be evidenced | `docs/NABH-MAPPING.md` |

---

## 1. First install

A fresh machine, no data, nobody yet configured. The whole sequence is four steps and
one of them is reading a number out of a log file.

**1. Install and start the server.**

    scripts\deploy\server-launch.ps1

On Linux or macOS, or for a source deployment, use `scripts/deploy/install-first-run.sh`.
Both scripts create the `data/` tree, persist the signing key, run the migrations to
head, and assert the `/health` version handshake before declaring success.

**2. Open the client and point it at the server.** On the same machine, the client
finds it automatically. On a LAN, see section 2.

**3. Read the setup code from the server log.** The first time the setup page is
opened, the server writes a six-digit code to its log and nowhere else. It is valid
for one hour and locks after five wrong attempts. Search the log for `setup code`.

**4. Walk the ten steps.** Identity, data, network, numbering, money, wards,
departments, people, modules, review. The people step creates the first real
administrator - after that, the setup code has done its job and stops working.

**If the machine has no browser**, the same ten steps run from a shell:

    set HHMS_ADMIN_PASSWORD=...
    python -m app.cli.setup --hospital-name "..." --admin-username ... --admin-full-name "..."

The password comes from an environment variable and never from a flag, because a flag
lands in shell history and in the process list.

**What to write down before you leave the building:** the administrator username, the
setup code is *not* needed after step 4, and where the `data/` directory is.

---

## 2. The LAN

A hospital runs one server and several clients. Two things have to be true.

**The server must be reachable.** Set `SERVER_PORT` in the wizard's network step or in
`data/pending-network.json` before finishing setup; the value is written into a marked
block in `.env` and takes effect on the next restart. The wizard tells you when a
restart is required - the setting screen shows a stored value that the running process
has not picked up yet.

**Discovery must find it.** With `DISCOVERY_ENABLED` on, a client on the same subnet
finds the server without being told an address. If it does not, the cause is almost
always one of:

| Symptom | Usual cause |
|---|---|
| Client sees no server | Server and client on different subnets, or the switch blocks broadcast |
| Client sees the server but cannot connect | A firewall rule on the server's port |
| Client connects to the wrong server | Two installations on one subnet; change `DISCOVERY_NAME` on one |

---

## 3. Backups, and the drill that makes them real

**A backup nobody has restored is a file, not a backup.** The drill below is the
point of this section; the schedule is secondary.

**The schedule.** Daily automatic backup is a setting (`AUTO_BACKUP_ENABLED`). The
client's backup workspace lists what exists and lets you take one by hand.

**The drill, quarterly, and after any hardware change:**

1. Take a backup. Note its filename and size.
2. On a different machine, install HHMS and stop the server before first run.
3. Restore the backup into that machine's `data/` directory.
4. Start the server. It must pass the `/health` handshake.
5. Log in as the administrator and open three things: a patient you know exists, the
   most recent invoice, and the audit trail.
6. Write down the date and who did it. An assessor will ask.

If step 5 fails, the backup is not a backup and the schedule is irrelevant.

---

## 4. Maintenance

**Nightly, automatic.** The audit hash chain is verified and a failure is logged at
error level. A break in the chain means the trail was altered outside the application,
which is the one thing the trail exists to detect.

**Monthly, by hand.** Run the orphan sweep and read the configuration health:

    python scripts\orphan_sweep.py
    python -m app.cli.config keys

**Annually, before the new financial year.** The operational year rollover moves
closed years into the archive tiers. Follow `docs/ANNUAL_CASE_ROLLOVER.md`; do not run
the rollover and a restore on the same day.

**When the software is updated.** Check the edition and the migration head:

    python -m alembic heads

There must be exactly one head. Two heads means a migration was edited rather than
added, and the database will not upgrade cleanly.

---

## 5. Troubleshooting

Work down this list before calling anyone. Each step says what a good answer looks
like, so you know when to stop.

| # | Check | Good answer | If not |
|---|---|---|---|
| 1 | `GET /api/v1/health` in a browser | `status: ok` with a version | Server is not running; see the log in `data/logs/` |
| 2 | Is the disk full? | Plenty free | The server will fail to write; free space first, then restart |
| 3 | `GET /api/v1/edition` | The edition you bought | Wrong `HHMS_EDITION` in `.env` |
| 4 | Can you log in? | Yes | Check the account is active and the clock is right - a skewed clock invalidates tokens |
| 5 | Is the menu short? | Screens you expect | Your role lacks the permission, or the module is not enabled. `GET /api/v1/navigation` shows what the server thinks you have |
| 6 | Did a setting not take effect? | `GET /api/v1/configuration/restart-status` is empty | Restart the server; the value is stored but the process has the old one |
| 7 | Do numbers repeat or skip? | They do not | Someone reset a sequence. `docs/CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md` |
| 8 | Is the audit trail intact? | The nightly verifier is quiet | Stop. A broken chain is not a support call, it is an incident |

**The log is the first thing to read, not the last.** It carries the setup code on a
fresh install, the audit chain result each night, and every request that failed with a
request id you can quote.

---

## 6. Handing over

When the machine changes hands, four things change with it:

1. **The administrator password** - rotate it, and rotate the signing key with
   `scripts/deploy/rotate-secret-key.ps1`.
2. **The setup code** - it is dead already if setup was completed; if it was not,
   complete setup before handing over.
3. **The backups** - the new owner must know where they are and must have run the
   drill in section 3 at least once.
4. **The documentation** - this file, the mapping, and the training guide. A hospital
   that cannot explain its own records to an assessor has a problem that starts the
   day the vendor leaves.

---

## What this runbook assumes, and what it does not

It assumes one server, a LAN, and Windows clients. It does not cover a multi-site
deployment, a cloud host, or a database other than the one HHMS ships with - none of
those are supported, and a runbook that described them would be fiction.

Every command above exists in this repository. A test asserts it: if a script is
renamed, this document fails the build rather than misleading the next operator.
