import disnake
from src import database
import config


# ================================================================================================ #
# ROLE Modals (moved from dev_panel.py)
# ================================================================================================ #

class CreateAdminRoleModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(label="Role Name", placeholder="E.g., DVP or AI", custom_id="role_name", style=disnake.TextInputStyle.short, max_length=100, required=True),
            disnake.ui.TextInput(label="Channels (Actions Mins)", placeholder="E.g., 5 10", custom_id="channels_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Roles (Actions Mins)", placeholder="E.g., 3 60", custom_id="roles_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Links/Spam (Actions Mins)", placeholder="E.g., 10 5", custom_id="links_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Webhooks (Actions Mins)", placeholder="E.g., 2 60", custom_id="webhooks_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
        ]
        super().__init__(title="Create Admin Role", custom_id="adm_create_role_modal", components=components)

    def parse_limits(self, text):
        try:
            parts = text.strip().split()
            if len(parts) >= 2: return int(parts[0]), int(parts[1])
            elif len(parts) == 1: return int(parts[0]), 60
            return 0, 0
        except ValueError:
            return 0, 0

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        name = inter.text_values["role_name"]
        ch_l, ch_t = self.parse_limits(inter.text_values["channels_limits"])
        rl_l, rl_t = self.parse_limits(inter.text_values["roles_limits"])
        lnk_l, lnk_t = self.parse_limits(inter.text_values["links_limits"])
        wh_l, wh_t = self.parse_limits(inter.text_values["webhooks_limits"])
        try:
            role = await inter.guild.create_role(name=name, reason="Created via Admin Panel")
            database.save_custom_role_limits(role.id, inter.guild.id, channels_limit=ch_l, channels_time=ch_t, roles_limit=rl_l, roles_time=rl_t, links_limit=lnk_l, links_time=lnk_t, webhooks_limit=wh_l, webhooks_time=wh_t)
            await inter.edit_original_response(f"✅ Role {role.mention} created with custom limits!")
        except Exception as e:
            await inter.edit_original_response(f"❌ Error: {e}")


class RemoveAdminRoleModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="Role ID to remove", placeholder="Insert ID...", custom_id="role_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Remove Admin Role", custom_id="adm_remove_role_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        rid = inter.text_values["role_id"]
        if not rid.isdigit():
            await inter.response.send_message("❌ Invalid ID format.", ephemeral=True)
            return
        role_id = int(rid)
        role = inter.guild.get_role(role_id)
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM custom_role_limits WHERE role_id = ?', (role_id,))
        changes = cursor.rowcount
        conn.commit()
        conn.close()
        msg = f"✅ Role `ID:{role_id}` removed from DB." if changes > 0 else f"⚠️ Role `ID:{role_id}` not found in DB."
        if role:
            try:
                await role.delete(reason="Deleted via Admin Panel")
                msg += f"\n✅ Role `@{role.name}` removed from server."
            except Exception as e:
                msg += f"\n❌ Error removing from server: {e}"
        else:
            msg += "\n⚠️ Role no longer existed on the server."
        await inter.response.send_message(msg, ephemeral=True)


class EditAdminRoleLimitsModal(disnake.ui.Modal):
    def __init__(self, role_id, current_limits):
        self.role_id = role_id
        components = [
            disnake.ui.TextInput(label="Channels Limit", value=str(current_limits["channels_limit"]), custom_id="channels_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Roles Limit", value=str(current_limits["roles_limit"]), custom_id="roles_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Links/Spam Limit", value=str(current_limits["links_limit"]), custom_id="links_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Webhooks Limit", value=str(current_limits["webhooks_limit"]), custom_id="webhooks_limit", style=disnake.TextInputStyle.short, required=True),
        ]
        super().__init__(title="Edit Role Limits", custom_id=f"adm_edit_role_{role_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        try:
            vals = {k: int(inter.text_values[k]) for k in ["channels_limit", "roles_limit", "links_limit", "webhooks_limit"]}
        except ValueError:
            await inter.response.send_message("❌ All limits must be numbers.", ephemeral=True)
            return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE custom_role_limits SET channels_limit=?, roles_limit=?, links_limit=?, webhooks_limit=? WHERE role_id=?',
                       (vals["channels_limit"], vals["roles_limit"], vals["links_limit"], vals["webhooks_limit"], self.role_id))
        conn.commit()
        conn.close()
        await inter.response.send_message(f"✅ Limits for role `ID:{self.role_id}` updated!", ephemeral=True)


class EditRoleLimitsView(disnake.ui.View):
    def __init__(self, role_id, current_limits):
        super().__init__(timeout=120.0)
        self.role_id = role_id
        self.current_limits = current_limits

    @disnake.ui.button(label="Edit Limits", style=disnake.ButtonStyle.success, custom_id="adm_edit_role_btn", emoji="📝")
    async def btn_edit(self, button, inter):
        await inter.response.send_modal(modal=EditAdminRoleLimitsModal(self.role_id, self.current_limits))


# ================================================================================================ #
# USER Modals (analogous to role modals)
# ================================================================================================ #

class CreateAdminUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(label="User ID", placeholder="Insert ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True),
            disnake.ui.TextInput(label="Channels (Actions Mins)", placeholder="E.g., 5 10", custom_id="channels_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Roles (Actions Mins)", placeholder="E.g., 3 60", custom_id="roles_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Links/Spam (Actions Mins)", placeholder="E.g., 10 5", custom_id="links_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Webhooks (Actions Mins)", placeholder="E.g., 2 60", custom_id="webhooks_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
        ]
        super().__init__(title="Add Admin User", custom_id="adm_create_user_modal", components=components)

    def parse_limits(self, text):
        try:
            parts = text.strip().split()
            if len(parts) >= 2: return int(parts[0]), int(parts[1])
            elif len(parts) == 1: return int(parts[0]), 60
            return 0, 0
        except ValueError:
            return 0, 0

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Invalid ID format.", ephemeral=True)
            return
        user_id = int(uid)
        ch_l, ch_t = self.parse_limits(inter.text_values["channels_limits"])
        rl_l, rl_t = self.parse_limits(inter.text_values["roles_limits"])
        lnk_l, lnk_t = self.parse_limits(inter.text_values["links_limits"])
        wh_l, wh_t = self.parse_limits(inter.text_values["webhooks_limits"])
        database.save_custom_user_limits(user_id, inter.guild.id, channels_limit=ch_l, channels_time=ch_t, roles_limit=rl_l, roles_time=rl_t, links_limit=lnk_l, links_time=lnk_t, webhooks_limit=wh_l, webhooks_time=wh_t)
        await inter.response.send_message(f"✅ User <@{user_id}> added with custom limits!", ephemeral=True)


class RemoveAdminUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="User ID to remove", placeholder="Insert ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Remove Admin User", custom_id="adm_remove_user_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Invalid ID format.", ephemeral=True)
            return
        changes = database.delete_custom_user_limits(int(uid))
        if changes > 0:
            await inter.response.send_message(f"✅ User `ID:{uid}` removed from DB.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ User `ID:{uid}` not found in DB.", ephemeral=True)


class EditAdminUserLimitsModal(disnake.ui.Modal):
    def __init__(self, user_id, current_limits):
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(label="Channels Limit", value=str(current_limits["channels_limit"]), custom_id="channels_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Roles Limit", value=str(current_limits["roles_limit"]), custom_id="roles_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Links/Spam Limit", value=str(current_limits["links_limit"]), custom_id="links_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Webhooks Limit", value=str(current_limits["webhooks_limit"]), custom_id="webhooks_limit", style=disnake.TextInputStyle.short, required=True),
        ]
        super().__init__(title="Edit User Limits", custom_id=f"adm_edit_user_{user_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        try:
            vals = {k: int(inter.text_values[k]) for k in ["channels_limit", "roles_limit", "links_limit", "webhooks_limit"]}
        except ValueError:
            await inter.response.send_message("❌ All limits must be numbers.", ephemeral=True)
            return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE custom_user_limits SET channels_limit=?, roles_limit=?, links_limit=?, webhooks_limit=? WHERE user_id=?',
                       (vals["channels_limit"], vals["roles_limit"], vals["links_limit"], vals["webhooks_limit"], self.user_id))
        conn.commit()
        conn.close()
        await inter.response.send_message(f"✅ Limits for user `ID:{self.user_id}` updated!", ephemeral=True)


class EditUserLimitsView(disnake.ui.View):
    def __init__(self, user_id, current_limits):
        super().__init__(timeout=120.0)
        self.user_id = user_id
        self.current_limits = current_limits

    @disnake.ui.button(label="Edit Limits", style=disnake.ButtonStyle.success, custom_id="adm_edit_user_btn", emoji="📝")
    async def btn_edit(self, button, inter):
        await inter.response.send_modal(modal=EditAdminUserLimitsModal(self.user_id, self.current_limits))


# ================================================================================================ #
# Add/Remove Trusted User Modals
# ================================================================================================ #

class AddTrustedUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="User ID", placeholder="Insert ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Add Trusted User", custom_id="adm_add_trusted_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Invalid ID format.", ephemeral=True)
            return
        user_id = int(uid)
        bot = inter.bot
        if user_id not in bot.user_ids:
            bot.user_ids.append(user_id)
            database.add_tracked_user(user_id)
            await inter.response.send_message(f"✅ User <@{user_id}> added to trusted list.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ User <@{user_id}> is already in the list.", ephemeral=True)


class RemoveTrustedUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="User ID", placeholder="Insert ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Remove Trusted User", custom_id="adm_remove_trusted_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Invalid ID format.", ephemeral=True)
            return
        user_id = int(uid)
        bot = inter.bot
        if user_id in bot.user_ids:
            bot.user_ids.remove(user_id)
            database.remove_tracked_user(user_id)
            await inter.response.send_message(f"✅ User <@{user_id}> removed from trusted list.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ User <@{user_id}> is not in the list.", ephemeral=True)


# ================================================================================================ #
# Admin Panel View
# ================================================================================================ #

class AdminPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=300.0)

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.author.id == config.OWNER_ID or database.is_server_owner(inter.guild.id, inter.author.id):
            return True
        await inter.response.send_message("⛔ Only owners can use this panel.", ephemeral=True)
        return False

    # ---- Row 0: Admin ROLE ----
    @disnake.ui.button(label="Create Admin ROLE", style=disnake.ButtonStyle.success, custom_id="adm_create_role", emoji="➕", row=0)
    async def btn_create_role(self, button, inter):
        await inter.response.send_modal(modal=CreateAdminRoleModal())

    @disnake.ui.button(label="Edit Admin ROLE", style=disnake.ButtonStyle.primary, custom_id="adm_edit_role", emoji="✏️", row=0)
    async def btn_edit_role(self, button, inter):
        await inter.response.send_message("✍️ Provide the **Role ID** in this chat within 60 seconds.", ephemeral=True)
        def check(m): return m.author.id == inter.author.id and m.channel.id == inter.channel.id
        try:
            msg = await inter.bot.wait_for('message', check=check, timeout=60.0)
        except Exception:
            await inter.edit_original_response(content="⏳ Timeout.")
            return
        rid = msg.content.strip()
        try: await msg.delete()
        except Exception: pass
        if not rid.isdigit():
            await inter.edit_original_response(content="❌ Invalid ID format.")
            return
        role_id = int(rid)
        role = inter.guild.get_role(role_id)
        limits = database.get_custom_role_limits(role_id)
        # Auto-Doctor
        if limits is not None and not role:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM custom_role_limits WHERE role_id = ?', (role_id,))
            conn.commit(); conn.close()
            await inter.edit_original_response(content=f"❌ Role `ID:{role_id}` not found on server. Removed from DB. Recommended to recreate.")
            return
        elif limits is None and not role:
            await inter.edit_original_response(content=f"❌ Role `ID:{role_id}` is not registered and not found on server.")
            return
        elif limits is None and role:
            await inter.edit_original_response(content=f"❌ Role `@{role.name}` is not registered as an admin role.")
            return
        text = f"✅ Role `@{role.name}` found.\n**Limits:** Ch:{limits['channels_limit']} Rl:{limits['roles_limit']} Lnk:{limits['links_limit']} Wh:{limits['webhooks_limit']}"
        await inter.edit_original_response(content=text, view=EditRoleLimitsView(role_id, limits))

    @disnake.ui.button(label="Remove Admin ROLE", style=disnake.ButtonStyle.danger, custom_id="adm_remove_role", emoji="🗑️", row=0)
    async def btn_remove_role(self, button, inter):
        await inter.response.send_modal(modal=RemoveAdminRoleModal())

    # ---- Row 1: Admin USER ----
    @disnake.ui.button(label="Create Admin USER", style=disnake.ButtonStyle.success, custom_id="adm_create_user", emoji="➕", row=1)
    async def btn_create_user(self, button, inter):
        await inter.response.send_modal(modal=CreateAdminUserModal())

    @disnake.ui.button(label="Edit Admin USER", style=disnake.ButtonStyle.primary, custom_id="adm_edit_user", emoji="✏️", row=1)
    async def btn_edit_user(self, button, inter):
        await inter.response.send_message("✍️ Provide the **User ID** in this chat within 60 seconds.", ephemeral=True)
        def check(m): return m.author.id == inter.author.id and m.channel.id == inter.channel.id
        try:
            msg = await inter.bot.wait_for('message', check=check, timeout=60.0)
        except Exception:
            await inter.edit_original_response(content="⏳ Timeout.")
            return
        uid = msg.content.strip()
        try: await msg.delete()
        except Exception: pass
        if not uid.isdigit():
            await inter.edit_original_response(content="❌ Invalid ID format.")
            return
        user_id = int(uid)
        member = inter.guild.get_member(user_id)
        limits = database.get_custom_user_limits(user_id)
        # Auto-Doctor
        if limits is not None and not member:
            database.delete_custom_user_limits(user_id)
            await inter.edit_original_response(content=f"❌ User `ID:{user_id}` not found on server. Removed from DB. Recommended to re-add.")
            return
        elif limits is None and not member:
            await inter.edit_original_response(content=f"❌ User `ID:{user_id}` is not registered and not found on server.")
            return
        elif limits is None and member:
            await inter.edit_original_response(content=f"❌ User `@{member.display_name}` is not registered as an admin user.")
            return
        text = f"✅ User `@{member.display_name}` found.\n**Limits:** Ch:{limits['channels_limit']} Rl:{limits['roles_limit']} Lnk:{limits['links_limit']} Wh:{limits['webhooks_limit']}"
        await inter.edit_original_response(content=text, view=EditUserLimitsView(user_id, limits))

    @disnake.ui.button(label="Remove Admin USER", style=disnake.ButtonStyle.danger, custom_id="adm_remove_user", emoji="🗑️", row=1)
    async def btn_remove_user(self, button, inter):
        await inter.response.send_modal(modal=RemoveAdminUserModal())

    # ---- Row 2: Trusted Users ----
    @disnake.ui.button(label="Add hold User", style=disnake.ButtonStyle.success, custom_id="adm_add_trusted", emoji="👤", row=2)
    async def btn_add_trusted(self, button, inter):
        await inter.response.send_modal(modal=AddTrustedUserModal())

    @disnake.ui.button(label="Remove hold User", style=disnake.ButtonStyle.secondary, custom_id="adm_remove_trusted", emoji="🚫", row=2)
    async def btn_remove_trusted(self, button, inter):
        await inter.response.send_modal(modal=RemoveTrustedUserModal())

    # ---- Row 3: Stubs ----
    @disnake.ui.button(label="Remove Quarantine", style=disnake.ButtonStyle.secondary, custom_id="adm_remove_quarantine", emoji="🔓", row=3)
    async def btn_remove_quarantine(self, button, inter):
        await inter.response.send_message("🚧 **WIP...** This feature will be available soon.", ephemeral=True)

    @disnake.ui.button(label="Reset Limits", style=disnake.ButtonStyle.secondary, custom_id="adm_reset_limits", emoji="🔄", row=3)
    async def btn_reset_limits(self, button, inter):
        await inter.response.send_message("🚧 **WIP...** This feature will be available soon.", ephemeral=True)


def setup(bot):
    pass
