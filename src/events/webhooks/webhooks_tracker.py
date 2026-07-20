import disnake
from disnake.ext import commands
import config
from src.services import admin_service
from src.services import config_service
from src.services.limits_service import limiter
from src.embeds import webhooks as embeds


class WebhooksTracker(commands.Cog):
    """Tracks webhook creation and bans unauthorized webhook usage."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild = channel.guild
        webhooks = await channel.webhooks()
        log_channel_id = await config_service.get_log_channel(guild.id, "webhooks")
        log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None
        server_booster = guild.get_role(await config_service.get_role_id(guild.id, "server_booster") or 0)
        quarantine = guild.get_role(await config_service.get_role_id(guild.id, "quarantine") or 0)

        for webhook in webhooks:
            if webhook.user:
                member = guild.get_member(webhook.user.id)
                if member and (member.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, member.id)):
                    continue
                if member:
                    limiter.add_action(guild.id, member.id, "webhooks")
                    if not await limiter.check_limit(guild.id, member.id, "webhooks", member.roles):
                        if server_booster and any(r.id == server_booster.id for r in member.roles):
                            roles_to_add = [r for r in [quarantine, server_booster] if r]
                        else:
                            roles_to_add = [quarantine] if quarantine else []
                        if roles_to_add:
                            await member.edit(roles=roles_to_add, reason="User moved to quarantine.")
                        if log_channel:
                            await log_channel.send(embed=embeds.webhook_created_punish(member, channel))
                        try:
                            await webhook.delete()
                        except disnake.errors.NotFound:
                            pass
                    else:
                        if log_channel:
                            await log_channel.send(embed=embeds.webhook_created_authorized(member, channel))
                        return

            if webhook.user and webhook.user.bot:
                await guild.ban(webhook.user, reason="Webhook created by a bot")
                try:
                    await webhook.delete()
                except disnake.errors.NotFound:
                    pass
            else:
                try:
                    await webhook.delete()
                except disnake.errors.NotFound:
                    pass


def setup(bot):
    bot.add_cog(WebhooksTracker(bot))
