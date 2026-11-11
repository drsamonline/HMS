# Code audit — 2026-11-11

A review of the whole repository at the close of the build plan, and of the licensing
and compliance work that followed it.

This is a working audit, not a certificate. It records what was checked, what was
found, and - importantly - what could not be checked in the time available. A finding
marked **unverified** is not a clean bill of health.

## How this was done

Mechanical checks first, because they do not get tired:

| Check | Method |
|---|---|
| Bare `except:` | `grep -rn "except:"` |
| `eval` / `exec` | `grep -rn "eval(\|exec("` |
| SQL built by f-string | `grep -rn 'execute(f"\|text(f"'` |
| Unguarded routes | the generated `docs/API_REFERENCE.md` |
| Committed secrets | `git ls-files` against `data/secret.key` |
| Debug prints in the server | `grep "^\s*print("` outside `cli/` |
| Dead markers | `TODO`, `FIXME`, `XXX`, `HACK` |
| Oversized modules | `wc -l` |

Then by reading: the authentication and permission path, the setup gate, the licensing
verifier, and the print path - the four places where a mistake is a security or safety
problem rather than a bug.

## Findings

### F-01 — A well-known default administrator password can be set, and nothing forces a change

**Severity: high. Status: open.**

`backend/app/cli/create_admin.py` defines `DEFAULT_BOOTSTRAP_PASSWORD = "admin"`. When
`create-admin` is run without `--password` and without `HHMS_ADMIN_INITIAL_PASSWORD` on
a terminal that cannot prompt, it creates the administrator with that password, skips
the minimum-length check (`and not used_default`), prints a warning, and returns
success.

The warning is honest and loud. It is also the only control.

Why it matters: this is a LAN hospital product. A server reachable on the hospital
network with `admin` / `admin` is not a hypothetical - it is the default outcome of
running one command on a machine where the operator did not read the output.

The setup wizard (B22–B26) is the safe path: it requires a code from the server log and
a password chosen by the person completing it. The CLI predates it and remains as the
headless escape hatch.

**Recommendation.** Refuse to create a default-password account unless an explicit
`--allow-default-password` flag is passed, and have that flag print the same warning
before doing anything. A test asserts the refusal.

### F-02 — The permission system fails closed, but the failure mode is a 403 that reads like a bug

**Severity: low. Status: by design, documented.**

`PERMISSION_ENFORCEMENT` defaults to `enforce`. A route with no declared permission is
refused by default, which is the right choice and is why `docs/API_REFERENCE.md` reports
**zero unguarded routes**.

The cost is that forgetting `require()` on a new route produces a 403 with the message
"This route declares no permission guard and is refused by default" - which reads like a
defect to whoever hits it, because it is one, on the server side. That is the intended
trade and is worth keeping.

### F-03 — Broad exception handlers: 42 of them

**Severity: low. Status: reviewed, mostly correct.**

Every one reviewed in the security-relevant paths is deliberate:

| Location | Handler | Verdict |
|---|---|---|
| `middleware/logging.py` | logs and re-raises | correct - a logging failure must not swallow a response |
| `dependencies/setup.py` | any decode failure → 401 | correct - a bad token is a bad token whatever the reason |
| `cli/*` | top-level boundary → exit code | correct for a command line |

The remaining ones are in CLI entry points, the desktop console and the archive
manager. None of them is in a request path that decides access.

### F-04 — One module is 2,573 lines

**Severity: medium. Status: open.**

`backend/app/api/v1/endpoints/dashboard.py` is 2,573 lines, and
`services/reporting.py` is 1,235. Everything else is under 1,500 and most are far
smaller.

This is not a correctness problem today - the tests cover it - but it is where the next
person will make a mistake, and it is the module most likely to conflict when two
changes land in the same week.

**Recommendation.** Split `dashboard.py` by the data it serves, not by size: the
clinical feeds, the billing feeds and the statistical feeds are three things that happen
to share a router.

### F-05 — Frontend escaping: every module has a helper, coverage unverified

**Severity: unknown. Status: unverified.**

Every JavaScript module that writes HTML defines or imports an escape helper. There are
109 `innerHTML` assignments across `frontend/js/`.

I did not verify that each of those 109 escapes every interpolated value. A mechanical
pass is possible - the newer components already do it, and the pattern `escapeHtml(x)`
is greppable - but it is a dedicated afternoon, not a line in an audit, and claiming it
without doing it would be the worst outcome of this document.

**What is known:** the components written during this build (`ui/dialog.js`,
`ui/states.js`, `ui/table.js`, `ui/help.js`, `ui/tutorial.js`,
`ui/institute-registrations.js`, `ui/prescription-print.js`) escape every value they
render, and two of them are covered by tests that assert it.

**What is not known:** the older workspace modules - `dashboard.js`, `print.js`,
`admin.js` - where the markup is built inline and there is more of it.

### F-06 — The audit trail's hash chain is verified nightly, and a break is not surfaced

**Severity: medium. Status: by design, but worth revisiting.**

`audit_chain.py` verifies the chain and logs at error level when it breaks. A hospital
administrator will not read the log.

A break in the chain means the trail was altered outside the application - the one thing
the trail exists to detect. It should appear on a screen, the way the expiring
registrations now do.

**Recommendation.** Surface it in the superintendent's home as an alert panel, reusing
the pattern from B56.

## What was checked and found clean

| Check | Result |
|---|---|
| Bare `except:` | none |
| `eval` / `exec` | none |
| SQL built by f-string | none - all queries are parameterised or ORM |
| Unguarded API routes | none - 279 routes, every one declared |
| `data/secret.key` committed | no - gitignored, and the rotation runbook covers history |
| Debug `print()` in the server | only in `server.py`'s smoke test, which is its output |
| `TODO` / `FIXME` / `XXX` / `HACK` | none |
| Licence file verified offline | yes - RS256, tested against forged and foreign keys |
| Setup gate | code in the log, hashed at rest, 5-attempt lockout, 60-minute life |
| Permission default | deny, and the reference proves it route by route |

## What this audit does not cover

- **Penetration testing.** Nobody has tried to break this deliberately.
- **The C# client.** `client/HHMS.Client` was not reviewed in this pass.
- **Dependency vulnerabilities.** No `pip-audit` run; the pinned versions are unexamined
  for CVEs.
- **The frozen binary.** Behaviour under PyInstaller differs from source in ways the
  suite does not exercise.
- **Clinical correctness.** The software records what a clinician enters. Whether the
  homoeopathic record structure is clinically right is a question for a practitioner,
  not an audit.

## The honest summary

The security-critical paths - authentication, permissions, the setup gate, the licence
verifier, the audit chain - are in good shape, tested, and fail closed.

Two things should be fixed before the first sale: **F-01**, because a default password
on a LAN server is the most likely way this product harms a hospital, and **F-06**,
because a broken audit chain that nobody sees is the same as no audit chain.

**F-05 is the unknown.** It is the largest surface and the least examined, and this
document says so rather than implying otherwise.
