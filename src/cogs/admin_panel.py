import disnake
from src import database
import config


# ================================================================================================ #
# ROLE Modals (moved from dev_panel.py)
# ================================================================================================ #

class CreateAdminRoleModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(label="Назва ролі", placeholder="Наприклад: DVP або AI", custom_id="role_name", style=disnake.TextInputStyle.short, max_length=100, required=True),
            disnake.ui.TextInput(label="Канали (Дій Хвилин)", placeholder="Наприклад: 5 10", custom_id="channels_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Ролі (Дій Хвилин)", placeholder="Наприклад: 3 60", custom_id="roles_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Лінки та Спам (Дій Хвилин)", placeholder="Наприклад: 10 5", custom_id="links_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Вебхуки (Дій Хвилин)", placeholder="Наприклад: 2 60", custom_id="webhooks_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
        ]
        super().__init__(title="Створити Адмін Роль", custom_id="adm_create_role_modal", components=components)

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
            await inter.edit_original_response(f"✅ Роль {role.mention} створено з кастомними лімітами!")
        except Exception as e:
            await inter.edit_original_response(f"❌ Помилка: {e}")


class RemoveAdminRoleModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="ID ролі для видалення", placeholder="Вставте ID...", custom_id="role_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Видалити Адмін Роль", custom_id="adm_remove_role_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        rid = inter.text_values["role_id"]
        if not rid.isdigit():
            await inter.response.send_message("❌ Невірний формат ID.", ephemeral=True)
            return
        role_id = int(rid)
        role = inter.guild.get_role(role_id)
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM custom_role_limits WHERE role_id = ?', (role_id,))
        changes = cursor.rowcount
        conn.commit()
        conn.close()
        msg = f"✅ Роль `ID:{role_id}` видалено з бази." if changes > 0 else f"⚠️ Ролі `ID:{role_id}` не знайдено в базі."
        if role:
            try:
                await role.delete(reason="Видалено через Admin Panel")
                msg += f"\n✅ Роль `@{role.name}` видалено з сервера."
            except Exception as e:
                msg += f"\n❌ Помилка видалення з сервера: {e}"
        else:
            msg += "\n⚠️ На сервері такої ролі вже не існувало."
        await inter.response.send_message(msg, ephemeral=True)


class EditAdminRoleLimitsModal(disnake.ui.Modal):
    def __init__(self, role_id, current_limits):
        self.role_id = role_id
        components = [
            disnake.ui.TextInput(label="Ліміт на канали", value=str(current_limits["channels_limit"]), custom_id="channels_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на ролі", value=str(current_limits["roles_limit"]), custom_id="roles_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на спам посиланнями", value=str(current_limits["links_limit"]), custom_id="links_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на вебхуки", value=str(current_limits["webhooks_limit"]), custom_id="webhooks_limit", style=disnake.TextInputStyle.short, required=True),
        ]
        super().__init__(title="Змінити ліміти ролі", custom_id=f"adm_edit_role_{role_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        try:
            vals = {k: int(inter.text_values[k]) for k in ["channels_limit", "roles_limit", "links_limit", "webhooks_limit"]}
        except ValueError:
            await inter.response.send_message("❌ Усі ліміти мають бути числами.", ephemeral=True)
            return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE custom_role_limits SET channels_limit=?, roles_limit=?, links_limit=?, webhooks_limit=? WHERE role_id=?',
                       (vals["channels_limit"], vals["roles_limit"], vals["links_limit"], vals["webhooks_limit"], self.role_id))
        conn.commit()
        conn.close()
        await inter.response.send_message(f"✅ Ліміти для ролі `ID:{self.role_id}` оновлено!", ephemeral=True)


class EditRoleLimitsView(disnake.ui.View):
    def __init__(self, role_id, current_limits):
        super().__init__(timeout=120.0)
        self.role_id = role_id
        self.current_limits = current_limits

    @disnake.ui.button(label="Змінити ліміти", style=disnake.ButtonStyle.success, custom_id="adm_edit_role_btn", emoji="📝")
    async def btn_edit(self, button, inter):
        await inter.response.send_modal(modal=EditAdminRoleLimitsModal(self.role_id, self.current_limits))


# ================================================================================================ #
# USER Modals (analogous to role modals)
# ================================================================================================ #

class CreateAdminUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(label="ID юзера", placeholder="Вставте ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True),
            disnake.ui.TextInput(label="Канали (Дій Хвилин)", placeholder="Наприклад: 5 10", custom_id="channels_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Ролі (Дій Хвилин)", placeholder="Наприклад: 3 60", custom_id="roles_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Лінки та Спам (Дій Хвилин)", placeholder="Наприклад: 10 5", custom_id="links_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
            disnake.ui.TextInput(label="Вебхуки (Дій Хвилин)", placeholder="Наприклад: 2 60", custom_id="webhooks_limits", style=disnake.TextInputStyle.short, max_length=20, required=True),
        ]
        super().__init__(title="Додати Адмін Юзера", custom_id="adm_create_user_modal", components=components)

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
            await inter.response.send_message("❌ Невірний формат ID.", ephemeral=True)
            return
        user_id = int(uid)
        ch_l, ch_t = self.parse_limits(inter.text_values["channels_limits"])
        rl_l, rl_t = self.parse_limits(inter.text_values["roles_limits"])
        lnk_l, lnk_t = self.parse_limits(inter.text_values["links_limits"])
        wh_l, wh_t = self.parse_limits(inter.text_values["webhooks_limits"])
        database.save_custom_user_limits(user_id, inter.guild.id, channels_limit=ch_l, channels_time=ch_t, roles_limit=rl_l, roles_time=rl_t, links_limit=lnk_l, links_time=lnk_t, webhooks_limit=wh_l, webhooks_time=wh_t)
        await inter.response.send_message(f"✅ Юзера <@{user_id}> додано з кастомними лімітами!", ephemeral=True)


class RemoveAdminUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="ID юзера для видалення", placeholder="Вставте ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Видалити Адмін Юзера", custom_id="adm_remove_user_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Невірний формат ID.", ephemeral=True)
            return
        changes = database.delete_custom_user_limits(int(uid))
        if changes > 0:
            await inter.response.send_message(f"✅ Юзера `ID:{uid}` видалено з бази.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ Юзера `ID:{uid}` не знайдено в базі.", ephemeral=True)


class EditAdminUserLimitsModal(disnake.ui.Modal):
    def __init__(self, user_id, current_limits):
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(label="Ліміт на канали", value=str(current_limits["channels_limit"]), custom_id="channels_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на ролі", value=str(current_limits["roles_limit"]), custom_id="roles_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на спам посиланнями", value=str(current_limits["links_limit"]), custom_id="links_limit", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Ліміт на вебхуки", value=str(current_limits["webhooks_limit"]), custom_id="webhooks_limit", style=disnake.TextInputStyle.short, required=True),
        ]
        super().__init__(title="Змінити ліміти юзера", custom_id=f"adm_edit_user_{user_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        try:
            vals = {k: int(inter.text_values[k]) for k in ["channels_limit", "roles_limit", "links_limit", "webhooks_limit"]}
        except ValueError:
            await inter.response.send_message("❌ Усі ліміти мають бути числами.", ephemeral=True)
            return
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE custom_user_limits SET channels_limit=?, roles_limit=?, links_limit=?, webhooks_limit=? WHERE user_id=?',
                       (vals["channels_limit"], vals["roles_limit"], vals["links_limit"], vals["webhooks_limit"], self.user_id))
        conn.commit()
        conn.close()
        await inter.response.send_message(f"✅ Ліміти для юзера `ID:{self.user_id}` оновлено!", ephemeral=True)


class EditUserLimitsView(disnake.ui.View):
    def __init__(self, user_id, current_limits):
        super().__init__(timeout=120.0)
        self.user_id = user_id
        self.current_limits = current_limits

    @disnake.ui.button(label="Змінити ліміти", style=disnake.ButtonStyle.success, custom_id="adm_edit_user_btn", emoji="📝")
    async def btn_edit(self, button, inter):
        await inter.response.send_modal(modal=EditAdminUserLimitsModal(self.user_id, self.current_limits))


# ================================================================================================ #
# Add/Remove Trusted User Modals
# ================================================================================================ #

class AddTrustedUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="ID юзера", placeholder="Вставте ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Додати довіреного юзера", custom_id="adm_add_trusted_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Невірний формат ID.", ephemeral=True)
            return
        user_id = int(uid)
        bot = inter.bot
        if user_id not in bot.user_ids:
            bot.user_ids.append(user_id)
            database.add_tracked_user(user_id)
            await inter.response.send_message(f"✅ Юзера <@{user_id}> додано до списку довірених.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ Юзер <@{user_id}> вже є у списку.", ephemeral=True)


class RemoveTrustedUserModal(disnake.ui.Modal):
    def __init__(self):
        components = [disnake.ui.TextInput(label="ID юзера", placeholder="Вставте ID...", custom_id="user_id", style=disnake.TextInputStyle.short, min_length=17, max_length=21, required=True)]
        super().__init__(title="Видалити довіреного юзера", custom_id="adm_remove_trusted_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        uid = inter.text_values["user_id"]
        if not uid.isdigit():
            await inter.response.send_message("❌ Невірний формат ID.", ephemeral=True)
            return
        user_id = int(uid)
        bot = inter.bot
        if user_id in bot.user_ids:
            bot.user_ids.remove(user_id)
            database.remove_tracked_user(user_id)
            await inter.response.send_message(f"✅ Юзера <@{user_id}> видалено зі списку довірених.", ephemeral=True)
        else:
            await inter.response.send_message(f"⚠️ Юзера <@{user_id}> немає у списку.", ephemeral=True)


# ================================================================================================ #
# Admin Panel View
# ================================================================================================ #

class AdminPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=300.0)

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.author.id == config.OWNER_ID or database.is_server_owner(inter.guild.id, inter.author.id):
            return True
        await inter.response.send_message("⛔ Лише власники можуть користуватися цією панеллю.", ephemeral=True)
        return False

    # ---- Row 0: Admin ROLE ----
    @disnake.ui.button(label="Create Admin ROLE", style=disnake.ButtonStyle.success, custom_id="adm_create_role", emoji="➕", row=0)
    async def btn_create_role(self, button, inter):
        await inter.response.send_modal(modal=CreateAdminRoleModal())

    @disnake.ui.button(label="Edit Admin ROLE", style=disnake.ButtonStyle.primary, custom_id="adm_edit_role", emoji="✏️", row=0)
    async def btn_edit_role(self, button, inter):
        await inter.response.send_message("✍️ Вкажіть **ID ролі** в цей чат протягом 60 секунд.", ephemeral=True)
        def check(m): return m.author.id == inter.author.id and m.channel.id == inter.channel.id
        try:
            msg = await inter.bot.wait_for('message', check=check, timeout=60.0)
        except Exception:
            await inter.edit_original_response(content="⏳ Час очікування вичерпано.")
            return
        rid = msg.content.strip()
        try: await msg.delete()
        except Exception: pass
        if not rid.isdigit():
            await inter.edit_original_response(content="❌ Невірний формат ID.")
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
            await inter.edit_original_response(content=f"❌ Роль `ID:{role_id}` не знайдено на сервері. Видалено з бази. Рекомендую створити заново.")
            return
        elif limits is None and not role:
            await inter.edit_original_response(content=f"❌ Ролі `ID:{role_id}` не зареєстровано і не знайдено на сервері.")
            return
        elif limits is None and role:
            await inter.edit_original_response(content=f"❌ Роль `@{role.name}` не зареєстрована як адмін-роль.")
            return
        text = f"✅ Роль `@{role.name}` знайдено.\n**Ліміти:** Ch:{limits['channels_limit']} Rl:{limits['roles_limit']} Lnk:{limits['links_limit']} Wh:{limits['webhooks_limit']}"
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
        await inter.response.send_message("✍️ Вкажіть **ID юзера** в цей чат протягом 60 секунд.", ephemeral=True)
        def check(m): return m.author.id == inter.author.id and m.channel.id == inter.channel.id
        try:
            msg = await inter.bot.wait_for('message', check=check, timeout=60.0)
        except Exception:
            await inter.edit_original_response(content="⏳ Час очікування вичерпано.")
            return
        uid = msg.content.strip()
        try: await msg.delete()
        except Exception: pass
        if not uid.isdigit():
            await inter.edit_original_response(content="❌ Невірний формат ID.")
            return
        user_id = int(uid)
        member = inter.guild.get_member(user_id)
        limits = database.get_custom_user_limits(user_id)
        # Auto-Doctor
        if limits is not None and not member:
            database.delete_custom_user_limits(user_id)
            await inter.edit_original_response(content=f"❌ Юзера `ID:{user_id}` не знайдено на сервері. Видалено з бази. Рекомендую додати заново.")
            return
        elif limits is None and not member:
            await inter.edit_original_response(content=f"❌ Юзера `ID:{user_id}` не зареєстровано і не знайдено на сервері.")
            return
        elif limits is None and member:
            await inter.edit_original_response(content=f"❌ Юзер `@{member.display_name}` не зареєстрований як адмін-юзер.")
            return
        text = f"✅ Юзер `@{member.display_name}` знайдено.\n**Ліміти:** Ch:{limits['channels_limit']} Rl:{limits['roles_limit']} Lnk:{limits['links_limit']} Wh:{limits['webhooks_limit']}"
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
        await inter.response.send_message("🚧 **В розробці...** Ця функція буде доступна найближчим часом.", ephemeral=True)

    @disnake.ui.button(label="Reset Limits", style=disnake.ButtonStyle.secondary, custom_id="adm_reset_limits", emoji="🔄", row=3)
    async def btn_reset_limits(self, button, inter):
        await inter.response.send_message("🚧 **В розробці...** Ця функція буде доступна найближчим часом.", ephemeral=True)


def setup(bot):
    pass
