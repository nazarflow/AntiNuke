import disnake
from disnake.ext import commands
import config
from src import database
from src.embeds.dashboard import dashboard_main


from src.cogs.dev_panel import DevPanelView

# ================================================================================================ #
# Persistent Dashboard View (lives forever, survives bot restarts)
# ================================================================================================ #

class DashboardView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Dev", style=disnake.ButtonStyle.danger, custom_id="dash_dev", emoji="🔑")
    async def btn_dev(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("⛔ Доступ лише для розробника.", ephemeral=True)
            return
        await inter.response.send_message("Відкриваю Dev Panel...", view=DevPanelView(), ephemeral=True)

    @disnake.ui.button(label="Adm", style=disnake.ButtonStyle.primary, custom_id="dash_adm", emoji="🛡️")
    async def btn_adm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id != config.OWNER_ID and not database.is_server_owner(inter.guild.id, inter.author.id):
            await inter.response.send_message("⛔ Доступ лише для власників.", ephemeral=True)
            return
        from src.cogs.admin_panel import AdminPanelView
        await inter.response.send_message("🛡️ **Admin Panel**", view=AdminPanelView(), ephemeral=True)

    @disnake.ui.button(label="Pre-Adm", style=disnake.ButtonStyle.secondary, custom_id="dash_preadm", emoji="👤")
    async def btn_preadm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("👤 **Pre-Admin Panel** — В розробці...", ephemeral=True)


# ================================================================================================ #
# Modal: Manual channel & category ID input
# ================================================================================================ #

class ChannelInputModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID категорії",
                placeholder="Вставте ID категорії...",
                custom_id="category_id_input",
                style=disnake.TextInputStyle.short,
                min_length=17,
                max_length=21,
            ),
            disnake.ui.TextInput(
                label="ID каналу",
                placeholder="Вставте ID текстового каналу...",
                custom_id="channel_id_input",
                style=disnake.TextInputStyle.short,
                min_length=17,
                max_length=21,
            ),
        ]
        super().__init__(
            title="Ручне налаштування каналу",
            custom_id="setup_channel_modal",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        cat_id_str = inter.text_values["category_id_input"]
        ch_id_str = inter.text_values["channel_id_input"]

        try:
            cat_id = int(cat_id_str)
            ch_id = int(ch_id_str)
        except ValueError:
            await inter.response.send_message("❌ Невірний формат ID. Мають бути тільки цифри.", ephemeral=True)
            return

        category = inter.guild.get_channel(cat_id)
        channel = inter.guild.get_channel(ch_id)

        if not category or not isinstance(category, disnake.CategoryChannel):
            await inter.response.send_message("❌ Категорію з таким ID не знайдено.", ephemeral=True)
            return
        if not channel or not isinstance(channel, disnake.TextChannel):
            await inter.response.send_message("❌ Текстовий канал з таким ID не знайдено.", ephemeral=True)
            return

        # Save to database
        database.save_guild_config(inter.guild.id, cat_id, ch_id)

        # Send dashboard embed to the channel
        await channel.send(embed=dashboard_main(), view=DashboardView())

        await inter.response.send_message(
            f"✅ Налаштування збережено!\n"
            f"Категорія: `{category.name}`\n"
            f"Канал: {channel.mention}",
            ephemeral=True,
        )


# ================================================================================================ #
# Step 2 View: Create channel automatically or enter manually
# ================================================================================================ #

class Step2View(disnake.ui.View):
    def __init__(self, original_message):
        super().__init__(timeout=60.0)
        self.original_message = original_message

    async def on_timeout(self):
        try:
            await self.original_message.delete()
        except Exception:
            pass

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("⛔ Ви не маєте доступу.", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Yes", style=disnake.ButtonStyle.success, custom_id="setup_step2_yes")
    async def btn_yes(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.defer(ephemeral=True)

        guild = inter.guild
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            guild.me: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Give admin roles access
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            category = await guild.create_category(
                name="AntiNuke Configuration",
                overwrites=overwrites,
                position=len(guild.categories),
            )
            channel = await guild.create_text_channel(
                name="Tuner",
                category=category,
            )

            # Save to database
            database.save_guild_config(guild.id, category.id, channel.id)

            # Send dashboard embed
            await channel.send(embed=dashboard_main(), view=DashboardView())

            await inter.edit_original_response(
                content=f"✅ Успішно створено! Канал: {channel.mention}", view=None
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Сталася помилка при створенні: {e}", view=None
            )

    @disnake.ui.button(label="No", style=disnake.ButtonStyle.secondary, custom_id="setup_step2_no")
    async def btn_no(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.send_modal(modal=ChannelInputModal())
        try:
            await self.original_message.delete()
        except Exception:
            pass


# ================================================================================================ #
# Step 1 View: Ask owner to give AI role first
# ================================================================================================ #

class Step1View(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.message = None

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except Exception:
                pass

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("⛔ Ви не маєте доступу.", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Done", style=disnake.ButtonStyle.success, custom_id="setup_step1_done")
    async def btn_done(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        view = Step2View(original_message=self.message)
        await inter.response.edit_message(
            content="Створити текстовий канал і категорію для автоматичного налаштування?",
            view=view,
        )


# ================================================================================================ #
# Reset Confirmation View
# ================================================================================================ #

class ResetConfirmView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.message = None

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except Exception:
                pass

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("⛔ Ви не маєте доступу.", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Скинути", style=disnake.ButtonStyle.danger, custom_id="setup_reset_yes")
    async def btn_reset(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.defer(ephemeral=True)

        guild_config = database.get_guild_config(inter.guild.id)
        
        # Respond BEFORE deleting, because deleting the channel invalidates the interaction webhook
        await inter.edit_original_response(
            content="✅ Запис у базі даних очищено. Видаляю канали...\nТепер можете знову використати `/set` в іншому каналі.", 
            view=None
        )

        if guild_config:
            cat_id, ch_id = guild_config
            
            # Delete channel
            channel = inter.guild.get_channel(ch_id)
            if channel:
                try:
                    await channel.delete(reason="Скидання налаштувань AntiNuke")
                except Exception:
                    pass

            # Delete category and all its child channels
            category = inter.guild.get_channel(cat_id)
            if category and isinstance(category, disnake.CategoryChannel):
                for ch in category.channels:
                    try:
                        await ch.delete(reason="Скидання налаштувань AntiNuke")
                    except Exception:
                        pass
                try:
                    await category.delete(reason="Скидання налаштувань AntiNuke")
                except Exception:
                    pass

        database.delete_guild_config(inter.guild.id)

    @disnake.ui.button(label="Відміна", style=disnake.ButtonStyle.secondary, custom_id="setup_reset_no")
    async def btn_cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.edit_message(content="Операцію скасовано.", view=None)


# ================================================================================================ #
# Setup Wizard Cog
# ================================================================================================ #

class SetupWizard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistent_views_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        # Register persistent view so buttons survive bot restarts
        # This must be done inside an async event loop (on_ready)
        if not self.persistent_views_added:
            self.bot.add_view(DashboardView())
            self.persistent_views_added = True

    @commands.slash_command(name="set", description="Почати процес налаштування AntiNuke (Тільки для власника)")
    async def cmd_set(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id != config.OWNER_ID:
            await inter.response.send_message("⛔ Ви не маєте доступу до цієї команди.", ephemeral=True)
            return

        # Check if already configured
        guild_config = database.get_guild_config(inter.guild.id)
        if guild_config:
            cat_id, ch_id = guild_config
            channel = inter.guild.get_channel(ch_id)

            if channel:
                view = ResetConfirmView()
                await inter.response.send_message(
                    f"⚠️ Канал налаштування вже існує: {channel.mention}\n"
                    f"Бажаєте скинути налаштування?",
                    view=view,
                    ephemeral=True,
                )
                view.message = await inter.original_response()
                return
            else:
                # Channel was deleted externally, clean up the DB record
                database.delete_guild_config(inter.guild.id)

        # Start fresh setup
        view = Step1View()
        await inter.response.send_message(
            content="Привіт, перед початком налаштування, дай мені роль AI",
            view=view,
            ephemeral=True,
        )
        view.message = await inter.original_response()


def setup(bot):
    bot.add_cog(SetupWizard(bot))
