"""CRUD operations for user-role assignments."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_role import UserRole
class UserRoleCRUD:
    async def get_by_user(self,db:AsyncSession,*,user_id:int)->list[UserRole]:
        return list((await db.execute(select(UserRole).where(UserRole.user_id==user_id).order_by(UserRole.role_id))).scalars().all())
    async def exists(self,db:AsyncSession,*,user_id:int,role_id:int)->bool:
        return (await db.execute(select(UserRole).where(UserRole.user_id==user_id,UserRole.role_id==role_id))).scalar_one_or_none() is not None
user_role_crud=UserRoleCRUD()
__all__=["UserRoleCRUD","user_role_crud"]
