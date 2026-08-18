# Unified Patient History

The patient history combines current live activity with explicitly selected historical operational years.

Archived events are read-only and are loaded only for the selected year. Archive event queries are bounded by the configured operational year (calendar or financial) so a full-database archive snapshot cannot leak records from another operational year into the selected historical view.

Supported historical event types include OPD visits, IPD admissions, investigations, billing invoices, MRD files, prescriptions, diagnoses, follow-ups, and case records when the corresponding archived table exists.
