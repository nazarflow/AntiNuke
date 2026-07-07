import disnake
from disnake.ext import commands
import config
from src.embeds import messages as embeds


class MessagesTracker(commands.Cog):
    """Tracks messages: @here/@everyone spam, webhook spam, edits, and deletions."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================================================== #
    # on_message (link spam / webhook spam detection)
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        log_channel = self.bot.get_channel(config.LOG_CHANNELS["links_spam"])
        log_channel_hooks = self.bot.get_channel(config.LOG_CHANNELS["webhooks"])
        quarantine = disnake.utils.get(message.guild.roles, id=config.ROLES["quarantine"])
        dvp = disnake.utils.get(message.guild.roles, id=config.ROLES["dvp"])
        server_booster = disnake.utils.get(message.guild.roles, id=config.ROLES["server_booster"])

        # Webhook spam detection
        if message.webhook_id and ("@everyone" in message.content or "@here" in message.content):
            webhooks = await message.channel.webhooks()
            webhook = None
            for w in webhooks:
                if w.id == message.webhook_id:
                    webhook = w
                    break

            await message.delete()

            if webhook:
                webhooks = await message.channel.webhooks()
                for wh in webhooks:
                    if wh.id == message.webhook_id:
                        await wh.delete()
                await log_channel_hooks.send(embed=embeds.webhook_spam(webhook.name))

        await self.bot.process_commands(message)

        # @here / @everyone spam detection
        if "@here" in message.content or "@everyone" in message.content:
            member = message.guild.get_member(message.author.id)
            if member is not None and (quarantine in member.roles or dvp in member.roles):
                return

            try:
                await message.delete()
            except disnake.errors.NotFound:
                pass

            await log_channel.send(embed=embeds.link_spam_punish(message.author))

            if any(r.id == config.ROLES["server_booster"] for r in member.roles):
                roles_to_add = [quarantine, server_booster]
            else:
                roles_to_add = [quarantine]
            await message.author.edit(roles=roles_to_add, reason="link")

    # ========================================================================================== #
    # on_message_edit
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            log_channel = self.bot.get_channel(config.LOG_CHANNELS["message_edit_delete"])
            await log_channel.send(
                embed=embeds.message_edited(before.author, before.content, after.content, before.channel)
            )

    # ========================================================================================== #
    # on_message_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        log_channel = self.bot.get_channel(config.LOG_CHANNELS["message_edit_delete"])
        await log_channel.send(
            embed=embeds.message_deleted(message.author, message.content, message.channel, message.guild.me.mention)
        )


def setup(bot):
    bot.add_cog(MessagesTracker(bot))
