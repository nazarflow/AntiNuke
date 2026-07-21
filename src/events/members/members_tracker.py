import disnake
from disnake.ext import commands
import config
from src.services import admin_service
from src.services import config_service
from src.services.limits_service import limiter
from src.embeds import members as embeds


class MembersTracker(commands.Cog):
    """Tracks member join (bot detection), bans, and voice state updates."""

    def __init__(self, bot):
        self.bot = bot

    async def _quarantine_roles(self, member, guild):
        quarantine = guild.get_role(await config_service.get_role_id(guild.id, "quarantine") or 0)
        server_booster = guild.get_role(await config_service.get_role_id(guild.id, "server_booster") or 0)
        if server_booster and any(r.id == server_booster.id for r in member.roles):
            return [r for r in [quarantine, server_booster] if r]
        return [quarantine] if quarantine else []

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        channel_id = await config_service.get_log_channel(guild.id, "bot_joins")
        if not member.bot:
            return
        added_by = None
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                added_by = entry.user
                break
        if added_by and (added_by.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, added_by.id)):
            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch:
                    await ch.send(f"Authorized developer <@{config.OWNER_ID}> added bot - {member.mention}. All hail the dev!")
        else:
            roles_to_add = await self._quarantine_roles(added_by, guild) if added_by else []
            await member.ban(reason="Unauthorized Bot")
            if added_by and roles_to_add:
                await added_by.edit(roles=roles_to_add, reason="Adding bot to server")
            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch:
                    await ch.send(embed=embeds.bot_joined_unauthorized(member, added_by))

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel_id = await config_service.get_log_channel(guild.id, "bans")
        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.ban).flatten()
        if not audit_log: return
        member = audit_log[0].user
        reason = audit_log[0].reason or "Reason not provided"
        if member.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, member.id):
            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch: await ch.send(embed=embeds.ban_authorized(member, user, reason))
            return
        limiter.add_action(guild.id, member.id, "roles")
        if not await limiter.check_limit(guild.id, member.id, "roles", member.roles):
            roles_to_add = await self._quarantine_roles(member, guild)
            if roles_to_add:
                await member.edit(roles=roles_to_add)
            await guild.unban(user, reason="Banned by mistake")
            embed = embeds.ban_unauthorized(member, user, reason)
        else:
            embed = embeds.ban_authorized(member, user, reason)
        if channel_id:
            ch = self.bot.get_channel(channel_id)
            if ch: await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.bot.user_ids and before.channel != after.channel and after.channel is not None:
            channel_id = await config_service.get_log_channel(member.guild.id, "voice_move")
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await member.move_to(channel)


def setup(bot):
    bot.add_cog(MembersTracker(bot))
