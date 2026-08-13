"""CRUD operations for roles."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate
class RoleCRUD(CRUDBase[Role,RoleCreate,RoleUpdate]):
    def __init__(self)->None: super().__init__(Role)
    async def get_by_name(self,db:AsyncSession,*,role_name:str)->Role|None:
        return (await db.execute(select(Role).where(Role.role_name==role_name))).scalar_one_or_none()
    async def get_active(self,db:AsyncSession)->list[Role]:
        return list((await db.execute(select(Role).where(Role.is_active.is_(True)).order_by(Role.role_name))).scalars().all())
role_crud=RoleCRUD()
__all__=["RoleCRUD","role_crud"]
