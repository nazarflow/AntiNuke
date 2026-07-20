import disnake
from disnake.ext import commands
import config
from src.services import admin_service
from src.services import config_service
from src.services.limits_service import limiter
from src.embeds import roles as embeds


class RolesTracker(commands.Cog):
    """Tracks role creation, deletion, permission updates, and role assignment/removal."""

    def __init__(self, bot):
        self.bot = bot

    async def _get_roles(self, guild):
        """Helper to fetch commonly used roles."""
        return {
            "quarantine": guild.get_role(await config_service.get_role_id(guild.id, "quarantine") or 0),
            "server_booster": guild.get_role(await config_service.get_role_id(guild.id, "server_booster") or 0),
        }

    def _quarantine_roles(self, member, roles):
        """Build the list of roles to assign during quarantine (preserve booster)."""
        booster = roles.get("server_booster")
        quarantine = roles.get("quarantine")

        if booster and any(r.id == booster.id for r in member.roles):
            return [r for r in [quarantine, booster] if r]
        return [quarantine] if quarantine else []

    # ========================================================================================== #
    # on_guild_role_create
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        channel_id = await config_service.get_log_channel(guild.id, "role_updates")
        roles = await self._get_roles(guild)

        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_create).flatten()
        if not audit_log: return
        member = audit_log[0].user

        if member.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, member.id):
            return

        if member.bot:
            if member.get_role(config.AI_ROLE_ID) or disnake.utils.get(member.roles, name="Ai"):
                embed = embeds.role_created_by_bot(member, role.name)
            else:
                await role.delete()
                await member.ban(reason="Role Created without AI")
                embed = embeds.role_created_by_bot_banned(member, role.name)

            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch: await ch.send(embed=embed)
        else:
            limiter.add_action(guild.id, member.id, "roles")
            if not await limiter.check_limit(guild.id, member.id, "roles", member.roles):
                await role.delete()
                roles_to_add = self._quarantine_roles(member, roles)
                if roles_to_add:
                    await member.edit(roles=roles_to_add)
                embed = embeds.role_created_quarantined(member, role.name)
            else:
                embed = embeds.role_created_authorized(member, role)

            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch: await ch.send(embed=embed)

    # ========================================================================================== #
    # on_guild_role_delete
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        channel_id = await config_service.get_log_channel(guild.id, "role_updates")
        roles = await self._get_roles(guild)

        audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_delete).flatten()
        if not audit_log: return
        member = audit_log[0].user

        if member.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, member.id):
            return

        if role.managed:
            return

        if member.bot:
            if member.get_role(config.AI_ROLE_ID) or disnake.utils.get(member.roles, name="Ai"):
                embed = embeds.role_deleted_by_bot(member, role.name)
            else:
                await member.ban(reason="Role Deleted without AI")
                embed = embeds.role_deleted_by_bot_banned(member, role.name)

            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch: await ch.send(embed=embed)
        else:
            limiter.add_action(guild.id, member.id, "roles")
            if not await limiter.check_limit(guild.id, member.id, "roles", member.roles):
                new_role = await guild.create_role(
                    name=role.name, color=role.color,
                    hoist=role.hoist, mentionable=role.mentionable,
                    reason=f'Recreated role "{role.name}" after deletion by {member.name}',
                )
                embed = embeds.role_deleted_quarantined(member, role.name, new_role)
                roles_to_add = self._quarantine_roles(member, roles)
                if roles_to_add:
                    await member.edit(roles=roles_to_add)
            else:
                embed = embeds.role_deleted_authorized(member, role.name)

            if channel_id:
                ch = self.bot.get_channel(channel_id)
                if ch: await ch.send(embed=embed)

    # ========================================================================================== #
    # on_guild_role_update
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        channel_id = await config_service.get_log_channel(after.guild.id, "role_updates")

        if before.permissions != after.permissions and after.permissions.administrator:
            audit_log = await after.guild.audit_logs(
                limit=1, action=disnake.AuditLogAction.role_update
            ).flatten()
            if not audit_log: return
            member = audit_log[0].user

            if member.id == config.OWNER_ID or await admin_service.is_server_owner(after.guild.id, member.id):
                return

            limiter.add_action(after.guild.id, member.id, "roles")
            if not await limiter.check_limit(after.guild.id, member.id, "roles", member.roles):
                await self._revert_role_settings(after, before.guild, member)
            else:
                if channel_id:
                    ch = self.bot.get_channel(channel_id)
                    if ch: await ch.send(embed=embeds.role_perms_changed_authorized(member))

    async def _revert_role_settings(self, role, guild, member):
        """Revert a role's permissions back to default and quarantine the offender."""
        channel_id = await config_service.get_log_channel(guild.id, "role_updates")
        roles = await self._get_roles(guild)
        default_role = guild.default_role

        await role.edit(
            name=role.name, permissions=default_role.permissions,
            color=role.color, hoist=default_role.hoist,
            mentionable=default_role.mentionable,
        )

        if channel_id:
            ch = self.bot.get_channel(channel_id)
            if ch: await ch.send(embed=embeds.role_perms_reverted(role, member))

        roles_to_add = self._quarantine_roles(member, roles)
        if roles_to_add:
            await member.edit(roles=roles_to_add)

    # ========================================================================================== #
    # on_member_update (role assignment / removal tracking)
    # ========================================================================================== #

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel_id = await config_service.get_log_channel(after.guild.id, "role_updates")
        guild = after.guild
        roles = await self._get_roles(guild)

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
                    if user.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, user.id):
                        break

                    if role.permissions.administrator:
                        limiter.add_action(guild.id, user.id, "roles")
                        if not await limiter.check_limit(guild.id, user.id, "roles", user.roles):
                            embed = embeds.role_assigned_admin_punish(user, role, after, roles.get("quarantine"))
                            roles_to_add = self._quarantine_roles(user, roles)
                            if roles_to_add:
                                await user.edit(roles=roles_to_add)
                            await after.remove_roles(role)
                        else:
                            embed = embeds.role_assigned_info(user, after, role)
                    else:
                        embed = embeds.role_assigned_info(user, after, role)

                    if channel_id:
                        ch = self.bot.get_channel(channel_id)
                        if ch: await ch.send(embed=embed)
                    break

    async def _handle_role_removed(self, role, after, guild, roles, channel_id):
        """Handle when a role is removed from a member."""
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == after.id and entry.user.id != self.bot.user.id:
                before_roles = set(entry.changes.before.roles)
                after_roles = set(entry.changes.after.roles)

                if role in before_roles - after_roles:
                    user = entry.user
                    if user.id == config.OWNER_ID or await admin_service.is_server_owner(guild.id, user.id):
                        break

                    if role.name == "Ai":
                        limiter.add_action(guild.id, user.id, "roles")
                        if not await limiter.check_limit(guild.id, user.id, "roles", user.roles):
                            roles_to_add = self._quarantine_roles(user, roles)
                            if roles_to_add:
                                await user.edit(roles=roles_to_add)
                            await after.add_roles(role)
                            embed = embeds.role_removed_ai_punish(user, role.name, after, roles.get("quarantine"))
                        else:
                            embed = embeds.role_removed_info(user, after, role)
                    else:
                        embed = embeds.role_removed_info(user, after, role)

                    if channel_id:
                        ch = self.bot.get_channel(channel_id)
                        if ch: await ch.send(embed=embed)
                    break


def setup(bot):
    bot.add_cog(RolesTracker(bot))
