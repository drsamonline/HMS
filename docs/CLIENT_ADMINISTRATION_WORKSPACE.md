# Client Administration Workspace — Batch 36

Provides an administrator-facing workspace for users, roles, permissions, and the existing department/service masters.

Server authorization remains authoritative. The client only presents administration controls to authorized users.

Administrative user creation and updates use the existing `User.password_hash` field and assign integer `UserRole` / `RolePermission` relationships.
