# HHMS Clinical Core

## Scope

The Clinical Core provides a compact, longitudinal homoeopathic record without
creating a separate database entity for every case-taking heading.

## Case Record

`CaseRecord` contains narrative clinical sections including chief complaints,
history of present illness, past history, family history, personal history,
mental and physical generals, particulars, sex-specific/reproductive history,
surgical history, examination, totality, characteristic symptoms, miasmatic
assessment, analytical notes, remedy differential, and prescribing rationale.

Quick-generals and modalities are compact structured data. Every modality can
record an effect (`agg` or `amel`) and its own additional free-text detail.

Optional sections remain nullable. A partially completed case can be saved,
retrieved, edited, and completed later.

## Diagnosis

`Diagnosis` is separate from homoeopathic assessment. It stores the clinical
diagnosis and optional ICD-11 code, title, URI, and release metadata. ICD-11 is
not required to save a case.

## Follow-up

`FollowUp` stores longitudinal changes, remedy response, clinical assessment,
decision, and optional links to previous and next prescriptions. Historical case
content is not overwritten by a follow-up.

## ICD-11 Integration

HHMS performs ICD-11 lookup only when requested by the user. The frontend calls
the HHMS `/api/v1/icd11/search` endpoint; the backend service then calls the WHO
ICD-11 API using credentials supplied through environment configuration.

The WHO ICD-11 API uses OAuth2 client credentials. The WHO token endpoint and API
base URL are configurable. No ICD-11 catalogue is bundled into HHMS for the
initial implementation. If credentials are not configured, ordinary clinical
record creation remains usable; only online ICD-11 lookup is unavailable.

## Clinical Validation Rule

Optional clinical sections are never made mandatory merely because they appear
on a printed case sheet. Only genuinely required identity, ownership, and
resource-link fields are validated.
