import disnake
from disnake.ext import commands
from datetime import timedelta
import config
from src.services import admin_service
from src.services import config_service
from src.services.limits_service import limiter
from src.embeds import channels as embeds


class ChannelsTracker(commands.Cog):
    """Tracks channel creation, deletion, and permission updates."""

    def __init__(self, bot):
        self.bot = bot

    async def _get_roles(self, guild):
        """Helper to fetch commonly used roles."""
        return {
            "quarantine": guild.get_role(await config_service.get_role_id(guild.id, "quarantine") or 0),
            "server_booster": guild.get_role(await config_service.get_role_id(guild.id, "server_booster") or 0),
        }

    def _quarantine_roles(self, member, roles):
        """Build the list of roles to assign during quarantine (preserve booster)."""
        booster = roles.get("server_booster")
        quarantine = roles.get("quarantine")
        if booster and any(r.id == booster.id for r in member.roles):
            return [r for r in [quarantine, booster] if r]
        return [quarantine] if quarantine else []

    # ========================================================================================== #
    # on_guild_channel_create
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        log_channel_id = await config_service.get_log_channel(guild.id, "channel_create")
        log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None

        creator = None
        created_at = channel.created_at

        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_create):
            if entry.created_at >= created_at:
                creator = entry.user

        if not creator: return

        if creator.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, creator.id):
            return

        roles = await self._get_roles(guild)

        if creator.bot:
            member = guild.get_member(creator.id)

            # Allow if bot has AI role
            if member and member.get_role(config.AI_ROLE_ID):
                if log_channel: await log_channel.send(embed=embeds.channel_create_info(channel, creator))
                return

            # Or allow if bot has an admin custom role with limits
            if member:
                limiter.add_action(guild.id, creator.id, "channels")
                if await limiter.check_limit(guild.id, creator.id, "channels", member.roles):
                    if log_channel: await log_channel.send(embed=embeds.channel_create_info(channel, creator))
                    return

            await guild.ban(creator, reason="Bot banned for unauthorized actions.")
            if log_channel:
                await log_channel.send(embed=embeds.channel_create_bot_warning(creator))
            await channel.delete()
            return
        else:
            limiter.add_action(guild.id, creator.id, "channels")
            if not await limiter.check_limit(guild.id, creator.id, "channels", creator.roles):
                roles_to_add = self._quarantine_roles(creator, roles)
                if roles_to_add:
                    try:
                        await creator.edit(roles=roles_to_add, reason="User exceeded channel creation limit.")
                    except Exception:
                        pass
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_punish(creator, 0))
                await channel.delete()
            else:
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_info(channel, creator))

    # ========================================================================================== #
    # on_guild_channel_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        log_channel_id = await config_service.get_log_channel(guild.id, "channel_delete")
        log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None

        deleter = None
        async for entry in guild.audit_logs(limit=1):
            if entry.target.id == channel.id:
                deleter = entry.user
            break

        if deleter is None:
            return

        if deleter.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, deleter.id):
            return

        roles = await self._get_roles(guild)

        if deleter.bot:
            member = guild.get_member(deleter.id)

            # Allow if bot has AI role
            if member and member.get_role(config.AI_ROLE_ID):
                if log_channel: await log_channel.send(embed=embeds.channel_delete_info(channel.name, deleter))
                return

            if member:
                limiter.add_action(guild.id, deleter.id, "channels")
                if await limiter.check_limit(guild.id, deleter.id, "channels", member.roles):
                    if log_channel: await log_channel.send(embed=embeds.channel_delete_info(channel.name, deleter))
                    return

            await guild.ban(deleter, reason="Bot banned for unauthorized actions.")
            if log_channel:
                await log_channel.send(embed=embeds.channel_delete_bot_warning(deleter))
        else:
            limiter.add_action(guild.id, deleter.id, "channels")
            if not await limiter.check_limit(guild.id, deleter.id, "channels", deleter.roles):
                roles_to_add = self._quarantine_roles(deleter, roles)
                if roles_to_add:
                    await deleter.edit(roles=roles_to_add, reason="User moved to quarantine for exceeding channel deletion limit.")
                if log_channel:
                    await log_channel.send(embed=embeds.channel_delete_punish(deleter, 0))
                await self._restore_channel(channel, guild, deleter, log_channel)
            else:
                if log_channel:
                    await log_channel.send(embed=embeds.channel_delete_info(channel.name, deleter))

    async def _restore_channel(self, channel, guild, deleter, log_channel):
        """Recreate a deleted channel with the same settings."""
        new_channel = None

        if isinstance(channel, disnake.TextChannel):
            new_channel = await guild.create_text_channel(
                name=channel.name, position=channel.position,
                category=channel.category, overwrites=channel.overwrites,
                reason="Channel recreated after deletion",
            )
        elif isinstance(channel, disnake.VoiceChannel):
            new_channel = await guild.create_voice_channel(
                name=channel.name, position=channel.position,
                category=channel.category, overwrites=channel.overwrites,
                user_limit=channel.user_limit, reason="Channel recreated after deletion",
            )

        if new_channel and log_channel:
            await log_channel.send(embed=embeds.channel_restored(new_channel, deleter))

    # ========================================================================================== #
    # on_guild_channel_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = after.guild
        channel_id = await config_service.get_log_channel(guild.id, "channel_update")
        log_channel = self.bot.get_channel(channel_id) if channel_id else None
        roles = await self._get_roles(guild)

        audit_log = await guild.audit_logs(
            limit=1, action=disnake.AuditLogAction.overwrite_update
        ).flatten()
        if not audit_log: return
        user = audit_log[0].user

        if user.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, user.id):
            return

        if user.bot:
            member = guild.get_member(user.id)

            if member and member.get_role(config.AI_ROLE_ID):
                if log_channel: await log_channel.send(embed=embeds.channel_update_bot(user, after))
                return

            if member:
                limiter.add_action(guild.id, user.id, "channels")
                if await limiter.check_limit(guild.id, user.id, "channels", member.roles):
                    if log_channel: await log_channel.send(embed=embeds.channel_update_bot(user, after))
                    return

            await user.ban(reason="Channel permission changes")
        else:
            limiter.add_action(guild.id, user.id, "channels")
            if not await limiter.check_limit(guild.id, user.id, "channels", user.roles):
                if isinstance(after, disnake.TextChannel) and before.overwrites != after.overwrites:
                    for role, overwrite in after.overwrites.items():
                        if isinstance(role, disnake.Role) and overwrite != before.overwrites.get(role):
                            await after.set_permissions(role, overwrite=before.overwrites.get(role))
                            roles_to_add = self._quarantine_roles(user, roles)
                            if roles_to_add:
                                await user.edit(roles=roles_to_add)
                            if log_channel:
                                await log_channel.send(embed=embeds.channel_update_unauthorized(user, after, role))
            else:
                for role in after.overwrites:
                    if isinstance(role, disnake.Role) and role in before.overwrites:
                        if before.overwrites[role] != after.overwrites[role]:
                            if log_channel:
                                await log_channel.send(embed=embeds.channel_update_authorized(user, after, role))


def setup(bot):
    bot.add_cog(ChannelsTracker(bot))
