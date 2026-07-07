import disnake


# ================================================================================================ #
# Channel Creation Embeds
# ================================================================================================ #

def channel_create_punish(creator, channels_created):
    embed = disnake.Embed(
        title="Punishment Issued",
        description=(
            f"{creator.mention} Received Quarantine role for creating "
            f"`{channels_created}` channels in `30` minutes."
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=creator.avatar)
    return embed


def channel_create_info(channel, creator):
    embed = disnake.Embed(
        title="Channel Creation",
        description=f"New channel {channel.mention} created by - {creator.mention}",
        color=disnake.Color.green(),
    )
    embed.set_thumbnail(url=creator.avatar)
    return embed


def channel_create_bot_warning(creator):
    return disnake.Embed(
        title="Warning",
        description=(
            f"New channel created by bot - {creator.mention}.\n"
            f"`Channels deleted, bot banned.`"
        ),
        color=disnake.Color.red(),
    )


# ================================================================================================ #
# Channel Deletion Embeds
# ================================================================================================ #

def channel_delete_punish(deleter, channels_deleted):
    embed = disnake.Embed(
        title="Punishment Issued",
        description=(
            f"{deleter.mention} received Quarantine for deleting "
            f"`{channels_deleted}` channels in `30` minutes."
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=deleter.avatar)
    return embed


def channel_delete_info(channel_name, deleter):
    embed = disnake.Embed(
        title="Channel Deletion",
        description=f"Channel `{channel_name}` was deleted by - {deleter.mention}.",
        color=disnake.Color.green(),
    )
    embed.set_thumbnail(url=deleter.avatar)
    return embed


def channel_delete_bot_warning(deleter):
    embed = disnake.Embed(
        title="Attention",
        description=f"Bot deleted a channel and was banned: {deleter.mention}.",
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=deleter.avatar)
    return embed


def channel_restored(new_channel, deleter):
    embed = disnake.Embed(
        title="Channel Restoration",
        description=f"Restoring `{new_channel}` after deletion...",
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=deleter.avatar)
    return embed


# ================================================================================================ #
# Channel Update Embeds
# ================================================================================================ #

def channel_update_bot(user, channel):
    embed = disnake.Embed(title="Channel Updated", description="", color=disnake.Color.blue())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="Bot", value=f"▫{user.mention}", inline=True)
    embed.add_field(name="Channel", value=f"▫{channel.mention}", inline=True)
    embed.add_field(
        name="Action",
        value="```Bot changed channel settings (role manipulation)```",
        inline=False,
    )
    return embed


def channel_update_unauthorized(user, channel, role=None):
    embed = disnake.Embed(title="Channel Updated", description="", color=disnake.Color.dark_red())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="User", value=f"▫{user.mention}", inline=True)
    embed.add_field(name="Channel", value=f"▫{channel.mention}", inline=True)
    if role is not None:
        embed.add_field(name="Role", value=f"▫{role.mention}", inline=True)
    embed.add_field(
        name="Action",
        value="```Changed role permissions and was quarantined```",
        inline=False,
    )
    return embed


def channel_update_authorized(user, channel, role):
    embed = disnake.Embed(title="Channel Updated", description="", color=disnake.Color.dark_green())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="User", value=f"▫{user.mention}", inline=True)
    embed.add_field(name="Channel", value=f"▫{channel.mention}", inline=True)
    embed.add_field(name="Role", value=f"▫{role.mention}", inline=True)
    embed.add_field(
        name="Action",
        value="```Changed channel settings (role manipulation)```",
        inline=False,
    )
    return embed
