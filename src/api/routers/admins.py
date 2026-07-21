# src/api/routers/admins.py
from fastapi import APIRouter, Depends, status
from src.api.auth import get_current_username
from src.services import admin_service

router = APIRouter(prefix="/api", tags=["Admins"], dependencies=[Depends(get_current_username)])

# ─── Admins ────────────────────────────────────────────────────────────────────

@router.get("/admins", response_model=list[int])
async def get_admins():
    return await admin_service.get_all_admins()

@router.post("/admins/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_admin(user_id: int):
    await admin_service.add_admin(user_id)
    return {"message": f"Admin {user_id} added"}

@router.delete("/admins/{user_id}")
async def remove_admin(user_id: int):
    await admin_service.remove_admin(user_id)
    return {"message": f"Admin {user_id} removed"}


# ─── Tracked Users ─────────────────────────────────────────────────────────────

@router.get("/tracked-users", response_model=list[int])
async def get_tracked_users():
    return await admin_service.get_all_tracked_users()

@router.post("/tracked-users/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_tracked_user(user_id: int):
    await admin_service.add_tracked_user(user_id)
    return {"message": f"User {user_id} tracked"}

@router.delete("/tracked-users/{user_id}")
async def remove_tracked_user(user_id: int):
    await admin_service.remove_tracked_user(user_id)
    return {"message": f"User {user_id} removed from tracking"}


# ─── Server Owners ─────────────────────────────────────────────────────────────

@router.get("/guilds/{guild_id}/owners", response_model=list[int])
async def get_server_owners(guild_id: int):
    return await admin_service.get_server_owners(guild_id)

@router.post("/guilds/{guild_id}/owners/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_server_owner(guild_id: int, user_id: int):
    await admin_service.add_server_owner(guild_id, user_id)
    return {"message": f"Owner {user_id} added to guild {guild_id}"}

@router.delete("/guilds/{guild_id}/owners/{user_id}")
async def remove_server_owner(guild_id: int, user_id: int):
    await admin_service.remove_server_owner(guild_id, user_id)
    return {"message": f"Owner {user_id} removed from guild {guild_id}"}
