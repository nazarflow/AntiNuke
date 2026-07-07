import disnake
from disnake.ext import commands
import config
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

        self.bot.admins.append(member.id)
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
            await ctx.send(f"{member.mention} was successfully removed from the admin list.")
        else:
            await ctx.send(f"{member.mention} is not in the admin list.")

    # ========================================================================================== #
    # !add_user - Add a user to the voice-move tracking list
    # ========================================================================================== #

    @commands.command()
    async def add_user(self, ctx, member: disnake.Member = None):
        if ctx.author.id not in self.bot.admins:
            await ctx.send("Not enough admin permissions to use this command")
            return

        if member is None:
            member = ctx.author

        user_id = member.id

        if user_id == config.OWNER_ID:
            await ctx.send("Access Denied.")
        elif user_id not in self.bot.user_ids:
            self.bot.user_ids.append(user_id)
            await ctx.send(embed=user_added_to_list(member))
        else:
            await ctx.send(embed=user_already_in_list(member))

    # ========================================================================================== #
    # !remove_user - Remove a user from the voice-move tracking list
    # ========================================================================================== #

    @commands.command()
    async def remove_user(self, ctx, member: disnake.Member = None):
        if ctx.author.id not in self.bot.admins:
            await ctx.send("Not enough admin permissions to use this command")
            return

        if member is None:
            member = ctx.author

        user_id = member.id

        if user_id in self.bot.user_ids:
            self.bot.user_ids.remove(user_id)
            await ctx.send(embed=user_removed_from_list(member))
        else:
            await ctx.send(embed=user_not_in_list(member))


def setup(bot):
    bot.add_cog(AdminCommands(bot))
