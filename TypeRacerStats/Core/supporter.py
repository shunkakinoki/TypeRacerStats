import csv
import json
import os
import random
import sqlite3
import sys
import time
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_OWNER_IDS, MAIN_COLOR, TR_GHOST, TR_INFO
from TypeRacerStats.file_paths import DATABASE_PATH, TEXTS_FILE_PATH_CSV, CSS_COLORS, CMAPS
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, graph_color, seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.supporter import load_supporters, get_supporter, update_supporters, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls

class Supporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['as'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def add_supporter(self, ctx, *args):
        if len(args) != 2: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"**{args[0]}** is not a valid Discord ID"))
            return

        try:
            tier = int(args[1])
            if tier < 1 or tier > 4:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"Tier level must be between 1 and 4"))
            return

        supporters = load_supporters()

        if args[0] in list(supporters.keys()):
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"<@{args[0]}> already in system"))
            return

        supporters.update({
            args[0]: {
                'color': MAIN_COLOR,
                'tier': tier,
                'graph_color': {
                    'bg': None,
                    'graph_bg': None,
                    'axis': None,
                    'line': None,
                    'text': None,
                    'grid': None,
                    'cmap': None
                }
            }
        })

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(description = f"**Tier {tier}** supporter <@{args[0]}> added to the list", color = discord.Color(0)))
        return

    @commands.command(aliases = ['ds'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def delete_supporter(self, ctx, *args):
        if len(args) != 1: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"**{args[0]}** is not a valid Discord ID"))
            return

        supporters = load_supporters()

        if not args[0] in list(supporters.keys()):
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"<@{args[0]}> is not in the system"))
            return

        try:
            del supporters[args[0]]
        except KeyError:
            pass

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(description = f"<@{args[0]}> removed from supporters list", color = discord.Color(0)))
        return

    @commands.command(aliases = ['us'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS)
    async def upgrade_supporter(self, ctx, *args):
        if len(args) != 2: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"**{args[0]}** is not a valid Discord ID"))
            return

        try:
            tier = int(args[1])
            if tier < 1 or tier > 4:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"Tier level must be between 1 and 4"))
            return

        supporters = load_supporters()

        if not args[0] in list(supporters.keys()):
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"<@{args[0]}> is not in the system"))
            return

        supporters[args[0]]['tier'] = tier

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(description = f"<@{args[0]}> upgraded to **Tier {tier}**", color = discord.Color(0)))
        return

    @commands.command(aliases = get_aliases('setcolor'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 2)
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
                try:
                    colors = get_colors()
                    color = colors[args[0].lower()]
                except KeyError:
                    await ctx.send(content = f"<@{ctx.message.author.id}>",
                                   embed = Error(ctx, ctx.message)
                                           .incorrect_format((f"[**{args[0]}** is not a valid hex_value]"
                                                               '(https://www.w3schools.com/colors/colors_picker.asp)')))
                    return

        supporters = load_supporters()

        supporters[str(ctx.message.author.id)]['color'] = color

        update_supporters(supporters)

        await ctx.send(embed = discord.Embed(title = 'Color updated', color = discord.Color(color)))
        return

    @commands.command(aliases = get_aliases('setgraphcolor'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 3)
    async def setgraphcolor(self, ctx, *args):
        supporters = load_supporters()
        user_id = str(ctx.message.author.id)
        color = 0

        if len(args) == 0:
            supporters[user_id]['graph_color'] = {
                'bg': None,
                'graph_bg': None,
                'axis': None,
                'line': None,
                'text': None,
                'grid': None,
                'cmap': None
            }

        else:
            category = args[0].lower()
            if not category in ['bg', 'graph_bg', 'axis', 'line', 'text', 'grid', 'cmap']:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format(('Must provide a valid category: '
                                                          '`[bg/graph_bg/axis/line/text/grid]`')))
                return

            if len(args) == 1:
                supporters[user_id]['graph_color'][category] = None
            else:
                try:
                    if category == 'cmap':
                        raise ValueError

                    color = int(f"0x{args[1]}", 16)
                    if color < 0 or color > 16777216:
                        raise ValueError
                except ValueError:
                    try:
                        if category == 'cmap':
                            cmaps = get_cmaps()
                            color = cmaps[args[1].lower()]
                        else:
                            colors = get_colors()
                            color = colors[args[1].lower()]
                    except KeyError:
                        await ctx.send(content = f"<@{ctx.message.author.id}>",
                                       embed = Error(ctx, ctx.message)
                                               .incorrect_format((f"[**{args[1]}** is not a valid hex_value or cmap]"
                                                                   '(https://www.w3schools.com/colors/colors_picker.asp)')))
                        return
                supporters[user_id]['graph_color'][category] = color
                if category == 'cmap' and not supporters[user_id]['graph_color']['line']:
                    supporters[user_id]['graph_color']['line'] = 0x447BAF

                if isinstance(color, str):
                    color = 0

        update_supporters(supporters)

        ax = plt.subplots()[1]
        ax.plot([x for x in range(0, 50)],
                [y ** 0.5 for y in range(0, 50)])

        ax.set_title('Sample Graph')
        ax.set_xlabel('x-axis')
        ax.set_ylabel('y-axis')

        plt.grid(True)
        file_name = 'Sample Graph.png'
        graph_color(ax, supporters[user_id]['graph_color'], False)
        plt.savefig(file_name, facecolor = ax.figure.get_facecolor())
        plt.close()

        file_ = discord.File(file_name, filename = 'image.png')
        embed = discord.Embed(title = 'Color Updated', color = discord.Color(color))
        embed.set_image(url = 'attachment://image.png')
        os.remove(file_name)

        await ctx.send(file = file_, embed = embed)
        return

    @commands.command(aliases = get_aliases('echo'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 1)
    async def echo(self, ctx, *args):
        await ctx.send(' '.join(args))
        return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
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

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('kayos'))
    async def kayos(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0:
            args = (3,)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} <typo_count>"))
            return

        try:
            typo_count = float(args[0])
            if typo_count < 0 or typo_count > 100:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`typo_proportion` must be a positive number between 0 and 100'))

        text, ghost = '', ''
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            tid, text, ghost = tuple(random.choice(list(reader)))

        typos, count = 'abcdefghijklmnopqrstuvwxyz!? <>_=1234567890/*-', 0
        text_ = ''
        for i in range(0, len(text)):
            if random.random() * 100 <= typo_count:
                random_ = random.choice(typos)
                if random_ == '_' or random_ == '*':
                    text_ += f"\{random_}"
                else:
                    text_ += random_
                if random_ != text[i]:
                    count += 1
            else:
                text_ += text[i]

        value_1 = f"\"{text_}\" "
        value_2 = (f"[{TR_INFO}]({Urls().text(tid)}) "
                    f"[{TR_GHOST}]({ghost})")
        value = value_1 + value_2
        if len(value) > 1024:
            value_1 = value_1[0:1019 - len(value_2)]
            value = value_1 + "…\"" + value_2

        embed = discord.Embed(title = f"Random Text With ≈{typo_count}% Random Typos",
                              color = discord.Color(MAIN_COLOR),
                              description = f"{f'{count:,}'} typos generated")
        embed.add_field(name = f"Text ID: {tid}",
                        value = value,
                        inline = False)
        embed.set_footer(text = "KayOS#6686's custom command")

        await ctx.send(embed = embed)
        return

    @commands.command(aliases = get_aliases('dicey'))
    async def dicey(self, ctx, *args):
        question = ' '.join(args)

        if not question:
            await ctx.send(content = f"<@{ctx.message.author.id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('You must ask a question!'))
            return

        affirmative = [
            'It is certain.',
            'It is decidedly so.',
            'Without a doubt.',
            'Yes – definitely.',
            'You may rely on it.',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good.',
            'Yes.',
            'Signs point to yes.'
        ]

        uncertain = [
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.'
        ]

        negative = [
            'Don\'t count on it.',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good.',
            'Very doubtful.',
            'No.',
            'Definitely not.'
        ]

        category = random.randint(1, 100)
        if category == 1:
            await ctx.send(embed = discord.Embed(title = 'How am I supposed to know?'))
        elif category <= 34:
            await ctx.send(random.choice(affirmative))
        elif category <= 67:
            await ctx.send(random.choice(uncertain))
        else:
            await ctx.send(random.choice(negative))
        return

def get_colors():
    with open(CSS_COLORS, 'r') as jsonfile:
        css_colors = json.load(jsonfile)

    return css_colors

def get_cmaps():
    with open(CMAPS, 'r') as jsonfile:
        cmaps = json.load(jsonfile)

    return cmaps

def setup(bot):
    bot.add_cog(Supporter(bot))
