# Client OPD → Clinical Handoff

## Purpose

After an OPD visit and token are successfully created, the client immediately opens the selected patient's Clinical Workspace.

## Flow

Patient selection → visit creation → server-generated OPD token → patient Clinical Workspace.

The server remains authoritative for visit and token creation. The handoff uses the existing patient workspace and does not create duplicate clinical records.
