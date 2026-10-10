# HHMS Medical Records Department (MRD)

## Scope

MRD manages the administrative/index layer for patient files and archival records. It does not replace the clinical `CaseRecord` or generic `MedicalDocument`.

## PatientFile

Stores the patient file number, file type, physical location, shelf/rack information and status.

## ArchiveRecord

Stores archive information linked to a PatientFile, including archive date/location, box number, retention period and status.

## Progressive completion

Optional physical/archive fields may remain empty and can be completed later. The API must not reject an otherwise valid record merely because optional MRD information is not yet available.

## API

- `GET /api/v1/patient-files?patient_id=...`
- `POST /api/v1/patient-files`
- `GET /api/v1/patient-files/{id}`
- `PATCH /api/v1/patient-files/{id}`
- `GET /api/v1/archive-records?patient_file_id=...`
- `POST /api/v1/archive-records`
- `GET /api/v1/archive-records/{id}`
- `PATCH /api/v1/archive-records/{id}`
