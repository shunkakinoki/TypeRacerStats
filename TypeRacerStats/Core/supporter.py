import csv
import sqlite3
import sys
import time
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_OWNER_IDS, MAIN_COLOR, TR_GHOST, TR_INFO
from TypeRacerStats.file_paths import DATABASE_PATH, TEXTS_FILE_PATH_CSV
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.supporter import load_supporters, get_supporter, update_supporters
from TypeRacerStats.Core.Common.urls import Urls

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

    @commands.command(aliases = get_aliases('charlieog'))
    async def charlieog(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <text_id>"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                                         "doesn't exist")))
            return

        if len(args) == 2:
            try:
                tid = int(args[1])
                if tid <= 0:
                    raise ValueError
            except ValueError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format(f"{args[1]} is not a valid text ID"))
                return
        else:
            tid = 3621293

        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist or has no races")))
            return

        file_name = f"t_{player}"
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM t_{player} ORDER BY t DESC LIMIT 1")
            last_race_timestamp = user_data.fetchone()[1]
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return

        text, ghost = '', ''
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if int(row[0]) == tid:
                    text, ghost = row[1], row[2]
        if not text or not ghost:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"{tid} is not a valid text ID"))
            return

        value_1 = f"\"{text}\" "
        value_2 = (f"[{TR_INFO}]({Urls().text(tid)}) "
                    f"[{TR_GHOST}]({ghost})")
        value = value_1 + value_2
        if len(value) > 1024:
            value_1 = value_1[0:1019 - len(value_2)]
            value = value_1 + "…\"" + value_2

        data = await fetch_data(player, 'play', last_race_timestamp + 0.01, time.time())

        if data:
            c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)", data)

        conn.commit()
        data = c.execute(f"""SELECT * FROM
                                    (SELECT *
                                    FROM {file_name}
                                    WHERE t >= {time.time() - 86400})
                            WHERE tid = {tid}""").fetchall()
        conn.close()

        if len(data) < 10:
            description = 'Next save available **now**'
        else:
            description = f"Next save available in **{seconds_to_text(86400 + data[0][1] - time.time())}**"
        value_ = ''
        for i, race in enumerate(data):
            value_ += (f"{i + 1}. {seconds_to_text(time.time() - race[1])} ago "
                       f"({race[3]} WPM)\n")

        embed = discord.Embed(title = f"{player}'s Text #{tid} Statistics in Last 24 Hours",
                              color = discord.Color(MAIN_COLOR),
                              description = description)
        embed.add_field(name = f"Text ID: {tid}",
                        value = value,
                        inline = False)
        if value_:
            embed.add_field(name = 'Races', value = value_, inline = False)
        embed.set_footer(text = "snowmelt#1745's custom command")

        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(Supporter(bot))
