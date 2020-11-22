import discord
from discord.ext import commands
from TypeRacerStats.config import BOT_OWNER_IDS
from TypeRacerStats.config import HELP_BLACK

class ManageModules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def load(self, ctx, extension):
        self.bot.load_extension(f"Core.{extension}")

        await ctx.send(embed = discord.Embed(color = discord.Color(HELP_BLACK),
                                             description = f"**{extension}** module loaded."))

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def unload(self, ctx, extension):
        self.bot.unload_extension(f"Core.{extension}")

        await ctx.send(embed = discord.Embed(color = discord.Color(HELP_BLACK),
                                             description = f"**{extension}** module unloaded."))

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def reload(self, ctx, extension):
        self.bot.unload_extension(f"Core.{extension}")
        self.bot.load_extension(f"Core.{extension}")

        await ctx.send(embed = discord.Embed(color = discord.Color(HELP_BLACK),
                                             description = f"**{extension}** module reloaded."))

def setup(bot):
    bot.add_cog(ManageModules(bot))
