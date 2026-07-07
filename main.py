import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import config
from src import database

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

# Initialize database
database.setup_db()

# Attach runtime state to the bot instance (accessible via self.bot in cogs)
# Load from SQLite database, guarantee owner has admin access
db_admins = database.get_all_admins()
client.admins = list(set(db_admins + [config.OWNER_ID]))
client.user_ids = database.get_all_tracked_users()
client.kick_counter = dict(config.KICK_COUNTER)

# ================================================================================================ #
# Auto-load all extensions (cogs & events)
# ================================================================================================ #

def load_extensions():
    """Load all .py extensions from specific directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Only scan cogs and events (skip embeds, database, etc.)
    directories_to_scan = ["src/cogs", "src/events"]
    
    total_loaded = 0
    total_failed = 0
    failed_modules = []
    
    print("\n" + "="*60)
    print("🚀 INIT: Starting AntiNuke Extension Loader")
    print("="*60)

    for relative_dir in directories_to_scan:
        full_path = os.path.join(base_dir, relative_dir.replace("/", os.sep))
        for root, dirs, files in os.walk(full_path):
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("__"):
                    filepath = os.path.join(root, filename)
                    relative = os.path.relpath(filepath, base_dir)
                    module = relative.replace(os.sep, ".").removesuffix(".py")

                    try:
                        client.load_extension(module)
                        print(f"  [+] Loaded successfully : {module}")
                        total_loaded += 1
                    except Exception as e:
                        print(f"  [-] Failed to load      : {module}")
                        print(f"      └─ Reason: {e}")
                        failed_modules.append(module)
                        total_failed += 1

    print("-" * 60)
    print(f"📊 SUMMARY: Successfully loaded: {total_loaded} / {total_loaded + total_failed}")
    if total_failed > 0:
        print(f"❌ ERRORS: {total_failed} modules failed to load.")
    else:
        print("✅ ERRORS: 0 (All modules loaded perfectly)")
    print("="*60 + "\n")

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
