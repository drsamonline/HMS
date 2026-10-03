"""Authentication endpoints."""
from __future__ import annotations
from fastapi import APIRouter,status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.auth import CurrentUserRead,LoginRequest,TokenResponse
from app.services.auth import auth_service
router=APIRouter(prefix="/auth",tags=["Authentication"])
@router.post("/login",response_model=TokenResponse,status_code=status.HTTP_200_OK)
async def login(credentials:LoginRequest,db:DatabaseSession)->TokenResponse:
    return TokenResponse(access_token=await auth_service.login(db,username=credentials.username,password=credentials.password))
@router.get("/me",response_model=CurrentUserRead)
async def current_user(db:DatabaseSession,current_user:CurrentUserDependency)->CurrentUserRead:
    user,roles,permissions=await auth_service.get_current_user_profile(db,user_id=int(str(current_user["sub"])))
    return CurrentUserRead(id=user.id,username=user.username,full_name=user.full_name,email=user.email,designation=user.designation,is_active=user.is_active,roles=roles,permissions=permissions)
__all__=["router","login","current_user"]
