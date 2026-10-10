# Client Clinical Case Workspace — Batch 09

## Scope
This batch connects the authenticated patient workspace to the existing `CaseRecord` API and implements the first real homoeopathic clinical data-entry screen.

## Design
The screen stays compact:
- narrative sections are free-text;
- quick generals are small structured selectors;
- modalities use a compact Agg./Amel. selector plus an additional-information field for each modality;
- optional sections remain optional;
- empty sections are omitted from the payload rather than causing save errors.

## Current case sections
Chief complaints, history of present illness, past history, family history, personal history, mental generals, physical generals, particulars/LSMC, female/gynaecological history, male history, sexual/reproductive history, obstetric history, surgical history, clinical examination, characteristic symptoms, totality, miasmatic assessment, analytical notes, remedy differential, and prescribing rationale.

## Explicit boundary
Diagnosis/ICD-11, prescription, and longitudinal follow-up remain separate backend records and will be connected in subsequent client batches. This batch does not duplicate those data models.

## Save behavior
A case may be created as Draft, Active, or Closed. Empty text blocks and unselected structured fields are omitted/null and do not block saving.
