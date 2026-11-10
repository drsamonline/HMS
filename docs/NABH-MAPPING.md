# NABH mapping — what HHMS can actually evidence

This is a checklist, not a claim of certification. Each row names a NABH Objective
Element, what the standard asks for, what HHMS does today, and the file or endpoint
that proves it. A row is `evidenced` only when the code does the thing; a feature
that is planned is `absent`, not `partial`.

The states are deliberately harsh. A hospital preparing for assessment is better
served by an honest gap list than by a document that reads well.

Scope: the NABH hospital standards and the NABH Digital Health Standards for
HIS/EMR are both in view, but this mapping follows what the software implements
rather than what a certificate requires. The 32 organisational KPIs in PSQ.3 are
the subject of their own wave and appear here as `absent`.

Extended rather than added: `docs/MASTER_SPECIFICATION.md` states NABH AYUSH as a
requirement in three places but maps nothing. This file is the mapping that
statement lacked; the specification is unchanged.

---

## 1. Access, identity and accountability

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| AAC.1 | Documented scope of services, accessible to staff | Modules are declared with dependencies and can be enabled per hospital; the navigation manifest shows only what is enabled | `backend/app/modules/registry.py`, `backend/app/modules/navigation.py` | evidenced |
| AAC.4 | Access to the record is controlled by role | 40 permission codes, 10 role templates, `require()` on every route, default deny | `backend/app/core/permissions.py`, `backend/app/dependencies/permissions.py` | evidenced |
| AAC.4 | A user sees only what their role allows | The server filters the menu and the home screen; a client never receives a screen name it cannot open | `GET /api/v1/navigation`, `GET /api/v1/home` | evidenced |
| IMS.1 | Unique identification of each patient | Patient number minted from a configured sequence, never reused | `backend/app/models/patient.py`, `backend/app/services/number_sequence.py` | evidenced |
| IMS.2 | Each entry in the record is attributable | Audit trail records actor, action, entity, before and after, request id and IP | `backend/app/services/audit.py`, `backend/app/models/audit_log.py` | evidenced |
| IMS.2 | The trail cannot be quietly altered | Append-only triggers plus a SHA-256 hash chain, verified nightly | `backend/app/services/audit_chain.py`, migration `0031` | evidenced |

## 2. Care of patients — records

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| COP.1 | A documented initial assessment for every patient | Case record with presenting complaint, history, examination, analysis and plan | `backend/app/models/case_record.py`, `backend/app/api/v1/endpoints/case_records.py` | evidenced |
| COP.2 | Care is planned and reviewed | Follow-up records with general, mental and particular state, remedy response and decision | `backend/app/models/followup.py`, `backend/app/services/followup.py` | evidenced |
| COP.2 | A change of treatment is justified | A decision to change the remedy or stop and reassess is refused without a stated reason (NCH Code of Ethics 31(1)) | `backend/app/services/followup.py` | evidenced |
| COP.8 | Referral carries a written case statement | A referral certificate is refused without one (NCH Code of Ethics 27) | `backend/app/services/certificates.py` | evidenced |
| COP.11 | Every certificate is retained | Retention date computed at issue and stored; register lists what is held and what is past retention (NCH 7(1)) | `backend/app/models/medical_certificate.py`, `GET /api/v1/compliance/certificate-retention` | evidenced |
| MOM.4 | Prescriptions are legible, complete and attributable | Prescriber name and NCH registration number travel with every prescription and render in its header; a missing number is shown as missing | `backend/app/schemas/prescription.py`, `frontend/js/ui/prescription.js` | evidenced |

## 3. Medication and laboratory

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| MOM.5 | A medication order is traceable to the prescriber | Prescription records the prescriber and the encounter | `backend/app/models/prescription.py` | evidenced |
| MOM.7 | Adverse drug events are reported | A pharmacovigilance register records the event and the report separately, with both timestamps (NCH 37) | `backend/app/models/adverse_event.py`, `backend/app/services/adverse_events.py` | evidenced |
| MOM.7 | Unreported events are visible | The readiness report counts events recorded and not yet reported | `GET /api/v1/compliance/nch-readiness` | evidenced |
| COP.6 | Laboratory results are verified before release | Results carry `verified_by` and a report status | `backend/app/models/investigation_result.py` | evidenced |
| COP.6 | A specimen is traceable to its result | An investigation carries the laboratory's accession, unique when set | `backend/app/models/investigation.py` | partial — the identifier is stored and refused when duplicated; collection time, collector and sample type are not recorded |

## 4. Records, audit and continuity

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| IMS.4 | Records are retained for the required period | Live, online-archive and cold-archive tiers with documented retention | `docs/ARCHIVE_RETENTION_TIERS.md`, `backend/app/services/archive_manager.py` | evidenced |
| IMS.4 | Records are not lost | Verified backups, with restore exercised | `backend/app/api/v1/endpoints/maintenance.py`, `docs/CLIENT_BACKUP_WORKSPACE.md` | evidenced |
| IMS.5 | Numbering is continuous and cannot be edited away | Sequences with prefix, padding and reset policy; a register of what was issued | `backend/app/models/number_sequence.py`, `docs/CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md` | evidenced |
| IMS.6 | The system can show what changed, when, and by whom | Audit review and export endpoints | `GET /api/v1/audit-logs`, `backend/app/api/v1/endpoints/audit_logs.py` | evidenced |
| PSQ.1 | Incidents are recorded and reviewed | Not implemented | — | absent |
| PSQ.3 | The hospital measures itself against the mandatory indicators | Nine indicators across three complete families, with an honest coverage report naming the eight families that cannot be served and what each needs | `backend/app/core/indicators.py`, `backend/app/core/psq3.py`, `docs/NABH-PSQ3.md`, `GET /api/v1/indicators/psq3` | partial |

## 5. Information management — the digital health standards

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| DH.2 | Role-based access with least privilege | As AAC.4 above | `backend/app/dependencies/permissions.py` | evidenced |
| DH.3 | Audit trail of access and change | As IMS.2 above | `backend/app/services/audit_chain.py` | evidenced |
| DH.5 | Data is backed up and recoverable | As IMS.4 above | `backend/app/api/v1/endpoints/maintenance.py` | evidenced |
| DH.7 | Interoperability | No FHIR or HL7 interface | — | absent |
| DH.8 | Electronic signatures | Not implemented; the audit trail is the attribution, not a signature | — | absent |

## 6. Configuration and change control

| Element | What NABH asks | What HHMS does | Evidence | State |
|---|---|---|---|---|
| IMS.3 | The system is configured to the hospital, not the reverse | 44-setting catalogue, wizard, configuration API with validation, export and import | `backend/app/core/settings_catalogue.py`, `backend/app/api/v1/endpoints/configuration.py` | evidenced |
| IMS.3 | A change to configuration is recorded | Every setting write is audited with before and after | `backend/app/services/settings_store.py` | evidenced |
| IMS.3 | A change that needs a restart is visible | Restart status names settings stored but not yet running | `GET /api/v1/configuration/restart-status` | evidenced |

---

## Roadmap — the `absent` rows

These are not owned, dated or costed here. They are the gap between the mapping
above and a complete assessment.

1. **PSQ.1 incident reporting** — a register of incidents and near-misses, separate
   from adverse drug events, with review and closure.
2. **PSQ.3 organisational KPIs** — the 32 mandatory indicators plus the 18
   department-specific ones. The spine exists (`backend/app/core/indicators.py`):
   nine indicators are declared and computed. Coverage is assessed by family in
   `docs/NABH-PSQ3.md` and served at `GET /api/v1/indicators/psq3`: three families
   are fully reportable, two partly, six not at all. The enumeration itself is
   blocked on the NABH standard document, which is not in this repository — see
   PSQ.3 below.
3. **DH.7 interoperability** — FHIR or HL7 exchange. Deliberately out of scope for a
   LAN SQLite product; the data model is frozen and a rewrite is not warranted.
4. **DH.8 electronic signatures** — a signed assertion of who approved what,
   distinct from the audit trail.
5. **Consent capture** — no table records consent to treatment or to disclosure.
6. **Medication reconciliation** — no admission-to-discharge reconciliation.
7. **Staff credentialing register** — registration numbers are stored per
   practitioner but there is no register of qualifications, expiry or privileges.
8. **Sample collection detail** — accession is recorded; collector, collection time
   and sample type are not.
9. **Discharge summary template** — discharge exists; a NABH-shaped summary
   template does not.
10. **Patient identification at the point of care** — no wristband or barcode
    verification.

## How to keep this honest

A row may only move from `absent` to `partial` or `evidenced` in the same change
that adds the code, and the evidence column must name a file or endpoint that
exists. A test asserts that every path named here resolves; a mapping that cites
something deleted is worse than no mapping.
