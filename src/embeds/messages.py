import disnake


# ================================================================================================ #
# Message Spam / Link Embeds
# ================================================================================================ #

def webhook_spam(webhook_name):
    return disnake.Embed(
        title="Webhook Spam",
        description=f"`{webhook_name}` was deleted.",
        color=disnake.Color.red(),
    )


def link_spam_punish(author):
    embed = disnake.Embed(
        title="Punishment Issued",
        description=f"{author.mention} posted an unauthorized link and was sent to quarantine.",
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=author.avatar)
    return embed


# ================================================================================================ #
# Message Edit / Delete Embeds
# ================================================================================================ #

def message_edited(author, original, edited, channel):
    embed = disnake.Embed(
        title="Message Edited",
        description=f"{author.mention} edited their message:",
        color=disnake.Color.blue(),
    )
    embed.add_field(name="Original Message", value=f"```{original}```", inline=False)
    embed.add_field(name="Edited Message", value=f"```{edited}```", inline=False)
    embed.add_field(name="Channel", value=f"{channel.mention}", inline=False)
    return embed


def message_deleted(author, content, channel, bot_mention):
    embed = disnake.Embed(
        title="Message Deleted",
        description=f"{author.mention} Deleted message {bot_mention}: ",
        color=disnake.Color.red(),
    )
    embed.add_field(name="Message", value=f"```{content}```", inline=False)
    embed.add_field(name="Channel", value=f"{channel.mention}", inline=False)
    return embed
