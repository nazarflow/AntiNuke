import disnake
from disnake.ext import commands
import config
from src.embeds import roles as embeds


class RolesTracker(commands.Cog):
    """Tracks role creation, deletion, permission updates, and role assignment/removal."""

    def __init__(self, bot):
        self.bot = bot

    def _get_roles(self, guild):
        """Helper to fetch commonly used roles."""
        return {
            "quarantine": guild.get_role(config.ROLES["quarantine"]),
            "dvp": guild.get_role(config.ROLES["dvp"]),
            "ai": guild.get_role(config.ROLES["ai"]),
            "server_booster": guild.get_role(config.ROLES["server_booster"]),
        }

    def _quarantine_roles(self, member, roles):
        """Build the list of roles to assign during quarantine (preserve booster)."""
        if any(r.id == config.ROLES["server_booster"] for r in member.roles):
            return [roles["quarantine"], roles["server_booster"]]
        return [roles["quarantine"]]

    # ========================================================================================== #
    # on_guild_role_create
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        channel_id = config.LOG_CHANNELS["role_updates"]
        roles = self._get_roles(guild)

        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_create).flatten()
        member = audit_log[0].user

        if member.bot:
            if disnake.utils.get(member.roles, name="Ai"):
                embed = embeds.role_created_by_bot(member, role.name)
            else:
                await role.delete()
                await member.ban(reason="Role Created without AI")
                embed = embeds.role_created_by_bot_banned(member, role.name)
            await self.bot.get_channel(channel_id).send(embed=embed)
        else:
            if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
                await role.delete()
                roles_to_add = self._quarantine_roles(member, roles)
                await member.edit(roles=roles_to_add)
                embed = embeds.role_created_quarantined(member, role.name)
            else:
                embed = embeds.role_created_authorized(member, role)
            await self.bot.get_channel(channel_id).send(embed=embed)

    # ========================================================================================== #
    # on_guild_role_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        channel_id = config.LOG_CHANNELS["role_updates"]
        roles = self._get_roles(guild)

        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_delete).flatten()
        member = audit_log[0].user

        if role.managed:
            return

        if member.bot:
            if disnake.utils.get(member.roles, name="Ai"):
                embed = embeds.role_deleted_by_bot(member, role.name)
            else:
                await member.ban(reason="Role Deleted without AI")
                embed = embeds.role_deleted_by_bot_banned(member, role.name)
            await self.bot.get_channel(channel_id).send(embed=embed)
        else:
            if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
                new_role = await guild.create_role(
                    name=role.name, color=role.color,
                    hoist=role.hoist, mentionable=role.mentionable,
                    reason=f'Recreated role "{role.name}" after deletion by {member.name}',
                )
                embed = embeds.role_deleted_quarantined(member, role.name, new_role)
                roles_to_add = self._quarantine_roles(member, roles)
                await member.edit(roles=roles_to_add)
            else:
                embed = embeds.role_deleted_authorized(member, role.name)
            await self.bot.get_channel(channel_id).send(embed=embed)

    # ========================================================================================== #
    # on_guild_role_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        channel_id = config.LOG_CHANNELS["role_updates"]

        if before.permissions != after.permissions and after.permissions.administrator:
            audit_log = await after.guild.audit_logs(
                limit=1, action=disnake.AuditLogAction.role_update
            ).flatten()
            member = audit_log[0].user

            if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
                await self._revert_role_settings(after, before.guild)
            else:
                await self.bot.get_channel(channel_id).send(
                    embed=embeds.role_perms_changed_authorized(member)
                )

    async def _revert_role_settings(self, role, guild):
        """Revert a role's permissions back to default and quarantine the offender."""
        channel_id = config.LOG_CHANNELS["role_updates"]
        roles = self._get_roles(guild)
        default_role = guild.default_role

        audit_log = await guild.audit_logs(
            limit=1, action=disnake.AuditLogAction.role_update
        ).flatten()
        member = audit_log[0].user

        await role.edit(
            name=role.name, permissions=default_role.permissions,
            color=role.color, hoist=default_role.hoist,
            mentionable=default_role.mentionable,
        )

        await self.bot.get_channel(channel_id).send(
            embed=embeds.role_perms_reverted(role, member)
        )

        roles_to_add = self._quarantine_roles(member, roles)
        await member.edit(roles=roles_to_add)

    # ========================================================================================== #
    # on_member_update (role assignment / removal tracking)
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel_id = config.LOG_CHANNELS["role_updates"]
        guild = after.guild
        roles = self._get_roles(guild)

        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)

        for role in added_roles:
            await self._handle_role_added(role, after, guild, roles, channel_id)

        for role in removed_roles:
            await self._handle_role_removed(role, after, guild, roles, channel_id)

    async def _handle_role_added(self, role, after, guild, roles, channel_id):
        """Handle when a role is added to a member."""
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == after.id and entry.user.id != self.bot.user.id:
                before_roles = set(entry.changes.before.roles)
                after_roles = set(entry.changes.after.roles)

                if role in after_roles - before_roles:
                    user = entry.user

                    if role.permissions.administrator and roles["dvp"] not in user.roles:
                        embed = embeds.role_assigned_admin_punish(user, role, after, roles["quarantine"])
                        roles_to_add = self._quarantine_roles(user, roles)
                        await user.edit(roles=roles_to_add)
                        await after.remove_roles(role)
                    else:
                        embed = embeds.role_assigned_info(user, after, role)

                    await self.bot.get_channel(channel_id).send(embed=embed)
                    break

    async def _handle_role_removed(self, role, after, guild, roles, channel_id):
        """Handle when a role is removed from a member."""
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == after.id and entry.user.id != self.bot.user.id:
                before_roles = set(entry.changes.before.roles)
                after_roles = set(entry.changes.after.roles)

                if role in before_roles - after_roles:
                    user = entry.user

                    if role.name == "Ai" and roles["dvp"] not in user.roles:
                        roles_to_add = self._quarantine_roles(user, roles)
                        await user.edit(roles=roles_to_add)
                        await after.add_roles(roles["ai"])
                        embed = embeds.role_removed_ai_punish(user, role.name, after, roles["quarantine"])
                    else:
                        embed = embeds.role_removed_info(user, after, role)

                    await self.bot.get_channel(channel_id).send(embed=embed)
                    break


def setup(bot):
    bot.add_cog(RolesTracker(bot))
