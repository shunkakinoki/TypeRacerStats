import sys
import discord
from discord.ext import commands
from TypeRacerStats.config import BOT_OWNER_IDS, MAIN_COLOR
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.supporter import load_supporters, update_supporters

class Supporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['as'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def add_supporter(self, ctx, *args):
        if len(args) != 1: return

        try:
            int(args[0])
            if len(args[0]) != 18:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"**{args[0]}** is not a valid Discord ID"))
            return

        supporters = load_supporters()

        if args[0] in supporters['supporters']:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"<@{args[0]}> already in system"))
            return

        supporters['supporters'].append(args[0])

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(description = f"<@{args[0]}> added to supporters list", color = discord.Color(0)))
        return

    @commands.command(aliases = ['ds'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def delete_supporter(self, ctx, *args):
        if len(args) != 1: return

        try:
            int(args[0])
            if len(args[0]) != 18:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"**{args[0]}** is not a valid Discord ID"))
            return

        supporters = load_supporters()

        if not args[0] in supporters['supporters']:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"**{args[0]}** is not in the system"))
            return

        supporters['supporters'].remove(args[0])

        try:
            del supporters[str(args[0])]
        except KeyError:
            pass

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(description = f"<@{args[0]}> removed from supporters list", color = discord.Color(0)))
        return

    @commands.command(aliases = get_aliases('setcolor'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in load_supporters()['supporters'])
    async def setcolor(self, ctx, *args):
        if len(args) > 1:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [hex_value]"))
            return

        if len(args) == 0:
            color = MAIN_COLOR

        elif len(args) == 1:
            try:
                color = int(f"0x{args[0]}", 16)
                if color < 0 or color > 16777216:
                    raise ValueError
            except ValueError:
                await ctx.send(content = f"<@{ctx.message.author.id}>",
                            embed = Error(ctx, ctx.message)
                                    .incorrect_format((f"[**{args[0]}** is not a valid hex_value]"
                                                        '(https://www.w3schools.com/colors/colors_picker.asp)')))
                return

        supporters = load_supporters()

        supporters.update({str(ctx.message.author.id): color})

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(title = 'Color updated', color = discord.Color(color)))
        return

    @commands.command(aliases = get_aliases('echo'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in load_supporters()['supporters'])
    async def echo(self, ctx, *args):
        await ctx.send(' '.join(args))
        return

def setup(bot):
    bot.add_cog(Supporter(bot))
