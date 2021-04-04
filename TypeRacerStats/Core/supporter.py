import csv
import datetime
import json
import os
from PIL import Image, ImageEnhance
import random
import re
import sqlite3
import sys
import time
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_OWNER_IDS, BOT_ADMIN_IDS, MAIN_COLOR, TR_GHOST, TR_INFO
from TypeRacerStats.file_paths import DATABASE_PATH, TEXTS_FILE_PATH_CSV, CSS_COLORS, CMAPS
from TypeRacerStats.Core.Common.accounts import check_account, load_accounts, update_accounts, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, graph_color, seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.supporter import load_supporters, get_supporter, update_supporters, check_dm_perms
from TypeRacerStats.Core.Common.text_id_caching import cache_id, get_cached_id
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.urls import Urls


class Supporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.eugene_message = '`null`'

    @commands.command(aliases=['as'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and
                    check_banned_status(ctx))
    async def add_supporter(self, ctx, *args):
        if len(args) != 2: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"**{args[0]}** is not a valid Discord ID"))
            return

        try:
            tier = int(args[1])
            if tier < 1 or tier > 4:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"Tier level must be between 1 and 4"))
            return

        supporters = load_supporters()

        if args[0] in list(supporters.keys()):
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               f"<@{args[0]}> already in system"))
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

        await ctx.send(embed=discord.Embed(
            description=
            f"**Tier {tier}** supporter <@{args[0]}> added to the list",
            color=discord.Color(0)))
        return

    @commands.command(aliases=['ds'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and
                    check_banned_status(ctx))
    async def delete_supporter(self, ctx, *args):
        if len(args) != 1: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"**{args[0]}** is not a valid Discord ID"))
            return

        supporters = load_supporters()

        if not args[0] in list(supporters.keys()):
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               f"<@{args[0]}> is not in the system"))
            return

        try:
            del supporters[args[0]]
        except KeyError:
            pass

        update_supporters(supporters)

        await ctx.send(embed=discord.Embed(
            description=f"<@{args[0]}> removed from supporters list",
            color=discord.Color(0)))
        return

    @commands.command(aliases=['us'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and
                    check_banned_status(ctx))
    async def upgrade_supporter(self, ctx, *args):
        if len(args) != 2: return

        try:
            int(args[0])
            if len(args[0]) > 18:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"**{args[0]}** is not a valid Discord ID"))
            return

        try:
            tier = int(args[1])
            if tier < 1 or tier > 4:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"Tier level must be between 1 and 4"))
            return

        supporters = load_supporters()

        if not args[0] in list(supporters.keys()):
            await ctx.send(content=f"<@{ctx.message.author.id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               f"<@{args[0]}> is not in the system"))
            return

        supporters[args[0]]['tier'] = tier

        update_supporters(supporters)

        await ctx.send(embed=discord.Embed(
            description=f"<@{args[0]}> upgraded to **Tier {tier}**",
            color=discord.Color(0)))
        return

    @commands.command(aliases=get_aliases('setcolor'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 2 and check_banned_status(ctx))
    async def setcolor(self, ctx, *args):
        if len(args) > 1:
            await ctx.send(
                content=f"<@{ctx.message.author.id}>",
                embed=Error(
                    ctx,
                    ctx.message).parameters(f"{ctx.invoked_with} [hex_value]"))
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
                    await ctx.send(
                        content=f"<@{ctx.message.author.id}>",
                        embed=Error(ctx, ctx.message).incorrect_format((
                            f"[**{args[0]}** is not a valid hex_value]"
                            '(https://www.w3schools.com/colors/colors_picker.asp)'
                        )))
                    return

        supporters = load_supporters()

        supporters[str(ctx.message.author.id)]['color'] = color

        update_supporters(supporters)

        await ctx.send(embed=discord.Embed(title='Color updated',
                                           color=discord.Color(color)))
        return

    @commands.command(aliases=get_aliases('setgraphcolor'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 3 and check_banned_status(ctx))
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
            if not category in [
                    'bg', 'graph_bg', 'axis', 'line', 'text', 'grid', 'cmap'
            ]:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   ('Must provide a valid category: '
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
                        await ctx.send(
                            content=f"<@{ctx.message.author.id}>",
                            embed=Error(ctx, ctx.message).incorrect_format((
                                f"[**{args[1]}** is not a valid hex_value or cmap]"
                                '(https://www.w3schools.com/colors/colors_picker.asp)'
                            )))
                        return
                supporters[user_id]['graph_color'][category] = color
                if category == 'cmap' and not supporters[user_id][
                        'graph_color']['line']:
                    supporters[user_id]['graph_color']['line'] = 0x447BAF

                if isinstance(color, str):
                    color = 0

        update_supporters(supporters)

        ax = plt.subplots()[1]
        ax.plot([x for x in range(0, 50)], [y**0.5 for y in range(0, 50)])

        ax.set_title('Sample Graph')
        ax.set_xlabel('x-axis')
        ax.set_ylabel('y-axis')

        plt.grid(True)
        file_name = 'Sample Graph.png'
        graph_colors = supporters[user_id]['graph_color']
        graph_colors.update({'name': '!'})
        graph_color(ax, graph_colors, False)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        plt.close()

        file_ = discord.File(file_name, filename='image.png')
        embed = discord.Embed(title='Color Updated',
                              color=discord.Color(color))
        embed.set_image(url='attachment://image.png')
        os.remove(file_name)

        await ctx.send(file=file_, embed=embed)
        return

    @commands.command(aliases=get_aliases('echo'))
    @commands.check(lambda ctx: str(ctx.message.author.id) in list(load_supporters().keys()) \
                                and int(load_supporters()[str(ctx.message.author.id)]['tier']) >= 1 and check_banned_status(ctx))
    async def echo(self, ctx, *, args):
        try:
            await ctx.message.delete()
        except:
            pass

        if ctx.message.author.id == 476016555981930526 and 't!tg train' in ctx.message.content:  #pasta's Discord ID
            await ctx.send('<a:pasta_200_iq_patch:794905370011107328>')
            return
        try:
            colors = re.findall('"color":\s*0x[0-9abcdefABCDEF]{6},', args)
            message = args
            for color in colors:
                message = message.replace(
                    color, f"\"color\": {int(color[-9:-1], 16)},")
            embed_data = json.loads(message)
            embed = discord.Embed(**embed_data)
            try:
                for field in embed_data['fields']:
                    embed.add_field(**field)
            except KeyError:
                pass
            try:
                embed.set_thumbnail(**embed_data['thumbnail'])
            except KeyError:
                pass
            try:
                embed.set_image(**embed_data['image'])
            except KeyError:
                pass
            try:
                embed.set_footer(**embed_data['footer'])
            except KeyError:
                pass
            try:
                embed.set_author(**embed_data['author'])
            except KeyError:
                pass
            await ctx.send(embed=embed)
            return
        except:
            await ctx.send(args)
            return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('charlieog'))
    async def charlieog(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <text_id>"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        if len(args) == 2:
            try:
                if args[1] == '*':
                    tid = get_cached_id(ctx.message.channel.id)
                    if not tid:
                        tid = int(args[1])
                else:
                    tid = int(args[1])
                if tid <= 0:
                    raise ValueError
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   f"{args[1]} is not a valid text ID"))
                return
        else:
            tid = 3621293

        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
        except:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist or has no races")))
            return

        file_name = f"t_{player}"
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT * FROM t_{player} ORDER BY t DESC LIMIT 1")
            last_race_timestamp = user_data.fetchone()[1]
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return

        text, ghost = '', ''
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if int(row[0]) == tid:
                    text, ghost = row[1], row[2]
        if not text or not ghost:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"{tid} is not a valid text ID"))
            return

        cache_id(ctx.message.channel.id, tid)

        value_1 = f"\"{text}\" "
        value_2 = (f"[{TR_INFO}]({Urls().text(tid)}) "
                   f"[{TR_GHOST}]({ghost})")
        value = value_1 + value_2
        if len(value) > 1024:
            value_1 = value_1[0:1019 - len(value_2)]
            value = value_1 + "…\"" + value_2

        data = await fetch_data(player, 'play', last_race_timestamp + 0.01,
                                time.time())

        if data:
            c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)",
                          data)

        conn.commit()
        data = c.execute(
            f"""SELECT * FROM
                        (SELECT *
                        FROM {file_name}
                        WHERE t >= ?)
                WHERE tid = ?""",
            (time.time() - 86400, tid)).fetchall()
        conn.close()

        if len(data) < 10:
            description = 'Next save available **now**'
        else:
            description = f"Next save available in **{seconds_to_text(86400 + data[0][1] - time.time())}**"
        value_ = ''
        for i, race in enumerate(data):
            value_ += (
                f"{i + 1}. {seconds_to_text(time.time() - race[1])} ago "
                f"({race[3]} WPM)\n")

        embed = discord.Embed(
            title=f"{player}'s Text #{tid} Statistics in Last 24 Hours",
            color=discord.Color(MAIN_COLOR),
            description=description)
        embed.add_field(name=f"Text ID: {tid}", value=value, inline=False)
        if value_:
            embed.add_field(name='Races', value=value_, inline=False)
        embed.set_footer(text="snowmelt#1745's custom command")

        await ctx.send(embed=embed)
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('kayos'))
    async def kayos(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0:
            args = (3, )

        if len(args) != 1:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} <typo_count>"))
            return

        try:
            typo_count = float(args[0])
            if typo_count < 0 or typo_count > 100:
                raise ValueError
        except ValueError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    '`typo_proportion` must be a positive number between 0 and 100'
                ))

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

        embed = discord.Embed(
            title=f"Random Text With ≈{typo_count}% Random Typos",
            color=discord.Color(MAIN_COLOR),
            description=f"{f'{count:,}'} typos generated")
        embed.add_field(name=f"Text ID: {tid}", value=value, inline=False)
        embed.set_footer(text="KayOS#6686's custom command")

        await ctx.send(embed=embed)
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('dicey'))
    async def dicey(self, ctx, *args):
        question = ' '.join(args)

        if not question:
            await ctx.send(
                content=f"<@{ctx.message.author.id}>",
                embed=Error(
                    ctx,
                    ctx.message).incorrect_format('You must ask a question!'))
            return

        affirmative = [
            'It is certain.', 'It is decidedly so.', 'Without a doubt.',
            'Yes – definitely.', 'You may rely on it.', 'As I see it, yes.',
            'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.',
            'Absolutely', 'Of course.', 'For sure.', 'YES.',
            'By all means, yes.', 'Yeah, I\'d say so.', 'Totally.',
            'Clearly, yes.'
        ]

        uncertain = [
            'Reply hazy, try again.', 'Ask again later.',
            'Better not tell you now.', 'Cannot predict now.',
            'Concentrate and ask again.'
        ]

        negative = [
            'Don\'t count on it.', 'My reply is no.', 'My sources say no.',
            'Outlook not so good.', 'Very doubtful.', 'No.', 'Definitely not.',
            'Certainly not.', 'No way.', 'Definitely not.', 'Of course not.',
            'Nah.', 'Nope.', 'NO.', 'Are you stupid?', 'Obviously not.'
        ]

        category = random.randint(1, 100)
        if category == 1:
            await ctx.send(embed=discord.Embed(
                title='How am I supposed to know?'))
        elif category <= 41:
            await ctx.send(random.choice(affirmative))
        elif category <= 60:
            await ctx.send(random.choice(uncertain))
        else:
            await ctx.send(random.choice(negative))
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.cooldown(1, 60, commands.BucketType.default)
    @commands.command(aliases=get_aliases('eugene'))
    async def eugene(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) > 0 and not user_id == 697048255254495312:
            return
        elif len(args) > 0:
            self.eugene_message = ' '.join(
                ctx.message.content.split(' ')[1:])[:2048]

        if not len(ctx.message.attachments):
            await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                                 title = (datetime.datetime.utcnow() +\
                                                          datetime.timedelta(hours = 9))
                                                          .strftime("%B %-d, %Y, %-I:%M:%S %p"),
                                                 description = self.eugene_message))
            return

        attached_file = ctx.message.attachments[0]

        if not attached_file.url.endswith('png'):
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               'Uploaded image must be **.png** file'))
            return

        height = attached_file.height
        width = attached_file.width
        size = attached_file.size

        if height > 1024 or width > 1024 or size > 1_572_864:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    'Uploaded image must be at most 1024px in width, 1024px in height, and 1.5MB in size.'
                ))
            return

        image_information = await ctx.message.attachments[0].save(
            fp='eugene.png')
        rgb_im = ImageEnhance.Contrast(
            Image.open('eugene.png').convert('RGB')).enhance(3)
        ascii_shades = """@%#*+=-:. """
        num_shades = len(ascii_shades)
        x = int((3900 * width / height)**0.5)
        y = int((3900 * height / width)**0.5 / 2)
        pixel_search_size = int(width / x)
        total_shade = 1_530 * pixel_search_size**2

        ascii_art = '```'

        cur_y = 0
        while cur_y < y:
            cur_x = 0
            while cur_x < x:
                cur_shade = 0
                for x_ in range(pixel_search_size):
                    for y_ in range(pixel_search_size * 2):
                        cur_pixel = rgb_im.getpixel(
                            (cur_x * pixel_search_size + x_,
                             2 * cur_y * pixel_search_size + y_))
                        cur_shade += sum(cur_pixel)
                normalized_shade = min(cur_shade / total_shade, 0.99)
                ascii_art += ascii_shades[int(num_shades * normalized_shade)]
                cur_x += 1
            ascii_art += '\n'
            cur_y += 1
        ascii_art += '```'

        os.remove('eugene.png')
        message = await ctx.send(ascii_art)
        await message.add_reaction('🗑️')

        def check(reaction, user):
            return str(reaction.emoji) == '🗑️' and\
                   reaction.message.id == message.id and\
                   (user.id == ctx.message.author.id or user.id in BOT_ADMIN_IDS)

        try:
            await self.bot.wait_for('reaction_add', check=check, timeout=10)
            await message.delete()
        except:
            await message.remove_reaction('🗑️', self.bot.user)

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('dessle'))
    async def dessle(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        dessle_enlighten = ctx.invoked_with in ['dessle', 'enlighten']
        dessle_invoked = ctx.message.author.id == 279844278455500800  #Dessle's Discord ID

        if (not dessle_invoked and len(args) > 0):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx,
                            ctx.message).parameters(f"{ctx.invoked_with}"))
            return
        elif dessle_invoked and dessle_enlighten and len(args) == 1:
            args = (args[0].strip('<@!').strip('>'), )
            try:
                if len(args[0]) > 18:
                    raise ValueError
                id_ = int(args[0])
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   f"**{args[0]}** is not a valid Discord ID"))
                return

            if id_ in BOT_OWNER_IDS:
                raise commands.CheckFailure
                return

            accounts = load_accounts()
            try:
                accounts[str(id_)]['desslejusted'] = True
                update_accounts(accounts)

                embed = discord.Embed(
                    color=discord.Color(MAIN_COLOR),
                    description=f"<@{id_}> **has been ENLIGHTENED**")
                await ctx.send(embed=embed)
                return
            except KeyError:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).incorrect_format(
                        f"<@{id_}> has not yet been linked to the bot"))
                return

        if len(args) > 0:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx,
                            ctx.message).parameters(f"{ctx.invoked_with}"))
            return

        texts = []
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                texts.append([row[0], row[1], row[2]])

        embed = discord.Embed(title='10 Random Texts',
                              color=discord.Color(MAIN_COLOR))

        for i in range(1, 11):
            random_text = random.choice(texts)
            texts.remove(random_text)

            name = f"{i}. Race Text ID: {random_text[0]}"
            text = f"\"{random_text[1]}\" "
            if len(text) > 50:
                text = f"\"{random_text[1][0:50]}…\" "

            value = text
            value += (f"[{TR_INFO}]({Urls().text(random_text[0])}) "
                      f"[{TR_GHOST}]({random_text[2]})\n")

            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="dessle#9999's custom command")
        await ctx.send(embed=embed)
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('ginoo'))
    async def ginoo(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = ('ginoo75', 1000)

        if len(args) != 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [player] [num_races]"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        try:
            num_races = int(args[1])
            if num_races <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               '`num_races` must be a positive integer'))
            return

        monthly_races = []
        current_month = {
            'month': None,
            'races': 0,
            'words_typed': 0,
            'chars_typed': 0,
            'points': 0,
            'time_spent': 0,
            'total_wpm': 0,
            'best_wpm': 0,
            'worst_wpm': 1000000
        }

        texts_length = load_texts_json()
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        try:
            user_data = c.execute(f"SELECT * FROM t_{player}")
            for row in user_data:
                month = datetime.datetime.fromtimestamp(
                    row[1]).strftime('%Y-%-m')
                if current_month['month'] == None:
                    current_month['month'] = month
                elif current_month['month'] != month:
                    if current_month['races'] >= num_races:
                        current_month.update({
                            'average_wpm':
                            round(
                                current_month['total_wpm'] /
                                current_month['races'], 2)
                        })
                        del current_month['total_wpm']
                        current_month['time_spent'] = round(
                            current_month['time_spent'], 2)
                        current_month['points'] = round(
                            current_month['points'], 2)
                        monthly_races.append(list(current_month.values()))
                    current_month = {
                        'month': month,
                        'races': 0,
                        'words_typed': 0,
                        'chars_typed': 0,
                        'points': 0,
                        'time_spent': 0,
                        'total_wpm': 0,
                        'best_wpm': 0,
                        'worst_wpm': 1000000
                    }

                current_month['races'] += 1
                current_month['words_typed'] += texts_length[str(
                    row[2])]['word count']
                current_month['chars_typed'] += texts_length[str(
                    row[2])]['length']
                current_month['points'] += row[4]
                current_month['time_spent'] += texts_length[str(
                    row[2])]['length'] * 12 / row[3]
                current_month['total_wpm'] += row[3]
                current_month['best_wpm'] = max(current_month['best_wpm'],
                                                row[3])
                current_month['worst_wpm'] = min(current_month['worst_wpm'],
                                                 row[3])
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        if not monthly_races:
            await ctx.send(embed=discord.Embed(
                color=discord.Color(MAIN_COLOR),
                title=
                f"{f'{num_races:,}'} Races Longevity Statistics for {player}",
                description='It\'s empty here.').set_footer(
                    text="ginoo75#6666's custom command"))
            return

        if current_month['races'] >= num_races:
            current_month.update({
                'average_wpm':
                round(current_month['total_wpm'] / current_month['races'], 2)
            })
            del current_month['total_wpm']
            current_month['time_spent'] = round(current_month['time_spent'], 2)
            current_month['points'] = round(current_month['points'], 2)
            monthly_races.append(list(current_month.values()))

        index, longest_chain_index = (0, ) * 2
        max_chain, current_chain = (1, ) * 2
        for i, month_stats in enumerate(monthly_races[1:]):
            index += 1
            previous_month = datetime.datetime.strptime(
                monthly_races[i][0], '%Y-%m')
            month = month_stats[0]
            next_month = (previous_month.month + 1) % 12
            if next_month == 0: next_month = 12
            if datetime.datetime.strptime(month, '%Y-%m') == datetime.datetime(
                    previous_month.year + int((previous_month.month) / 12),
                    next_month, 1):
                current_chain += 1
                if current_chain > max_chain:
                    max_chain = current_chain
                    longest_chain_index = index - current_chain + 1
            else:
                current_chain = 1

        monthly_races.insert(0, list(current_month.keys()))

        file_name = f"{player}_longevity_{num_races}.csv"
        with open(file_name, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(monthly_races)

        file_ = discord.File(file_name, filename=file_name)

        embed = discord.Embed(
            color=discord.Color(MAIN_COLOR),
            title=f"{f'{num_races:,}'} Races Longevity Statistics for {player}",
            description=
            (f"**{f'{(index + 1):,}'}** months with chain of "
             f"**{f'{max_chain:,}'}** starting on "
             f"**{datetime.datetime.strptime(monthly_races[longest_chain_index + 1][0], '%Y-%m').strftime('%B %Y')}**"
             ))
        embed.set_footer(text="ginoo75#6666's custom command")

        await ctx.send(file=file_, embed=embed)
        os.remove(file_name)
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
