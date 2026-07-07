import disnake


# ================================================================================================ #
# Member Join Embeds
# ================================================================================================ #

def bot_joined_unauthorized(bot_member, added_by):
    return disnake.Embed(
        title="Bot Joined",
        description=(
            f"Bot {bot_member.mention} added by - {added_by.mention}.\n"
            f"Bot banned, user quarantined."
        ),
        color=disnake.Color.red(),
    )


# ================================================================================================ #
# Ban Embeds
# ================================================================================================ #

def ban_unauthorized(member, user, reason):
    embed = disnake.Embed(title="Ban", description="", color=disnake.Color.red())
    embed.set_thumbnail(url=member.avatar)
    embed.add_field(name="User", value=f"▫{member.mention}", inline=True)
    embed.add_field(name="Banned by", value=f"▫{user.mention}", inline=True)
    embed.add_field(name="Reason", value=f"```{reason}, User was unbanned```", inline=False)
    return embed


def ban_authorized(member, user, reason):
    embed = disnake.Embed(title="Ban", description="", color=disnake.Color.dark_red())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="User", value=f"▫{member.mention}", inline=True)
    embed.add_field(name="Banned by", value=f"▫{user.mention}", inline=True)
    embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
    return embed


# ================================================================================================ #
# Moderation Command Embeds
# ================================================================================================ #

def roles_restored_success(user, member, roles_removed):
    embed = disnake.Embed(title="Roles Restored", description="", color=disnake.Color.dark_green())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="User:", value=f"▫{member.mention}", inline=False)
    embed.add_field(
        name="Roles:",
        value=f"{', '.join([role.mention for role in roles_removed])}",
        inline=False,
    )
    return embed


def roles_restored_empty(user, member):
    embed = disnake.Embed(title="Roles Restored", description="", color=disnake.Color.dark_green())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(name="User:", value=f"▫{member.mention}", inline=False)
    embed.add_field(
        name="Roles:",
        value="User has no removed roles in the last `10` minutes",
        inline=False,
    )
    return embed


def roles_restored_no_permission(user):
    embed = disnake.Embed(title="Roles Restored", description="", color=disnake.Color.dark_green())
    embed.set_thumbnail(url=user.avatar)
    embed.add_field(
        name="Error",
        value="```You don't have permission to use this command```",
        inline=False,
    )
    return embed


# ================================================================================================ #
# Admin Command Embeds
# ================================================================================================ #

def user_added_to_list(member):
    return disnake.Embed(
        title="Added to List",
        description=f"{member.mention}'s ID has been added to the list.",
        color=disnake.Color.blue(),
    )


def user_already_in_list(member):
    return disnake.Embed(
        title="Added to List",
        description=f"{member.mention}'s ID is already in the list.",
        color=disnake.Color.blue(),
    )


def user_removed_from_list(member):
    return disnake.Embed(
        title="Removed from List",
        description=f"{member.mention}'s ID has been removed from the list.",
        color=disnake.Color.blue(),
    )


def user_not_in_list(member):
    return disnake.Embed(
        title="Removed from List",
        description=f"{member.mention}'s ID is not in the list.",
        color=disnake.Color.blue(),
    )
