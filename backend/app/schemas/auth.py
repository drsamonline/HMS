"""Authentication schemas."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
class LoginRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", str_strip_whitespace=True)
    username:str=Field(min_length=1,max_length=150)
    password:str=Field(min_length=1,max_length=256)
class TokenResponse(BaseModel):
    model_config=ConfigDict(extra="forbid")
    access_token:str; token_type:str="bearer"
class CurrentUserRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; username:str; full_name:str; email:str|None; designation:str|None; is_active:bool
    roles:list[str]
    permissions:list[str]
__all__=["LoginRequest","TokenResponse","CurrentUserRead"]
