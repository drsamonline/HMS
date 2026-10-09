"""Administrator workflows for users, roles and permissions."""
from __future__ import annotations
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.password import hash_password
from app.core.exceptions import (
    AuthorizationException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.admin import AdminRoleCreate, AdminRoleUpdate, AdminUserCreate, AdminUserUpdate

_ADMIN_ROLE_NAMES = {"admin", "administrator", "superadmin", "super administrator"}

async def _require_admin(db: AsyncSession, user_id: int) -> None:
    rows = await db.execute(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active.is_(True))
    )
    if not any(str(name).strip().lower() in _ADMIN_ROLE_NAMES for name in rows.scalars().all()):
        raise AuthorizationException("Administrator access is required.")

async def list_users(db: AsyncSession, actor_id: int) -> list[dict]:
    await _require_admin(db, actor_id)
    users = list((await db.execute(select(User).order_by(User.username))).scalars().all())
    assignments = (await db.execute(select(UserRole, Role).join(Role, Role.id == UserRole.role_id))).all()
    by_user: dict[int, list[tuple[int, str]]] = {}
    for ur, role in assignments:
        by_user.setdefault(ur.user_id, []).append((role.id, role.role_name))
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email,
             "mobile_number": u.mobile_number, "designation": u.designation, "is_active": u.is_active,
             "role_ids": [x[0] for x in by_user.get(u.id, [])], "role_names": [x[1] for x in by_user.get(u.id, [])]} for u in users]

async def create_user(db: AsyncSession, actor_id: int, data: AdminUserCreate) -> User:
    await _require_admin(db, actor_id)
    existing = await db.scalar(select(User).where(User.username == data.username.strip()))
    if existing:
        raise DuplicateResourceException("Username already exists.")
    user = User(username=data.username.strip(), password_hash=hash_password(data.password), full_name=data.full_name.strip(),
                email=data.email.strip().lower() if data.email else None, mobile_number=data.mobile_number,
                designation=data.designation, is_active=data.is_active)
    db.add(user)
    await db.flush()
    if data.role_ids:
        roles = list((await db.execute(select(Role).where(Role.id.in_(data.role_ids)))).scalars().all())
        for role in roles:
            db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=actor_id))
    await db.commit(); await db.refresh(user); return user

async def update_user(db: AsyncSession, actor_id: int, user_id: int, data: AdminUserUpdate) -> dict:
    await _require_admin(db, actor_id)
    user = await db.get(User, user_id)
    if user is None: raise ResourceNotFoundException("User not found.")
    values = data.model_dump(exclude_unset=True)
    roles = values.pop("role_ids", None)
    password = values.pop("password", None)
    for key, value in values.items(): setattr(user, key, value)
    if password: user.password_hash = hash_password(password)
    if roles is not None:
        await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
        for role_id in roles: db.add(UserRole(user_id=user.id, role_id=role_id, assigned_by=actor_id))
    await db.commit()
    return (await list_users(db, actor_id))[next(i for i,x in enumerate(await list_users(db, actor_id)) if x["id"] == user.id)]

async def list_roles(db: AsyncSession, actor_id: int) -> list[dict]:
    await _require_admin(db, actor_id)
    roles = list((await db.execute(select(Role).order_by(Role.role_name))).scalars().all())
    assignments = (await db.execute(select(RolePermission, Permission).join(Permission, Permission.id == RolePermission.permission_id))).all()
    by_role: dict[int, list[tuple[int, str]]] = {}
    for rp, p in assignments: by_role.setdefault(rp.role_id, []).append((p.id, p.code))
    return [{"id": r.id, "role_name": r.role_name, "description": r.description, "is_active": r.is_active,
             "permission_ids": [x[0] for x in by_role.get(r.id, [])], "permission_codes": [x[1] for x in by_role.get(r.id, [])]} for r in roles]

async def create_role(db: AsyncSession, actor_id: int, data: AdminRoleCreate) -> Role:
    await _require_admin(db, actor_id)
    existing = await db.scalar(select(Role).where(Role.role_name == data.role_name.strip()))
    if existing: raise DuplicateResourceException("Role already exists.")
    role = Role(role_name=data.role_name.strip(), description=data.description, is_active=data.is_active)
    db.add(role); await db.flush()
    for permission_id in data.permission_ids: db.add(RolePermission(role_id=role.id, permission_id=permission_id, assigned_by=actor_id))
    await db.commit(); await db.refresh(role); return role

async def update_role(db: AsyncSession, actor_id: int, role_id: int, data: AdminRoleUpdate) -> dict:
    await _require_admin(db, actor_id)
    role = await db.get(Role, role_id)
    if role is None: raise ResourceNotFoundException("Role not found.")
    values = data.model_dump(exclude_unset=True); permission_ids = values.pop("permission_ids", None)
    for key,value in values.items(): setattr(role,key,value)
    if permission_ids is not None:
        await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
        for pid in permission_ids: db.add(RolePermission(role_id=role.id, permission_id=pid, assigned_by=actor_id))
    await db.commit()
    return next(x for x in await list_roles(db, actor_id) if x["id"] == role.id)

async def list_permissions(db: AsyncSession, actor_id: int) -> list[Permission]:
    await _require_admin(db, actor_id)
    return list((await db.execute(select(Permission).where(Permission.is_active.is_(True)).order_by(Permission.module, Permission.code))).scalars().all())

__all__ = ["list_users","create_user","update_user","list_roles","create_role","update_role","list_permissions"]
