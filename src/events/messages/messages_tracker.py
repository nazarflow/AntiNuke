import disnake
from disnake.ext import commands
import config
from src import database
from src.embeds import messages as embeds
from src.rate_limiter import limiter


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

        guild_id = message.guild.id
        if message.author.id == config.OWNER_ID or database.is_server_owner(guild_id, message.author.id):
            pass # We still process command but owner bypasses punishment later
            
        log_channel = self.bot.get_channel(database.get_log_channel(guild_id, "links_spam") or 0)
        log_channel_hooks = self.bot.get_channel(database.get_log_channel(guild_id, "webhooks") or 0)
        quarantine = message.guild.get_role(database.get_role_id(guild_id, "quarantine") or 0)
        server_booster = message.guild.get_role(database.get_role_id(guild_id, "server_booster") or 0)

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
                if log_channel_hooks:
                    await log_channel_hooks.send(embed=embeds.webhook_spam(webhook.name))

        await self.bot.process_commands(message)

        # @here / @everyone spam detection
        if "@here" in message.content or "@everyone" in message.content:
            if message.author.id == config.OWNER_ID or database.is_server_owner(guild_id, message.author.id):
                return
                
            member = message.guild.get_member(message.author.id)
            if member is None: return
            
            limiter.add_action(guild_id, message.author.id, "links")
            if limiter.check_limit(guild_id, message.author.id, "links", member.roles):
                return

            try:
                await message.delete()
            except disnake.errors.NotFound:
                pass

            if log_channel:
                await log_channel.send(embed=embeds.link_spam_punish(message.author))

            if server_booster and any(r.id == server_booster.id for r in member.roles):
                roles_to_add = [r for r in [quarantine, server_booster] if r]
            else:
                roles_to_add = [quarantine] if quarantine else []
                
            if roles_to_add:
                await message.author.edit(roles=roles_to_add, reason="link")

    # ========================================================================================== #
    # on_message_edit
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content and before.guild:
            log_channel = self.bot.get_channel(database.get_log_channel(before.guild.id, "message_edit_delete") or 0)
            if log_channel:
                await log_channel.send(
                    embed=embeds.message_edited(before.author, before.content, after.content, before.channel)
                )

    # ========================================================================================== #
    # on_message_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild:
            log_channel = self.bot.get_channel(database.get_log_channel(message.guild.id, "message_edit_delete") or 0)
            if log_channel:
                await log_channel.send(
                    embed=embeds.message_deleted(message.author, message.content, message.channel, message.guild.me.mention)
                )


def setup(bot):
    bot.add_cog(MessagesTracker(bot))
