# Licensing

How a copy of HHMS learns what it is allowed to run, and why it works this way.

## The problem

The edition has to be decided somewhere, and every option has a cost.

| Mechanism | Works offline | Enforceable | Fails when |
|---|---|---|---|
| Environment variable | yes | **no** | anybody edits a text file |
| Online activation | **no** | yes | the hospital LAN has no internet - which is most of them |
| Signed licence file | yes | yes | the private key leaks |
| Dongle | yes | yes | it is lost, and hospitals lose things |

HHMS uses a **signed licence file**. A hospital LAN frequently has no internet or a
firewall that would make an activation server unreachable, so a licence that needs a
phone-home fails in exactly the buildings that buy the software.

## How it works

The vendor holds a private key. A licence is a short signed statement:

```
{
  "edition":  "hospital",
  "customer": "Sunrise Homoeopathy",
  "iat":      1762732800,
  "exp":      1794268800,
  "ref":      "hospital-20261111093000"
}
```

The software ships the matching **public key** in `backend/app/core/licence_keys.py`
and verifies the signature without contacting anybody. Nobody can add an edition to the
file without invalidating the signature, so editing the file is not a route to a free
upgrade.

The licence lives at `data/licence.key` on the server.

## Issuing one

Once, on a machine that is not this repository:

```
python -m app.cli.licence keygen --private vendor-private.pem --public vendor-public.pem
```

Paste `vendor-public.pem` into `backend/app/core/licence_keys.py` and rebuild. **Keep
the private key offline.** If it leaks, every licence you have ever issued can be
forged, and the only remedy is a new key and a new release.

Then, per customer:

```
python -m app.cli.licence issue \
    --private vendor-private.pem \
    --edition hospital \
    --customer "Sunrise Homoeopathy" \
    --months 12 \
    --out sunrise-hospital.key
```

Send them the file. They put it at `data/licence.key` and restart.

Two more commands, for support:

```
python -m app.cli.licence inspect sunrise-hospital.key   # what did we sell them
python -m app.cli.licence check   sunrise-hospital.key   # is it genuine
```

## What happens when

| State | Edition | What the user sees |
|---|---|---|
| Valid licence | As licensed | Nothing |
| No licence | Free | Nothing - this is the normal free install |
| Expired, within 30 days | As licensed | A warning, and it keeps working |
| Expired, past 30 days | Free | A warning naming the expiry date |
| Forged or altered | Free | A warning, and an error in the log |
| `HHMS_EDITION` set, no licence | As set | A warning that this is an evaluation path |

**The grace period is deliberate.** Bricking a hospital's records on an anniversary is
not a business model, it is a hazard - a doctor who cannot open a patient's record
because a renewal was missed is a worse outcome than a licence that ran a month long.
Thirty days is enough to chase a renewal and short enough that it is not the same as no
expiry at all.

## What this does not do

**It is not copy protection.** Somebody determined enough can patch the check out of a
binary, and no scheme in this file changes that. What it does is make the honest case
honest and the dishonest case deliberate: a clinic running the hospital edition without
a licence is not confused about what it bought.

**It does not phone home.** There is no telemetry, no seat counting and no kill switch.
A hospital that never contacts the vendor again keeps working for as long as its
licence says.

**It does not bind to hardware.** A licence is not tied to a machine, so a hospital can
replace a failed server without waiting for a new file. The cost is that one licence
could run on two servers; the benefit is that a Friday-night failure is fixed on Friday
night.

## The free edition

Free is a real edition, not a trial:

- registration, OPD, dispensing, billing, and printing the whole case and its bills
- **no NABH** - accreditation reporting is a paid feature
- no inpatient, no laboratory, no medical records

It runs forever with no licence file and no expiry. The only thing that distinguishes it
from a paid copy is what it can do.
