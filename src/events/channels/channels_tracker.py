import disnake
from disnake.ext import commands
from datetime import timedelta
import config
from src.embeds import channels as embeds


class ChannelsTracker(commands.Cog):
    """Tracks channel creation, deletion, and permission updates."""

    def __init__(self, bot):
        self.bot = bot

    def _get_roles(self, guild):
        """Helper to fetch commonly used roles."""
        return {
            "quarantine": disnake.utils.get(guild.roles, id=config.ROLES["quarantine"]),
            "dvp": disnake.utils.get(guild.roles, id=config.ROLES["dvp"]),
            "ai": disnake.utils.get(guild.roles, id=config.ROLES["ai"]),
            "server_booster": disnake.utils.get(guild.roles, id=config.ROLES["server_booster"]),
        }

    def _quarantine_roles(self, member, roles):
        """Build the list of roles to assign during quarantine (preserve booster)."""
        if any(r.id == config.ROLES["server_booster"] for r in member.roles):
            return [roles["quarantine"], roles["server_booster"]]
        return [roles["quarantine"]]

    # ========================================================================================== #
    # on_guild_channel_create
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = self.bot.get_channel(config.LOG_CHANNELS["channel_create"])
        guild = channel.guild
        creator = None
        created_at = channel.created_at

        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_create):
            if entry.created_at >= created_at:
                creator = entry.user

        roles = self._get_roles(guild)
        history = await guild.audit_logs(
            limit=20, action=disnake.AuditLogAction.channel_create
        ).filter(
            lambda e: e.user == creator and e.created_at > created_at - timedelta(minutes=30)
        ).flatten()
        channels_created = len(history)

        if creator.bot:
            member = guild.get_member(creator.id)
            if member and any(r.id == config.ROLES["ai"] for r in member.roles):
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_info(channel, creator))
                return
            else:
                await guild.ban(creator, reason="Bot banned for unauthorized actions.")
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_bot_warning(creator))
                await channel.delete()
                return
        else:
            if channels_created >= 1 and roles["dvp"] not in creator.roles and roles["ai"] not in creator.roles:
                roles_to_add = self._quarantine_roles(creator, roles)
                try:
                    await creator.edit(roles=roles_to_add, reason="User exceeded channel creation limit.")
                except Exception:
                    print(f"Failed to quarantine user {creator.id}")
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_punish(creator, channels_created))
                await channel.delete()
            else:
                if log_channel:
                    await log_channel.send(embed=embeds.channel_create_info(channel, creator))

    # ========================================================================================== #
    # on_guild_channel_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = self.bot.get_channel(config.LOG_CHANNELS["channel_delete"])
        guild = channel.guild

        deleter = None
        async for entry in guild.audit_logs(limit=1):
            if entry.target.id == channel.id:
                deleter = entry.user
            break

        if deleter is None:
            return

        roles = self._get_roles(guild)
        history = await guild.audit_logs(
            limit=20, action=disnake.AuditLogAction.channel_delete
        ).filter(
            lambda e: e.user == deleter and e.created_at > channel.created_at - timedelta(minutes=30)
        ).flatten()
        channels_deleted = len(history)

        if deleter.bot:
            member = guild.get_member(deleter.id)
            if member and any(r.id == config.ROLES["ai"] for r in member.roles):
                try:
                    await log_channel.send(embed=embeds.channel_delete_info(channel.name, deleter))
                except AttributeError:
                    pass
            else:
                await guild.ban(deleter, reason="Bot banned for unauthorized actions.")
                try:
                    await log_channel.send(embed=embeds.channel_delete_bot_warning(deleter))
                except AttributeError:
                    pass
        else:
            if channels_deleted >= 1 and roles["dvp"] not in deleter.roles and roles["ai"] not in deleter.roles:
                roles_to_add = self._quarantine_roles(deleter, roles)
                await deleter.edit(roles=roles_to_add, reason="User moved to quarantine for exceeding channel deletion limit.")
                try:
                    await log_channel.send(embed=embeds.channel_delete_punish(deleter, channels_deleted))
                except AttributeError:
                    pass
            else:
                try:
                    await log_channel.send(embed=embeds.channel_delete_info(channel.name, deleter))
                except AttributeError:
                    pass

        if roles["dvp"] not in deleter.roles and roles["ai"] not in deleter.roles:
            await self._restore_channel(channel, guild, deleter, log_channel)

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

        if new_channel:
            try:
                await log_channel.send(embed=embeds.channel_restored(new_channel, deleter))
            except AttributeError:
                pass

    # ========================================================================================== #
    # on_guild_channel_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        channel_id = config.LOG_CHANNELS["channel_update"]
        guild = after.guild
        roles = self._get_roles(guild)

        audit_log = await guild.audit_logs(
            limit=1, action=disnake.AuditLogAction.overwrite_update
        ).flatten()
        user = audit_log[0].user

        if user.bot:
            if roles["ai"] not in user.roles:
                await user.ban(reason="Channel permission changes")
            else:
                await self.bot.get_channel(channel_id).send(
                    embed=embeds.channel_update_bot(user, after)
                )
        else:
            if roles["dvp"] not in user.roles:
                if isinstance(after, disnake.TextChannel) and before.overwrites != after.overwrites:
                    for role, overwrite in after.overwrites.items():
                        if isinstance(role, disnake.Role) and overwrite != before.overwrites.get(role):
                            await after.set_permissions(role, overwrite=before.overwrites.get(role))
                            roles_to_add = self._quarantine_roles(user, roles)
                            await user.edit(roles=roles_to_add)
                            await self.bot.get_channel(channel_id).send(
                                embed=embeds.channel_update_unauthorized(user, after, role)
                            )
            else:
                for role in after.overwrites:
                    if isinstance(role, disnake.Role) and role in before.overwrites:
                        if before.overwrites[role] != after.overwrites[role]:
                            await self.bot.get_channel(channel_id).send(
                                embed=embeds.channel_update_authorized(user, after, role)
                            )


def setup(bot):
    bot.add_cog(ChannelsTracker(bot))
