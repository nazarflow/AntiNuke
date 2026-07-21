import disnake
from disnake.ext import commands
import traceback
import sys
import os
import datetime
import config

class GlobalErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_error_to_file(self, error, error_type="Unknown"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filepath = os.path.join(self.log_dir, "errors.log")
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] === ERROR in {error_type} ===\n")
            traceback.print_exception(type(error), error, error.__traceback__, file=f)
            f.write("\n" + "="*50 + "\n\n")

    async def notify_developer(self, error, error_source: str):
        try:
            owner = await self.bot.fetch_user(config.OWNER_ID)
            if owner:
                embed = disnake.Embed(
                    title="⚠️ Critical Error Caught",
                    description=f"An error occurred in `{error_source}`.",
                    color=disnake.Color.red()
                )
                embed.add_field(name="Error Message", value=f"```py\n{str(error)[:1000]}\n```", inline=False)
                
                # Try to get file and line number
                tb = traceback.extract_tb(error.__traceback__)
                if tb:
                    last_call = tb[-1]
                    embed.add_field(name="Location", value=f"`{last_call.filename}` (Line {last_call.lineno})", inline=False)
                
                embed.set_footer(text="Full traceback saved to src/logs/errors.log")
                await owner.send(embed=embed)
        except Exception as e:
            print(f"[ERROR] Failed to send error DM to developer: {e}")

    # 1. Catch Slash Command Errors
    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        # Ignore CommandNotFound
        if isinstance(error, commands.CommandNotFound):
            return

        cmd_name = inter.application_command.name if inter.application_command else "Unknown"
        print(f"  [CRITICAL] Error in slash command /{cmd_name} - Logs saved / sent to dev")
        
        self.log_error_to_file(error, f"Slash Command /{cmd_name}")
        await self.notify_developer(error, f"Slash Command: /{cmd_name}")

        try:
            msg = "⚠️ An error occurred. Developer notified."
            if inter.response.is_done():
                await inter.followup.send(msg, ephemeral=True)
            else:
                await inter.response.send_message(msg, ephemeral=True)
        except:
            pass

    # 2. Catch Prefix Command Errors
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return

        print(f"  [CRITICAL] Error in prefix command {ctx.command} - Logs saved / sent to dev")
        self.log_error_to_file(error, f"Prefix Command !{ctx.command}")
        await self.notify_developer(error, f"Prefix Command: !{ctx.command}")

        try:
            await ctx.send("⚠️ An error occurred. Developer notified.")
        except:
            pass

def setup(bot):
    cog = GlobalErrorHandler(bot)
    bot.add_cog(cog)
    
    # Override global on_error to intercept event exceptions properly
    async def global_on_error(event_method, *args, **kwargs):
        error = sys.exc_info()[1]
        if not error:
            return
            
        print(f"  [CRITICAL] Error in event {event_method} - Logs saved / sent to dev")
        
        # Handle specifically Missing Permissions (Forbidden) to clarify the issue
        if isinstance(error, disnake.errors.Forbidden):
            error_source = f"Event: {event_method} (Missing Permissions)"
        else:
            error_source = f"Event: {event_method}"
            
        cog.log_error_to_file(error, error_source)
        await cog.notify_developer(error, error_source)

        # If it was an interaction, try to respond to the user
        if args and isinstance(args[0], disnake.Interaction):
            inter = args[0]
            try:
                msg = "⚠️ A critical error occurred. Developer notified."
                if inter.response.is_done():
                    await inter.followup.send(msg, ephemeral=True)
                else:
                    await inter.response.send_message(msg, ephemeral=True)
            except:
                pass

    bot.on_error = global_on_error
