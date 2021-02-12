import csv
import os
import sqlite3
import time
import discord
from discord.ext import commands
from TypeRacerStats.config import BOT_OWNER_IDS, HELP_BLACK
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.Core.Common.formatting import escape_sequence
from TypeRacerStats.Core.Common.errors import Error


class ManageModules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    async def list_modules(self, ctx):
        modules = ''
        for filename in os.listdir('TypeRacerStats/Core'):
            if filename.endswith('.py') and filename != '__init__.py':
                modules += f"**{filename[:-3]}**\n"

        await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                           description=modules))
        return

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    async def load(self, ctx, extension):
        try:
            self.bot.load_extension(f"Core.{extension}")
        except commands.errors.ExtensionNotFound:
            await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                               description=f"**{extension}** module not found."))
            return

        await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                           description=f"**{extension}** module loaded."))

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    async def unload(self, ctx, extension):
        if extension == 'manage_modules':
            await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                               description=f"**{extension}** module can not be unloaded."))
            return

        try:
            self.bot.unload_extension(f"Core.{extension}")
        except commands.errors.ExtensionNotFound:
            await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                               description=f"**{extension}** module was never loaded."))
            return

        await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                           description=f"**{extension}** module unloaded."))

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    async def reload(self, ctx, extension):
        try:
            self.bot.unload_extension(f"Core.{extension}")
            self.bot.load_extension(f"Core.{extension}")
        except commands.errors.ExtensionNotFound:
            await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                               description=f"**{extension}** module not found."))
            return
        except commands.errors.ExtensionNotLoaded:
            await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                               description=f"**{extension}** module was never loaded."))
            return

        await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                           description=f"**{extension}** module reloaded."))

    @commands.command()
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    async def droptable(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) != 1:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                                 "doesn't exist")))
            return

        await ctx.send(embed=discord.Embed(title='Type "YES" to confirm', color=discord.Color(0)), delete_after=10)

        msg = await self.bot.wait_for('message', check=check(ctx.message.author), timeout=10)

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        try:
            c.execute(f"DROP TABLE t_{player}")
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .missing_information("The user's table does not exist"))
            return

        conn.close()

        await ctx.send(embed=discord.Embed(color=discord.Color(HELP_BLACK),
                                           title=f"{player} table dropped"))


def check(author):
    def inner_check(message):
        if message.author != author:
            return False
        if message.content == 'YES':
            return True
        else:
            return False
    return inner_check


def setup(bot):
    bot.add_cog(ManageModules(bot))
