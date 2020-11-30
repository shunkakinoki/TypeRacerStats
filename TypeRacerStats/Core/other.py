import datetime
import sys
import time
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import seconds_to_text

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = get_aliases('unixreference'))
    async def unixreference(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) > 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} <timestamp>"))
            return
        if len(args) == 0:
            embed = discord.Embed(title = "Unix Timestamp Conversions",
                                  color = discord.Color(MAIN_COLOR))
            embed.set_footer(text = "All converted times are in UTC")
            embed.add_field(name = "Times",
                            value = ('1.25e9 - August 11, 2009\n'
                                     '1.30e9 - March 13, 2011\n'
                                     '1.35e9 - October 12, 2012\n'
                                     '1.40e9 - May 13, 2014\n'
                                     '1.45e9 - December 13, 2015\n'
                                     '1.50e9 - July 14, 2017\n'
                                     '1.55e9 - February 12, 2019\n'
                                     '1.60e9 - September 13, 2020\n'
                                     '1.65e9 - April 15, 2022'))
            await ctx.send(embed = embed)
            return
        try:
            time = int(args[0])
            await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                                 description = datetime.datetime.fromtimestamp(time)
                                                               .strftime("%B %d, %Y, %I:%M:%S")))
            return
        except ValueError:
            try:
                scientific_notation_lst = args[0].lower().split('e')
                await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                                     description = datetime.datetime.fromtimestamp(
                                                                   float(scientific_notation_lst[0]) * 10 ** (int(scientific_notation_lst[1])))
                                                                   .strftime("%B %d, %Y, %I:%M:%S")))
                return
            except:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`timestamp` must be an integer or scientific notation (e.g. 1.0365e9)'))
                return

def setup(bot):
    bot.add_cog(Other(bot))
