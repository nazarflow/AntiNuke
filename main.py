import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import config

# ================================================================================================ #
# Load environment variables
# ================================================================================================ #

load_dotenv()
TOKEN = os.getenv("TOKEN")

# ================================================================================================ #
# Bot initialization
# ================================================================================================ #

client = commands.Bot(
    command_prefix=config.PREFIX,
    intents=disnake.Intents.all(),
    test_guilds=config.TEST_GUILDS,
)
client.remove_command("help")

# Attach runtime state to the bot instance (accessible via self.bot in cogs)
client.user_ids = list(config.USER_IDS)
client.admins = list(config.ADMIN_IDS)
client.kick_counter = dict(config.KICK_COUNTER)

# ================================================================================================ #
# Auto-load all extensions (cogs & events)
# ================================================================================================ #

def load_extensions():
    """Recursively load all .py extensions from src/cogs and src/events."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, "src")

    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("__"):
                # Convert file path to module path (e.g. src.events.channels.channels_tracker)
                filepath = os.path.join(root, filename)
                relative = os.path.relpath(filepath, base_dir)
                module = relative.replace(os.sep, ".").removesuffix(".py")

                try:
                    client.load_extension(module)
                    print(f"  [OK] Loaded: {module}")
                except Exception as e:
                    print(f"  [FAIL] Failed to load {module}: {e}")

# ================================================================================================ #
# on_ready
# ================================================================================================ #

@client.event
async def on_ready():
    await client.change_presence(
        status=disnake.Status.do_not_disturb,
        activity=disnake.Activity(
            type=disnake.ActivityType.watching,
            name="admin abusers",
        ),
    )
    print(f"Logged in as {client.user}")

# ================================================================================================ #
# Start
# ================================================================================================ #

if __name__ == "__main__":
    print("Loading extensions...")
    load_extensions()
    print("Starting bot...")
    client.run(TOKEN)
