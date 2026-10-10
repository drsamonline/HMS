# RBAC Consistency Batch

The pre-existing RBAC layer mixed two incompatible designs: the actual project schema uses integer `User.id` and `Role.id`, while UserRole/RolePermission were UUID-based and referenced lower-case PostgreSQL table names that do not exist in the HHMS initial schema.

This batch aligns the RBAC models, schemas, CRUD layer and authentication profile endpoint with the established integer `User`/`Role` schema.

`GET /api/v1/auth/me` now returns the authenticated user together with role names and permission codes. The client can use this for role-aware navigation without duplicating authorization logic.
