import disnake


def dashboard_main():
    """Main dashboard embed for the Tuner channel."""
    embed = disnake.Embed(
        title="⚙️ AntiNuke — Control Panel",
        description=(
            "Глобальне налаштування і швидкий доступ до бота.\n"
            "Натисніть кнопку нижче для доступу до налаштувань."
        ),
        color=disnake.Color.dark_theme(),
    )
    embed.add_field(
        name="🔑 Dev",
        value="Повний контроль (тільки для розробника)",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Adm",
        value="Управління адмін-списком та відстеженням",
        inline=False,
    )
    embed.add_field(
        name="👤 Pre-Adm",
        value="Частковий доступ до функцій антикраша",
        inline=False,
    )
    embed.set_footer(text="AntiNuke Configuration System")
    return embed
