"""Authentication and current-user services."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.core.exceptions import AuthenticationException, DatabaseException
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.permission import Permission
from app.services.user import UserService
class AuthService:
    def __init__(self,user_service:UserService|None=None): self.user_service=user_service or UserService()
    async def authenticate(self,db:AsyncSession,*,username:str,password:str)->User:
        if not username.strip() or not password: raise AuthenticationException("Incorrect username or password.")
        try: user=await self.user_service.get_by_username(db,username=username.strip())
        except SQLAlchemyError as exc: raise DatabaseException("Unable to authenticate user.") from exc
        if user is None or not verify_password(password,user.hashed_password): raise AuthenticationException("Incorrect username or password.")
        return user
    async def login(self,db:AsyncSession,*,username:str,password:str)->str:
        user=await self.authenticate(db,username=username,password=password)
        return create_access_token(subject=str(user.id))
    async def get_current_user_profile(self,db:AsyncSession,*,user_id:int) -> tuple[User,list[str],list[str]]:
        user=await db.get(User,user_id)
        if user is None or not user.is_active: raise AuthenticationException("Authenticated user is not available.")
        role_rows=await db.execute(select(Role.role_name, Permission.code).join(UserRole,UserRole.role_id==Role.id).outerjoin(RolePermission,RolePermission.role_id==Role.id).outerjoin(Permission,Permission.id==RolePermission.permission_id).where(UserRole.user_id==user_id,Role.is_active.is_(True)))
        roles=set(); permissions=set()
        for role_name,code in role_rows.all():
            roles.add(role_name)
            if code: permissions.add(code)
        return user,sorted(roles),sorted(permissions)
auth_service=AuthService()
__all__=["AuthService","auth_service"]
