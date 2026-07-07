import disnake
from disnake.ext import commands
import config
from src.embeds import webhooks as embeds


class WebhooksTracker(commands.Cog):
    """Tracks webhook creation and bans unauthorized webhook usage."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================================================== #
    # on_webhooks_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        webhooks = await channel.webhooks()
        log_channel = self.bot.get_channel(config.LOG_CHANNELS["webhooks"])
        server_booster = channel.guild.get_role(config.ROLES["server_booster"])

        for webhook in webhooks:
            if webhook.user:
                member = channel.guild.get_member(webhook.user.id)

                if member and not any(r.id == config.ROLES["dvp"] for r in member.roles):
                    quarantine = channel.guild.get_role(config.ROLES["quarantine"])

                    if any(r.id == config.ROLES["server_booster"] for r in member.roles):
                        roles_to_add = [quarantine, server_booster]
                    else:
                        roles_to_add = [quarantine]

                    await member.edit(roles=roles_to_add, reason="User moved to quarantine.")
                    await log_channel.send(embed=embeds.webhook_created_punish(member, channel))

                    try:
                        await webhook.delete()
                    except disnake.errors.NotFound:
                        pass
                else:
                    await log_channel.send(embed=embeds.webhook_created_authorized(member, channel))
                    return

            if webhook.user and webhook.user.bot:
                await channel.guild.ban(webhook.user, reason="Webhook created by a bot")
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
