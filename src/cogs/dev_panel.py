import disnake
from src import database
import asyncio

class CompareModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID ролі Server Booster",
                placeholder="Вставте ID...",
                custom_id="server_booster_id",
                style=disnake.TextInputStyle.short,
                min_length=17,
                max_length=21,
                required=False
            )
        ]
        super().__init__(
            title="Ручне додавання ролей",
            custom_id="dev_compare_modal",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        booster_str = inter.text_values["server_booster_id"]
        
        updates = {}
        if booster_str.isdigit():
            updates['server_booster_id'] = int(booster_str)
            
        try:
            if updates:
                database.save_guild_roles(inter.guild.id, **updates)
                await inter.response.send_message("✅ Ролі успішно збережено в базу даних.", ephemeral=True)
            else:
                await inter.response.send_message("⚠️ Жодних валідних ID не знайдено.", ephemeral=True)
        except OverflowError:
            await inter.response.send_message("❌ Помилка: Введено занадто велике число (ID невалідний).", ephemeral=True)





class AddOwnerModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID нового власника",
                placeholder="Вставте ID...",
                custom_id="owner_id",
                style=disnake.TextInputStyle.short,
                min_length=17,
                max_length=21,
                required=True
            )
        ]
        super().__init__(title="Додати власника сервера", custom_id="add_owner_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        owner_id = inter.text_values["owner_id"]
        if owner_id.isdigit():
            database.add_server_owner(inter.guild.id, int(owner_id))
            await inter.response.send_message(f"✅ Власника <@{owner_id}> успішно додано!", ephemeral=True)
        else:
            await inter.response.send_message("❌ Невірний ID.", ephemeral=True)

class DelOwnerModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID власника для видалення",
                placeholder="Вставте ID...",
                custom_id="owner_id",
                style=disnake.TextInputStyle.short,
                min_length=17,
                max_length=21,
                required=True
            )
        ]
        super().__init__(title="Видалити власника сервера", custom_id="del_owner_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        owner_id = inter.text_values["owner_id"]
        if owner_id.isdigit():
            database.remove_server_owner(inter.guild.id, int(owner_id))
            await inter.response.send_message(f"✅ Власника <@{owner_id}> успішно видалено!", ephemeral=True)
        else:
            await inter.response.send_message("❌ Невірний ID.", ephemeral=True)

class FixSkipView(disnake.ui.View):
    def __init__(self, missing_channels, missing_roles, missing_custom_roles, missing_custom_users=None):
        super().__init__(timeout=120.0)
        self.missing_channels = missing_channels
        self.missing_roles = missing_roles
        self.missing_custom_roles = missing_custom_roles
        self.missing_custom_users = missing_custom_users or []

    @disnake.ui.button(label="Fix", style=disnake.ButtonStyle.success, custom_id="dev_doctor_fix", emoji="🛠️")
    async def btn_fix(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        report = "Починаю процес виправлення...\n"
        
        # 1. Fix missing log channels
        if self.missing_channels:
            config = database.get_guild_config(guild.id)
            if config:
                cat_id, _ = config
                category = guild.get_channel(cat_id)
                if category:
                    created_channels = {}
                    for name in self.missing_channels:
                        try:
                            ch = await guild.create_text_channel(name=name, category=category)
                            created_channels[f"{name}_id"] = ch.id
                            report += f"✅ Канал `#{name}` створено.\n"
                        except Exception as e:
                            report += f"⚠️ Помилка створення каналу `#{name}`: {e}\n"
                    
                    if created_channels:
                        database.save_guild_log_channels(guild.id, **created_channels)
                        report += "💾 ID нових каналів збережено.\n"
                else:
                    report += "❌ Категорію не знайдено, не можу створити канали.\n"
                    
        # 2. Fix missing quarantine roles
        if self.missing_roles:
            created_roles = {}
            for name in self.missing_roles:
                try:
                    role = await guild.create_role(name=name, reason="AntiNuke Doctor Fix")
                    created_roles[f"{name}_id"] = role.id
                    report += f"✅ Роль `@{name}` створено.\n"
                    
                    max_pos = guild.me.top_role.position - 1
                    if max_pos > 0:
                        try:
                            await role.edit(position=max_pos)
                        except Exception:
                            pass
                except Exception as e:
                    report += f"⚠️ Помилка створення ролі `@{name}`: {e}\n"
            
            if created_roles:
                database.save_guild_roles(guild.id, **created_roles)
                report += "💾 ID нових ролей збережено.\n"
                
        # 3. Fix missing custom roles (delete from DB)
        if self.missing_custom_roles:
            conn = database.get_connection()
            cursor = conn.cursor()
            for role_id in self.missing_custom_roles:
                cursor.execute('DELETE FROM custom_role_limits WHERE role_id = ?', (role_id,))
                report += f"✅ Запис про видалену кастомну роль `ID:{role_id}` очищено з бази.\n"
            conn.commit()
            conn.close()
            
        # 4. Fix missing custom users (delete from DB)
        if self.missing_custom_users:
            conn = database.get_connection()
            cursor = conn.cursor()
            for user_id in self.missing_custom_users:
                cursor.execute('DELETE FROM custom_user_limits WHERE user_id = ?', (user_id,))
                report += f"✅ Запис про видаленого кастомного юзера `ID:{user_id}` очищено з бази.\n"
            conn.commit()
            conn.close()
            
        await inter.edit_original_response(content=report, view=None)

    @disnake.ui.button(label="Skip", style=disnake.ButtonStyle.secondary, custom_id="dev_doctor_skip", emoji="⏭️")
    async def btn_skip(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(content="Фікс пропущено.", view=None)





class DevPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=300.0)

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        import config
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("❌ Лише головний власник бота може користуватися цією панеллю.", ephemeral=True)
            return False
        return True


    @disnake.ui.button(label="Pull", style=disnake.ButtonStyle.success, custom_id="dev_pull", emoji="📥", row=0)
    async def btn_pull(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        
        # 1. Get Category ID
        config = database.get_guild_config(guild.id)
        if not config:
            await inter.edit_original_response(content="❌ Категорія налаштувань не знайдена. Виконайте `/set` спочатку.")
            return
            
        cat_id, _ = config
        category = guild.get_channel(cat_id)
        if not category or not isinstance(category, disnake.CategoryChannel):
            await inter.edit_original_response(content="❌ Категорія налаштувань була видалена або недоступна.")
            return

        report = "Починаю Pull процес...\n"
        await inter.edit_original_response(content=report)

        # 2. Create Channels
        channel_names = [
            "channel_create", "channel_delete", "channel_update", 
            "links_spam", "webhooks", "bot_joins", 
            "message_edit_delete", "voice_move", "role_updates", "bans"
        ]
        
        created_channels = {}
        for name in channel_names:
            try:
                ch = await guild.create_text_channel(name=name, category=category)
                created_channels[f"{name}_id"] = ch.id
                report += f"✅ Канал `#{name}` створено.\n"
            except Exception as e:
                report += f"⚠️ Помилка створення каналу `#{name}`: {e}\n"
        
        if created_channels:
            database.save_guild_log_channels(guild.id, **created_channels)
            report += "💾 ID каналів збережено в базу.\n"

        # Update progress
        await inter.edit_original_response(content=report)

        # 3. Create Roles
        role_names = ["quarantine", "quarantine_alt"]
        created_roles = {}
        
        for name in role_names:
            try:
                role = await guild.create_role(name=name, reason="AntiNuke Dev Pull")
                created_roles[f"{name}_id"] = role.id
                report += f"✅ Роль `@{name}` створено.\n"
                
                # Try to move role up
                # We can't move higher than bot's top role
                max_pos = guild.me.top_role.position - 1
                if max_pos > 0:
                    try:
                        await role.edit(position=max_pos)
                    except Exception:
                        pass
            except Exception as e:
                report += f"⚠️ Помилка створення ролі `@{name}`: {e}\n"

        if created_roles:
            database.save_guild_roles(guild.id, **created_roles)
            report += "💾 ID ролей збережено в базу.\n"
            report += "\n⚠️ **УВАГА:** Не забудьте самостійно налаштувати права для створених ролей у звичайних каналах!"

        await inter.edit_original_response(content=report)


    @disnake.ui.button(label="Compare", style=disnake.ButtonStyle.primary, custom_id="dev_compare", emoji="⚖️", row=0)
    async def btn_compare(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(modal=CompareModal())


    @disnake.ui.button(label="Doctor", style=disnake.ButtonStyle.secondary, custom_id="dev_doctor", emoji="🩺", row=0)
    async def btn_doctor(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        import config
        
        embed = disnake.Embed(title="🩺 AntiNuke System Doctor", color=disnake.Color.blue())
        
        missing_channels = []
        missing_roles = []
        missing_custom_roles = []
        missing_custom_users = []
        
        # Channels
        log_channels = database.get_guild_log_channels(guild.id)
        channels_status = ""
        if log_channels:
            keys = [
                "channel_create", "channel_delete", "channel_update", "links_spam", 
                "webhooks", "bot_joins", "message_edit_delete", "voice_move", 
                "role_updates", "bans"
            ]
            for i, key in enumerate(keys):
                ch_id = log_channels[i+1]
                if ch_id:
                    ch = guild.get_channel(ch_id)
                    if ch:
                        channels_status += f"✅ `{key}` — {ch.mention}\n"
                    else:
                        channels_status += f"❌ `{key}` — КАНАЛ НЕ ЗНАЙДЕНО (Видалено?)\n"
                        missing_channels.append(key)
                else:
                    channels_status += f"⚠️ `{key}` — Не налаштовано\n"
        else:
            channels_status = "❌ База даних пуста (Зробіть Pull)."
            
        embed.add_field(name="Log Channels", value=channels_status, inline=False)
        
        # Roles
        roles = database.get_guild_roles(guild.id)
        roles_status = ""
        
        # Add AI role status
        ai_role = guild.get_role(config.AI_ROLE_ID)
        if ai_role:
            roles_status += f"✅ `ai` — {ai_role.mention}\n"
        else:
            roles_status += f"❌ `ai` — РОЛЬ НЕ ЗНАЙДЕНО (Невірно вказано ID в config.py?)\n"
            
        if roles:
            keys = ["quarantine", "quarantine_alt", "server_booster"]
            for i, key in enumerate(keys):
                try:
                    role_id = roles[i+1]
                except IndexError:
                    role_id = None
                if role_id:
                    role = guild.get_role(role_id)
                    if role:
                        roles_status += f"✅ `{key}` — {role.mention}\n"
                    else:
                        roles_status += f"❌ `{key}` — РОЛЬ НЕ ЗНАЙДЕНО (Видалено?)\n"
                        if key in ["quarantine", "quarantine_alt"]:
                            missing_roles.append(key)
                else:
                    roles_status += f"⚠️ `{key}` — Не налаштовано\n"
        else:
            roles_status += "❌ База даних пуста (Зробіть Pull/Compare)."
            
        custom_roles = database.get_all_custom_roles(guild.id)
        if custom_roles:
            roles_status += "\n **Кастомні Адмін Ролі:** \n "
            for cr_id in custom_roles:
                cr = guild.get_role(cr_id)
                if cr:
                    limits = database.get_custom_role_limits(cr_id)
                    roles_status += f" ✅ {cr.mention} (Chanels: {limits['channels_limit']} Roles: {limits['roles_limit']} Links: {limits['links_limit']} Webhook: {limits['webhooks_limit']})\n"
                else:
                    roles_status += f"❌ `ID:{cr_id}` (Видалено?)\n"
                    missing_custom_roles.append(cr_id)
            
        embed.add_field(name="Roles", value=roles_status, inline=False)
        
        # Custom Users
        custom_users = database.get_all_custom_users(guild.id)
        users_status = ""
        if custom_users:
            users_status += "**Кастомні Адміни (Юзери):** \n "
            for cu_id in custom_users:
                member = guild.get_member(cu_id)
                if member:
                    limits = database.get_custom_user_limits(cu_id)
                    users_status += f" ✅ {member.mention} (Chanels: {limits['channels_limit']} Roles: {limits['roles_limit']} Links: {limits['links_limit']} Webhook: {limits['webhooks_limit']})\n"
                else:
                    users_status += f"❌ `ID:{cu_id}` (Вийшов з сервера?)\n"
                    missing_custom_users.append(cu_id)
            embed.add_field(name="Users", value=users_status, inline=False)
        
        # Owners
        owners = database.get_server_owners(guild.id)
        owners_str = f"👑 **Головний Власник:** \n <@{config.OWNER_ID}>\n"
        if owners:
            owners_str += "**Додаткові власники:**\n"
            for o in owners:
                owners_str += f"✅ <@{o}>\n"
        else:
            owners_str += "*Додаткових власників немає.*\n"
            
        embed.add_field(name="Owners", value=owners_str, inline=False)
        
        await inter.edit_original_response(embed=embed)
        
        if missing_channels or missing_roles or missing_custom_roles or missing_custom_users:
            view = FixSkipView(missing_channels, missing_roles, missing_custom_roles, missing_custom_users)
            await inter.followup.send("⚠️ **Увага:** Знайдено відсутні канали/ролі/юзерів. Хочете їх пофіксити?", view=view, ephemeral=True)

    @disnake.ui.button(label="Owner", style=disnake.ButtonStyle.primary, custom_id="dev_add_owner", emoji="➕", row=1)
    async def btn_add_owner(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(modal=AddOwnerModal())

    @disnake.ui.button(label="Del Owner", style=disnake.ButtonStyle.secondary, custom_id="dev_del_owner", emoji="➖", row=1)
    async def btn_del_owner(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(modal=DelOwnerModal())




def setup(bot):
    # Цей файл містить лише UI компоненти (Views/Modals), але оскільки він лежить у src/cogs/,
    # лоадер намагається його завантажити як розширення. Тому додаємо порожню функцію setup.
    pass


