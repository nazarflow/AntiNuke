# src/api/routers/limits.py
from fastapi import APIRouter, Depends, HTTPException
from src.api.auth import get_current_username
from src.api import schemas
from src.services import admin_service

router = APIRouter(prefix="/api/limits", tags=["Custom Limits"], dependencies=[Depends(get_current_username)])

# ─── Custom Role Limits ────────────────────────────────────────────────────────

@router.get("/roles/{role_id}", response_model=schemas.CustomRoleLimitsResponse)
async def get_custom_role_limits(role_id: int):
    limits = await admin_service.get_custom_role_limits(role_id)
    if not limits:
        raise HTTPException(status_code=404, detail="Custom limits not found for this role")
    return schemas.CustomRoleLimitsResponse(role_id=role_id, guild_id=limits.get("guild_id", 0), **limits)

@router.post("/roles/{role_id}/guild/{guild_id}")
async def set_custom_role_limits(role_id: int, guild_id: int, limits: schemas.CustomRoleLimitsUpdate):
    data = limits.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    await admin_service.save_custom_role_limits(role_id, guild_id, **data)
    return {"message": "Custom role limits updated"}

@router.delete("/roles/{role_id}")
async def delete_custom_role_limits(role_id: int):
    deleted = await admin_service.delete_custom_role_limits(role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Limits not found")
    return {"message": "Custom role limits deleted"}


# ─── Custom User Limits ────────────────────────────────────────────────────────

@router.get("/users/{user_id}", response_model=schemas.CustomUserLimitsResponse)
async def get_custom_user_limits(user_id: int):
    limits = await admin_service.get_custom_user_limits(user_id)
    if not limits:
        raise HTTPException(status_code=404, detail="Custom limits not found for this user")
    return schemas.CustomUserLimitsResponse(user_id=user_id, guild_id=limits.get("guild_id", 0), **limits)

@router.post("/users/{user_id}/guild/{guild_id}")
async def set_custom_user_limits(user_id: int, guild_id: int, limits: schemas.CustomUserLimitsUpdate):
    data = limits.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    await admin_service.save_custom_user_limits(user_id, guild_id, **data)
    return {"message": "Custom user limits updated"}

@router.delete("/users/{user_id}")
async def delete_custom_user_limits(user_id: int):
    deleted = await admin_service.delete_custom_user_limits(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Limits not found")
    return {"message": "Custom user limits deleted"}
