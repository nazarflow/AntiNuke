import asyncio
import os
import uvicorn

import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import config
from src.database import init_db
from src.database import repository as db
from src.api.app import app

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

async def main():
    print("="*60)
    print("  AntiNuke Bot & Web API Initialization")
    print("="*60)
    
    # 1. Initialize database and schemas
    print("[*] Initializing Database...")
    await init_db()

    # 2. Load runtime state
    print("[*] Loading Runtime State...")
    db_admins = await db.get_all_admins()
    client.admins = list(set(db_admins + [config.OWNER_ID]))
    client.user_ids = await db.get_all_tracked_users()
    client.kick_counter = dict(config.KICK_COUNTER)

    # 3. Load bot extensions
    load_extensions()

    # 4. Configure FastAPI Uvicorn Server
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(uvicorn_config)

    # 5. Start both tasks concurrently in the same event loop
    print("\n🚀 Starting Disnake Client and FastAPI Server concurrently...")
    await asyncio.gather(
        server.serve(),
        client.start(TOKEN)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutdown requested.")
