import disnake


# ================================================================================================ #
# Role Created Embeds
# ================================================================================================ #

def role_created_by_bot(member, role_name):
    embed = disnake.Embed(
        title="Role Created",
        description=f"Bot - {member.mention}, created role `{role_name}`",
        color=disnake.Color.blue(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_created_by_bot_banned(member, role_name):
    embed = disnake.Embed(
        title="Role Created",
        description=f"Bot - {member.mention}, created role `{role_name}`. and was banned",
        color=disnake.Color.dark_red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_created_quarantined(member, role_name):
    embed = disnake.Embed(
        title="Role Created",
        description=f"User - {member.mention}, created role `{role_name}`. and was quarantined",
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_created_authorized(member, role):
    embed = disnake.Embed(
        title="Role Created",
        description=f"User - {member.mention}, created role - {role.mention}",
        color=disnake.Color.green(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


# ================================================================================================ #
# Role Deleted Embeds
# ================================================================================================ #

def role_deleted_by_bot(member, role_name):
    embed = disnake.Embed(
        title="Role Deleted",
        description=f"Bot - {member.mention}, deleted role `{role_name}`.",
        color=disnake.Color.blue(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_deleted_by_bot_banned(member, role_name):
    embed = disnake.Embed(
        title="Role Deleted",
        description=f"Bot - {member.mention}, deleted role `{role_name}`. and was banned",
        color=disnake.Color.dark_red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_deleted_quarantined(member, role_name, new_role):
    embed = disnake.Embed(
        title="Role Deleted",
        description=(
            f"User - {member.mention}, deleted role - `{role_name}`.\n"
            f"***and was quarantined.***\n"
            f"Role restored - {new_role.mention}"
            f"```Please move it to its original position```"
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_deleted_authorized(member, role_name):
    embed = disnake.Embed(
        title="Role Deleted",
        description=f"User - {member.mention}, deleted role - `{role_name}`",
        color=disnake.Color.green(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


# ================================================================================================ #
# Role Permissions Changed Embeds
# ================================================================================================ #

def role_perms_changed_authorized(member):
    embed = disnake.Embed(
        title="Role Permissions Changed",
        description=f"{member.mention} gave admin permissions to role",
        color=disnake.Color.blue(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


def role_perms_reverted(role, member):
    embed = disnake.Embed(
        title="Role Permissions Changed",
        description=(
            f"Role - {role.mention} was given admin permissions.\n"
            f"By - {member.mention}\n"
            f"```User Quarantined```"
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=member.avatar)
    return embed


# ================================================================================================ #
# Role Assignment / Removal Embeds
# ================================================================================================ #

def role_assigned_admin_punish(user, role, target, quarantine):
    embed = disnake.Embed(
        title="Role Assignment",
        description=(
            f"{user.mention} gave admin permissions - {role.mention} "
            f"to user - {target.mention}\n"
            f"and was sent to {quarantine.mention}"
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=user.avatar)
    return embed


def role_assigned_info(user, target, role):
    embed = disnake.Embed(title="Role Assignment", color=disnake.Color.green())
    embed.add_field(name="Action", value=f"{user.mention} assigned to {target.mention}", inline=False)
    embed.add_field(name="Role", value=f"{role.mention}", inline=False)
    embed.set_thumbnail(url=user.avatar)
    return embed


def role_removed_ai_punish(user, role_name, target, quarantine):
    embed = disnake.Embed(
        title="Role Removal",
        description=(
            f"{user.mention} removed AI role {role_name}, "
            f"from bot {target.mention} and got {quarantine.mention}."
        ),
        color=disnake.Color.red(),
    )
    embed.set_thumbnail(url=user.avatar)
    return embed


def role_removed_info(user, target, role):
    embed = disnake.Embed(title="Role Removal", color=disnake.Color.blue())
    embed.add_field(name="Action", value=f"{user.mention} removed role from {target.mention}", inline=False)
    embed.add_field(name="Role", value=f"{role.mention}", inline=False)
    embed.set_thumbnail(url=user.avatar)
    return embed
