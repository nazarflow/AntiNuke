import disnake
from disnake.ext import commands
import config
from src.services import admin_service
from src.embeds.members import user_added_to_list, user_already_in_list, user_removed_from_list, user_not_in_list


class AdminCommands(commands.Cog):
    """Commands for managing admin list and user tracking list."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================================================== #
    # !add_adm - Add a user to the admin list
    # ========================================================================================== #

    @commands.command()
    async def add_adm(self, ctx, member: disnake.Member):
        if ctx.author.id != config.OWNER_ID:
            await ctx.send(
                f"{ctx.author.mention}, Only the owner can add/remove administrators."
            )
            return

        if member.id not in self.bot.admins:
            self.bot.admins.append(member.id)
            await admin_service.add_admin(member.id)
        await ctx.send(f"{member.mention} was successfully added to the admin list.")

    # ========================================================================================== #
    # !remove_adm - Remove a user from the admin list
    # ========================================================================================== #

    @commands.command()
    async def remove_adm(self, ctx, member: disnake.Member):
        if ctx.author.id != config.OWNER_ID:
            await ctx.send(
                f"{ctx.author.mention}, Only the owner can add/remove administrators."
            )
            return

        if member.id in self.bot.admins:
            self.bot.admins.remove(member.id)
            await admin_service.remove_admin(member.id)
            await ctx.send(f"{member.mention} was successfully removed from the admin list.")
        else:
            await ctx.send(f"{member.mention} is not in the admin list.")

def setup(bot):
    bot.add_cog(AdminCommands(bot))
