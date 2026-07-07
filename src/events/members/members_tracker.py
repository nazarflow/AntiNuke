import disnake
from disnake.ext import commands
import config
from src.embeds import members as embeds


class MembersTracker(commands.Cog):
    """Tracks member join (bot detection), bans, and voice state updates."""

    def __init__(self, bot):
        self.bot = bot

    def _quarantine_roles(self, member, guild):
        """Build the list of roles to assign during quarantine (preserve booster)."""
        quarantine = guild.get_role(config.ROLES["quarantine"])
        server_booster = guild.get_role(config.ROLES["server_booster"])
        if any(r.id == config.ROLES["server_booster"] for r in member.roles):
            return [quarantine, server_booster]
        return [quarantine]

    # ========================================================================================== #
    # on_member_join (unauthorized bot detection)
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = config.LOG_CHANNELS["bot_joins"]
        guild = member.guild
        dvp = disnake.utils.get(guild.roles, id=config.ROLES["dvp"])

        if not member.bot:
            return

        added_by = None
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                added_by = entry.user
                break

        if added_by and added_by.id == config.OWNER_ID:
            await self.bot.get_channel(channel_id).send(
                f"Authorized developer <@{config.OWNER_ID}> added bot - {member.mention}. All hail the dev!"
            )
        else:
            roles_to_add = self._quarantine_roles(added_by, guild)
            await member.ban(reason="Unauthorized Bot")
            await added_by.edit(roles=roles_to_add, reason="Adding bot to server")
            await self.bot.get_channel(channel_id).send(
                embed=embeds.bot_joined_unauthorized(member, added_by)
            )
            await self.bot.get_channel(channel_id).send(f"{dvp.mention} - Please investigate")

    # ========================================================================================== #
    # on_member_ban
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        dvp = guild.get_role(config.ROLES["dvp"])
        channel_id = config.LOG_CHANNELS["bans"]

        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.ban).flatten()
        member = audit_log[0].user
        reason = audit_log[0].reason if audit_log else "No reason provided."

        if reason is None:
            reason = "Reason not provided"

        if dvp not in member.roles:
            roles_to_add = self._quarantine_roles(member, guild)
            await member.edit(roles=roles_to_add)
            await guild.unban(user, reason="Banned by mistake")
            embed = embeds.ban_unauthorized(member, user, reason)
        else:
            embed = embeds.ban_authorized(member, user, reason)

        await self.bot.get_channel(channel_id).send(embed=embed)

    # ========================================================================================== #
    # on_voice_state_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.bot.user_ids and before.channel != after.channel and after.channel is not None:
            channel = self.bot.get_channel(config.LOG_CHANNELS["voice_move"])
            await member.move_to(channel)


def setup(bot):
    bot.add_cog(MembersTracker(bot))
