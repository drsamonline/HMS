# HHMS User Guide

End-user manual for the Homeopathic Hospital Management System (HHMS) — a LAN-based
hospital management system where one Windows machine runs **HHMS-Server** (the only
component that touches the SQLite database) and every workstation runs
**HHMS-Client** (a WebView2 window serving the same HTML/CSS/JS interface).

Audience: receptionists, clinicians, IPD nurses, pharmacy staff, lab coordinators,
billing clerks, inventory/procurement officers, MRD/archive staff, and administrators.
Nothing in this guide requires programming knowledge.

Related documents: [ADMIN_TRAINING.md](ADMIN_TRAINING.md) (setup & operations),
[DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md) (codebase),
[CLIENT_AUTH_PATIENT_WORKSPACE.md](CLIENT_AUTH_PATIENT_WORKSPACE.md),
[UI_GUIDELINES.md](UI_GUIDELINES.md), [API_SPECIFICATION.md](API_SPECIFICATION.md).

---

## 1. Starting HHMS

### 1.1 Launching the client
1. Double-click **HHMS-Client.exe** (Start Menu shortcut created by the installer).
2. The login screen appears. If the server is running on the LAN, the client
   discovers it automatically via UDP broadcast (`HHMS_DISCOVER_V1`) — you normally
   never type an address.
3. If discovery does not find the server, use **Connect manually** and enter the
   server machine's LAN address, e.g. `http://192.168.1.10:8000`.

> First launch on a fresh Windows PC may prompt to install the Microsoft Edge
> WebView2 Runtime. Follow the prompt, or ask your administrator to deploy the
> offline redistributable (see ADMIN_TRAINING.md §2).

### 1.2 Signing in
Enter your **username** and **password** given by your administrator. A wrong
password shows an inline error. After repeated failed attempts (default: 10 per
minute per workstation) sign-in is briefly blocked with a "too many attempts"
message — this is the brute-force protection; wait about a minute and try again.

### 1.3 Signing out / locking
Use **Sign out** in the header. Sessions are per-workstation; always sign out at a
shared desk so the next user sees their own navigation.

## 2. Navigation and roles

The left sidebar shows only the modules your role can access. Visibility is driven
by the live server profile (`GET /auth/me`), re-checked every time you sign in —
never by a stale local guess. Denied modules are hidden, disabled, and marked
unreachable for assistive technology simultaneously.

| Module | Typical users | What you do there |
|--------|---------------|-------------------|
| Patients | Reception | Register patients, search the master list, update demographics |
| OPD | Reception, Clinicians | Walk-in tokens, queue board, consultation entries |
| Clinical | Doctors | Case records: history, repertorisation, prescriptions, follow-ups |
| IPD | Ward staff | Admissions, beds, notes, transfers, discharge summaries |
| Investigations | Doctors, Lab | Order labs/X-rays, record results, track billing of orders |
| Pharmacy | Dispensers | Medicine stock, dispensing against prescriptions |
| Billing | Billing clerks | Invoices, payments, refunds, settlement review |
| MRD | Records staff | Medical record files, document archiving |
| Inventory | Stores | Stock balance, indents, issues |
| Procurement | Stores/Purchase | Purchase orders and receiving |
| Reports | All permitted | Printable envelopes: invoices, receipts, summaries |
| Statistics | Admins/Managers | Department/service breakdowns, trends |
| Activity | Admins | Audit trail of who did what |
| Administration | Admins | Departments, designations, users, roles, settings |

Doctors see Clinical/OPD/IPD tools; reception sees Patients/OPD/Billing entry
points; administrators additionally see Administration and Activity. If a module
you expect is missing, your role needs updating — contact your administrator
(do not attempt self-service changes).

Within record screens, tabs behave the same way: inaccessible tabs are removed
from the keyboard focus order and the first allowed tab receives focus.

## 3. Core daily workflows

### 3.1 Patient registration (Reception)
1. **Patients → New patient.** Fill name, age/DOB, sex, contact, and address.
2. Save — the system mints the UHID/patient number automatically (sequence
   numbers are generated atomically by the server; never edit them by hand).
3. Search existing patients **before** creating a new record to avoid duplicates;
   use partial name or phone search.

### 3.2 OPD visit (Reception → Doctor)
1. **OPD → New token** for the registered patient, choosing department/doctor.
2. The token enters the department queue board visible to all clients.
3. The clinician opens the patient from the queue, records the consultation under
   **Clinical**, and prescribes medicines and/or investigations.
4. Progress the queue state as patients are seen; discharged/completed tokens
   leave the active board but remain in history.

### 3.3 Case record & prescription (Doctor)
1. From **Clinical**, open or create the case record for the visit.
2. Enter remedy, potency, dosage instructions, and follow-up date.
3. Prescriptions print through the standard print envelope (Reports/print dialog)
   using the clinic's prescription template.

### 3.4 IPD admission & discharge (Ward staff)
1. **IPD → Admit**: select patient, ward/bed, admitting doctor.
2. Daily progress notes under the admission; order investigations from the same
   context.
3. **Discharge**: complete the discharge summary; the bed is released back to the
   ward occupancy counts and the encounter closes for billing.

### 3.5 Billing (Billing clerk)
1. Charges (consultation, pharmacy, investigations, IPD days) accumulate onto the
   patient invoice.
2. **Billing → Invoice**: add/verify line items, apply any approved discounts,
   then settle with payments (cash/other modes). Partial payments are supported;
   the outstanding balance is always shown.
3. Refunds are entered as negative payments and appear on the refund audit feed
   for review. Print receipts/invoice copies from the print envelope.

### 3.6 Pharmacy & investigations
- **Pharmacy**: dispense against a prescription line; stock decrements on issue.
- **Investigations**: ordered tests appear in the lab worklist; entering a result
  marks the order complete and keeps its billed amount reconciled on the
  investigation-billing dashboard.

### 3.7 Reports & printing
Every dashboard/report offers a **print envelope**: the paper output matches the
screen figures by construction. Choose Reports → the desired statement → preview →
send to the clinic printer. Statistics and administrative reports cover
department breakdowns, outstanding invoices, pending investigations, ward
occupancy, settlement/refund audits, and activity summaries.

## 4. Data-entry conventions (all users)

- Required fields are marked; empty mandatory fields block saving with an inline
  message — fix the highlighted field rather than resubmitting blindly.
- Dates use the format configured for the clinic; free text is trimmed and
  normalized server-side (double spaces/case quirks won't break searches).
- One patient = one record. Merge/duplicate corrections are administrator tasks.
- Never share your password; the audit trail attributes every change to your user.

## 5. Troubleshooting (client side)

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| "Server not found" on start | Server machine off/asleep, or different network | Start HHMS-Server on the host PC; verify both machines are on the same LAN/subnet; try manual connect with the server IP |
| Login says too many attempts | Rate limiter after repeated failures | Wait ~60 seconds; if you forgot the password, ask the admin to reset it |
| A sidebar module vanished | Your role changed or profile didn't load | Sign out and back in; if still missing, ask admin to confirm your role assignments |
| Printing produces blank/wrong layout | Printer driver or template mismatch | Check the OS default printer; use the preview first; report template issues to your administrator |
| Screen frozen/stale data | Network hiccup with the server | Refresh (Ctrl+R); if persistent, confirm the server app is running |
| Client window is white on first run | WebView2 runtime missing | Install the Edge WebView2 Runtime (admin-deployed offline installer works without internet) |

Escalate anything unresolved to your internal HHMS administrator, noting the
workstation name, time, and what you were doing — the Activity log will show the
server-side record.

## 6. Do-not list

- Don't copy, move, or edit files inside the server's `data/` folder while the
  server is running.
- Don't run two HHMS-Server instances against the same database folder.
- Don't close the server console during writes (use its exit procedure).
- Don't back up by zipping the `.sqlite3` file alone — use the Backup workspace
  (see ADMIN_TRAINING.md §6).
