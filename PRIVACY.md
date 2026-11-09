# Privacy

Version: 1.0 (draft for review)
Effective: on publication
Owner: Dr Sohil Momin, Vadodara, Gujarat — sohilmomin2000@gmail.com
Changes: Initial version.

HHMS is hospital software that runs on your own network. This document describes what the software stores, where it stores it, and what leaves the installation. It is written about the code in this repository and is updated in the same commit as any change to how that code handles data.

## Who is responsible for patient data

The hospital or clinic that installs HHMS is the **Data Fiduciary** under the Digital Personal Data Protection Act, 2023. It decides what is collected and why, and it answers to its patients.

The Licensor — Dr Sohil Momin — is the **software provider**. HHMS is installed on a server inside the hospital, and the Licensor does not receive, host, copy or have any access to the data in it. There is no vendor-side account, no licence server and no remote support channel that carries patient data.

This distinction matters: a request about a patient's record goes to the hospital that holds it, not to the software's author.

## What the software stores

HHMS holds the records a hospital needs to run. All of it is entered by hospital staff, on hospital equipment.

| Category | Examples |
| --- | --- |
| Patient identity | Name, patient number, gender, date of birth or age, blood group, mobile number, address |
| Clinical records | Homoeopathic case records, follow-ups, progress notes, diagnosis including ICD-11 coding, prescriptions and items |
| Investigations | Investigation orders and results, laboratory and imaging records |
| Admission | IPD admission, ward and bed, discharge summary, diet and nutritional assessment, pain assessment |
| Documents | Files attached to a patient, such as scanned reports |
| Billing | Invoices, invoice items, payments, outstanding balances |
| Pharmacy and stores | Medicine master, batches, stock ledger, dispense records, procurement and goods receipt |
| Access control | User accounts, roles and permissions |
| Audit trail | A permanent log of significant system activity, including which user performed it |

Health data is sensitive personal data under the Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011, and personal data under the DPDP Act, 2023. It is treated as such.

## Where it is stored

Everything sits in one writable data directory on the server:

| Path | Contents |
| --- | --- |
| `data/hhms.sqlite3` | The database |
| `data/uploads/` | Patient documents and other uploaded files |
| `data/backups/` | Backups created by the backup workspace |
| `data/logs/` | Server logs |
| `.env` | Server configuration, including the signing secret |

Only the server process opens the database. Client machines speak HTTP/JSON to it over the hospital LAN and never touch the file directly. The location can be moved with the `HHMS_APPLICATION_ROOT` environment variable, which is useful when the data directory is kept on an encrypted volume or a network share with restricted permissions.

## What leaves the installation

**Nothing.** HHMS makes no outbound internet connection. There is no telemetry, no analytics, no crash reporting, no advertising identifier, no licence check and no update ping. The application contains no code that reaches a host outside your network, which you can confirm by searching the source for external URLs and by watching the server's outbound traffic.

Two things sit outside that statement and are worth stating plainly:

- **Links you click.** Documentation and the ICD-11 lookup point to websites. Opening one takes you to that site, with its own privacy policy. The software loads nothing from it.
- **Anything you add.** If a future version adds a cloud feature, this document and the test that forbids an outbound call change in the same commit.

## Accounts and access

Access is by named user account with a password, and every request is authorised against a role and its permissions. Sign-in is rate limited. Sessions are token-based and expire. Administrative actions are recorded in the audit trail with the user who performed them.

The hospital decides who holds which role. HHMS does not ship with a shared login, and a shared login defeats both the audit trail and this document.

## Retention

HHMS does not delete clinical or billing records on its own. Records move through archive tiers as years close, and older data is retained rather than removed. The schedule, the rollover mechanics and the erasure position are set out in [RETENTION-AND-ERASURE.md](docs/legal/RETENTION-AND-ERASURE.md).

## Backups

Backups are written to `data/backups/` on the server, and to wherever an administrator copies them. A backup is a complete copy of patient data: it must be protected like the database itself — restricted to staff who need it, on encrypted media if it leaves the premises, and deleted when its retention period ends. A backup restored to a laptop is a second, unmanaged copy of the hospital's patient data.

## Children and dependants

HHMS records patients of any age, including children, and a child's record is often entered by a parent. Under s.9 of the DPDP Act, 2023, processing a child's personal data requires verifiable parental consent, with limited exceptions. A hospital treating a child has separate grounds to consider. This is an open question for counsel — see `docs/legal/LEGAL-INDEX.md` — and not something this document settles.

## Your rights

A patient's rights under the DPDP Act — access, correction, erasure, grievance, nomination — are exercised against the hospital that holds the record. The hospital publishes its own contact for that. HHMS provides the records and the audit trail that let the hospital answer such a request.

## Changes

This document is versioned in the repository. A change to how the software handles data is a change to this document in the same commit.

Contact: Dr Sohil Momin — sohilmomin2000@gmail.com
