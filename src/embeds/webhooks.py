import disnake


# ================================================================================================ #
# Webhook Tracking Embeds
# ================================================================================================ #

def webhook_created_punish(member, channel):
    embed = disnake.Embed(
        title="Punishment Issued",
        description=(
            f"{member.mention} created a webhook in {channel.mention} "
            f"and was quarantined\n`Webhook deleted`"
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def webhook_created_authorized(member, channel):
    return disnake.Embed(
        title="Webhook Creation",
        description=f"{member.mention} created a webhook in {channel.mention}",
        color=disnake.Color.blue(),
    )
