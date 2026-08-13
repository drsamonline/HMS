"""HHMS permission schemas."""
from __future__ import annotations
from pydantic import Field
from app.schemas.base import BaseSchema
class PermissionRead(BaseSchema):
    id:int; name:str; code:str; module:str; description:str|None; is_active:bool
__all__=["PermissionRead"]
