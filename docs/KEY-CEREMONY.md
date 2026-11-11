# Making your licence key

This is the last thing standing between the software and the first sale. It takes about
ten minutes and you do it once.

Written for somebody who has never done it. If a step does not work, the next section
says what probably went wrong.

---

## What this is, and why you are doing it

The software checks a licence file before it unlocks a paid edition. To check it, it
needs to know what a genuine licence looks like.

That is what a key pair is. Two halves:

| Half | Where it lives | What it does |
|---|---|---|
| **Private key** | On your computer only, never shared | **Signs** a licence. This is your stamp. |
| **Public key** | Inside the software you ship | **Checks** the signature. This is the wax seal everybody can see. |

You sign a licence with the private key, the hospital's copy checks it with the public
key, and no internet is involved.

**If the private key leaks, anybody can sign a licence and your paid editions become
free.** That is the whole risk, and the whole reason for the care below.

Right now the software ships with a *development* key — one that is in the public
repository, so anybody who downloads it can forge a licence. It is there so the software
runs during development. Replacing it is this document.

---

## Before you start

You need:

- The HHMS project folder on this computer
- Python installed (you already have it if you have run the server)
- Two folders: one for the project, one for the keys — **they must be different**

The second folder is the important one. Keys that live inside the project get committed
by accident, and a key in a repository is a key that is public.

---

## Step 1 — Make a folder for the keys, outside the project

Open **PowerShell** (press `Windows`, type `powershell`, press Enter).

```powershell
mkdir C:\HHMS-keys
cd C:\HHMS-keys
```

If you are on a Mac or Linux machine, the same thing:

```bash
mkdir -p ~/HHMS-keys
cd ~/HHMS-keys
```

**Check:** the prompt now shows `C:\HHMS-keys` (or `~/HHMS-keys`). If it still shows the
project folder, the `cd` did not work — type it again.

---

## Step 2 — Go to the project and install what the tool needs

Still in PowerShell, pointing at your project folder. Change the path to wherever yours
actually is:

```powershell
cd C:\path\to\your\HMS\backend
pip install -r requirements.txt
```

This takes a minute or two. If it says `pip is not recognised`, Python is not on your
PATH — reinstall Python and tick **"Add Python to PATH"** on the first screen.

---

## Step 3 — Generate the key pair

Still in `backend`, run:

```powershell
python -m app.cli.licence keygen --private C:\HHMS-keys\vendor-private.pem --public C:\HHMS-keys\vendor-public.pem
```

You should see:

```
private key: C:\HHMS-keys\vendor-private.pem  <- never commit this, never ship it
public key:  C:\HHMS-keys\vendor-public.pem  <- paste into backend/app/core/licence_keys.py
```

**If it says `vendor-private.pem exists. Refusing to overwrite`** — you have already done
this once. Do not force it unless you are certain you want to throw away the old key,
because every licence you have already issued would stop being valid.

---

## Step 4 — Put the public key into the software

Open the public key in Notepad:

```powershell
notepad C:\HHMS-keys\vendor-public.pem
```

It looks like this — three lines of dashes and a block of letters:

```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
...
-----END PUBLIC KEY-----
```

Select **all** of it (`Ctrl+A`, `Ctrl+C`).

Now open this file in your project:

```
backend\app\core\licence_keys.py
```

Find this part:

```python
RELEASE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
...the old key...
-----END PUBLIC KEY-----"""
```

Replace everything between the triple quotes with what you copied. It should end up
looking like:

```python
RELEASE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...your key...
-----END PUBLIC KEY-----"""
```

Save the file. **Keep the triple quotes and the dashes exactly as they are.**

---

## Step 5 — Tell the tests the key has changed

One test exists to remind you which key is live. It currently expects the development
key, so it will fail — that is the test doing its job.

Open `backend\tests\test_batch_b54_licensing.py`, find:

```python
assert IS_DEVELOPMENT_KEY is True, (
```

and change it to:

```python
assert IS_DEVELOPMENT_KEY is False, (
```

Save it.

---

## Step 6 — Check it worked

In `backend`:

```powershell
cd C:\path\to\your\HMS
python scripts\check_release_ready.py
```

You want:

```
ready: the build carries a release key
```

If it still says **NOT READY TO SHIP**, the public key was not pasted correctly. Open
`licence_keys.py` and check the triple quotes are intact and the dashes are on their own
lines.

---

## Step 7 — Back up the private key. Do this now.

`vendor-private.pem` is the only copy of your signing stamp.

**Make two copies:**

1. One on a USB stick, kept somewhere physical and locked
2. One in a password manager's file storage, or an encrypted archive

**Do not** put it in the project folder, in Dropbox's public area, in email, or in a chat.

### If you lose it

Nothing breaks immediately. Every licence you have already issued keeps working, because
the public key is inside those builds.

But you cannot issue **new** licences, and you cannot renew existing ones. The only fix is
a brand new key pair and a new release, which means every customer has to install the new
build. That is a bad week. Make the backup.

### If it leaks

Somebody can sign a licence that your software accepts. You need a new key pair, a new
release, and to tell your customers. The old key stops mattering the moment the new build
ships — but any licence forged before then still works on the old build.

---

## Step 8 — Issue your first licence

Back in `backend`:

```powershell
python -m app.cli.licence issue --private C:\HHMS-keys\vendor-private.pem --edition clinic --customer "Test Clinic" --months 12 --out C:\HHMS-keys\test-clinic.key
```

That writes a licence file. Check it:

```powershell
python -m app.cli.licence check C:\HHMS-keys\test-clinic.key
```

You want to see the edition, the customer and an expiry date, with no `REJECTED`.

**If it says REJECTED** — the public key in the build does not match the private key you
signed with. Go back to Step 4.

To see what you sold, without verifying:

```powershell
python -m app.cli.licence inspect C:\HHMS-keys\test-clinic.key
```

---

## Step 9 — What the hospital does with the file

Send them `test-clinic.key`. Tell them:

> Save this file as `data\licence.key` in the HHMS folder on the server, then restart
> the software.

That is the whole installation. No internet, no activation screen, no phone call.

---

## The three editions you can sell

| Edition | For | What it includes |
|---|---|---|
| `personal` | One doctor, free | Registration, OPD, dispensing, billing, printing |
| `clinic` | Multi-doctor clinic | The above, plus stock, laboratory and NABH |
| `hospital` | Inpatient | The above, plus IPD and medical records |
| `enterprise` | Colleges, teaching hospitals | Everything, plus QCI |

`--months 0` issues a licence with no expiry, which is what a perpetual sale looks like.
`--trial` makes it a trial, which defaults to one month and says so on the invoice.

---

## One page to keep

| | |
|---|---|
| Private key | `C:\HHMS-keys\vendor-private.pem` — offline, two backups, never in the project |
| Public key | `backend\app\core\licence_keys.py` — inside the software, safe to publish |
| Issue a licence | `python -m app.cli.licence issue --private ... --edition ... --customer ... --months 12 --out ...` |
| Check a licence | `python -m app.cli.licence check <file>` |
| Before you ship | `python scripts\check_release_ready.py` must say `ready` |
