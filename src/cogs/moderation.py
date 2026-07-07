import disnake
from disnake.ext import commands
from datetime import datetime, timedelta, timezone
import config
from src.embeds.members import roles_restored_success, roles_restored_empty, roles_restored_no_permission


class Moderation(commands.Cog):
    """Moderation commands (role restoration, etc.)."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================================================== #
    # !back - Restore recently removed roles for a user
    # ========================================================================================== #

    @commands.command()
    async def back(self, ctx, member: disnake.Member):
        user = member
        channel_id = config.LOG_CHANNELS["role_updates"]

        if ctx.author.id not in self.bot.admins:
            embed = roles_restored_no_permission(user)
        else:
            audit_log_entries = await ctx.guild.audit_logs(
                limit=None, action=disnake.AuditLogAction.member_role_update
            ).flatten()
            roles_removed = []
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)

            for entry in audit_log_entries:
                if entry.created_at < time_threshold or entry.target.id != user.id:
                    continue
                roles_before = set(entry.before.roles)
                roles_after = set(entry.after.roles)
                roles_removed += list(roles_before - roles_after)

            if roles_removed:
                await user.add_roles(*roles_removed)
                embed = roles_restored_success(user, member, roles_removed)
            else:
                embed = roles_restored_empty(user, member)

        await self.bot.get_channel(channel_id).send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
