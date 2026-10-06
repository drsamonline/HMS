"""Administrative user, role and permission APIs."""
from __future__ import annotations
from fastapi import APIRouter, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.admin import AdminRoleCreate, AdminRoleRead, AdminRoleUpdate, AdminUserCreate, AdminUserRead, AdminUserUpdate
from app.schemas.permission import PermissionRead
from app.services.administration import create_role, create_user, list_permissions, list_roles, list_users, update_role, update_user
router = APIRouter(prefix="/administration", tags=["Administration"])

def actor_id(current_user: CurrentUserDependency) -> int: return int(str(current_user["sub"]))

@router.get("/users", response_model=list[AdminUserRead])
async def get_users(db: DatabaseSession, current_user: CurrentUserDependency): return await list_users(db, actor_id(current_user))
@router.post("/users", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED)
async def add_user(data: AdminUserCreate, db: DatabaseSession, current_user: CurrentUserDependency):
    user = await create_user(db, actor_id(current_user), data)
    rows = await list_users(db, actor_id(current_user)); return next(x for x in rows if x["id"] == user.id)
@router.patch("/users/{user_id}", response_model=AdminUserRead)
async def edit_user(user_id: int, data: AdminUserUpdate, db: DatabaseSession, current_user: CurrentUserDependency): return await update_user(db, actor_id(current_user), user_id, data)
@router.get("/roles", response_model=list[AdminRoleRead])
async def get_roles(db: DatabaseSession, current_user: CurrentUserDependency): return await list_roles(db, actor_id(current_user))
@router.post("/roles", response_model=AdminRoleRead, status_code=status.HTTP_201_CREATED)
async def add_role(data: AdminRoleCreate, db: DatabaseSession, current_user: CurrentUserDependency):
    role = await create_role(db, actor_id(current_user), data); rows = await list_roles(db, actor_id(current_user)); return next(x for x in rows if x["id"] == role.id)
@router.patch("/roles/{role_id}", response_model=AdminRoleRead)
async def edit_role(role_id: int, data: AdminRoleUpdate, db: DatabaseSession, current_user: CurrentUserDependency): return await update_role(db, actor_id(current_user), role_id, data)
@router.get("/permissions", response_model=list[PermissionRead])
async def get_permissions(db: DatabaseSession, current_user: CurrentUserDependency): return await list_permissions(db, actor_id(current_user))
__all__=["router"]
