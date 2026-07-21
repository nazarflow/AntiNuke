import disnake


def dashboard_main():
    """Main dashboard embed for the Tuner channel."""
    embed = disnake.Embed(
        title="⚙️ AntiNuke — Control Panel",
        description=(
            "Global settings and quick access to the bot.\n"
            "Click the button below to access settings."
        ),
        color=disnake.Color.dark_theme(),
    )
    embed.add_field(
        name="🔑 Dev",
        value="Full control (Developer only)",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Adm",
        value="Admin list and tracking management",
        inline=False,
    )
    embed.add_field(
        name="👤 Pre-Adm",
        value="Partial access to anti-crash features",
        inline=False,
    )
    embed.set_footer(text="AntiNuke Configuration System")
    return embed
