# src/api/routers/guilds.py
from fastapi import APIRouter, Depends, HTTPException
from src.api.auth import get_current_username
from src.api import schemas
from src.services import config_service

router = APIRouter(prefix="/api/guilds", tags=["Guild Configuration"], dependencies=[Depends(get_current_username)])

# ─── Guild Config ──────────────────────────────────────────────────────────────

@router.get("/{guild_id}/config", response_model=schemas.GuildConfigResponse)
async def get_guild_config(guild_id: int):
    res = await config_service.get_guild_config(guild_id)
    if not res:
        raise HTTPException(status_code=404, detail="Config not found")
    cat, ch = res
    return schemas.GuildConfigResponse(guild_id=guild_id, tuner_category_id=cat, tuner_channel_id=ch)

@router.post("/{guild_id}/config")
async def update_guild_config(guild_id: int, config: schemas.GuildConfigUpdate):
    cat_id = config.tuner_category_id if config.tuner_category_id is not None else 0
    ch_id = config.tuner_channel_id if config.tuner_channel_id is not None else 0
    await config_service.save_guild_config(guild_id, cat_id, ch_id)
    return {"message": "Config updated"}

@router.delete("/{guild_id}/config")
async def delete_guild_config(guild_id: int):
    await config_service.delete_guild_config(guild_id)
    return {"message": "Config deleted"}


# ─── Guild Roles ───────────────────────────────────────────────────────────────

@router.get("/{guild_id}/roles")
async def get_guild_roles(guild_id: int):
    row = await config_service.get_guild_roles(guild_id)
    if not row:
        raise HTTPException(status_code=404, detail="Roles not configured")
    return row

@router.post("/{guild_id}/roles")
async def update_guild_roles(guild_id: int, roles: schemas.GuildRolesUpdate):
    data = roles.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    await config_service.save_guild_roles(guild_id, **data)
    return {"message": "Roles updated"}


# ─── Guild Log Channels ────────────────────────────────────────────────────────

@router.get("/{guild_id}/log-channels")
async def get_guild_log_channels(guild_id: int):
    row = await config_service.get_guild_log_channels(guild_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log channels not configured")
    return row

@router.post("/{guild_id}/log-channels")
async def update_guild_log_channels(guild_id: int, channels: schemas.GuildLogChannelsUpdate):
    data = channels.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    await config_service.save_guild_log_channels(guild_id, **data)
    return {"message": "Log channels updated"}


# ─── Guild Limits ──────────────────────────────────────────────────────────────

@router.get("/{guild_id}/limits")
async def get_guild_limits(guild_id: int):
    row = await config_service.get_guild_limits(guild_id)
    if not row:
        raise HTTPException(status_code=404, detail="Guild limits not configured")
    return row

@router.post("/{guild_id}/limits")
async def update_guild_limits(guild_id: int, limits: schemas.GuildLimitsUpdate):
    data = limits.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    await config_service.save_guild_limits(guild_id, **data)
    return {"message": "Guild limits updated"}
