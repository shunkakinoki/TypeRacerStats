import csv
import math
import os
import random
import sqlite3
import sys
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR, TR_INFO, TR_GHOST
from TypeRacerStats.file_paths import DATABASE_PATH, TEXTS_FILE_PATH_CSV
from TypeRacerStats.Core.Common.accounts import check_account, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, graph_color
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.texts import load_texts_large
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms, get_graph_colors
from TypeRacerStats.Core.Common.text_id_caching import cache_id, get_cached_id
from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.utility import reduce_list


class TextStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('textbests') + ['breakdown'] +
                      get_aliases('breakdown'))
    async def textbests(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        tb = ctx.invoked_with in ['textbests'] + get_aliases('textbests')
        bd = ctx.invoked_with in ['breakdown'] + get_aliases('breakdown')

        if len(args) == 0: args = check_account(user_id)(args)

        try:
            if len(args) == 0:
                raise ValueError
            elif len(args) > 2:
                raise ValueError
            elif bd and len(args) != 1:
                raise ValueError
        except ValueError:
            optional = ' <num_texts>' if tb else ''
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user]{optional}"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        filter_tb = len(args) == 2
        if filter_tb:
            try:
                num_texts = int(args[1])
                if num_texts <= 0:
                    raise TypeError
            except TypeError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   '`num_texts` must be a positive integer'))
                return

        sum_, count = 0, 0
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT gn, tid, MAX(wpm) FROM t_{player} GROUP BY tid ORDER BY wpm"
            ).fetchall()
            if filter_tb:
                user_data = user_data[-num_texts:]
            min_bucket = int(user_data[0][2] // 10)
            max_bucket = int(user_data[-1][2] //
                             10) if user_data[-1][2] // 10 <= 30 else 30

            if bd:
                breakdown_dict, textbest_dict = {}, {}
                for i in range(min_bucket, max_bucket + 1):
                    breakdown_dict.update({i: 0})
                    textbest_dict.update({i: {'count': 0, 'sum': 0}})

            for row in user_data:
                count += 1
                sum_ += row[2]
                if bd:
                    bucket = int(row[2] // 10) if row[2] // 10 <= 30 else 30
                    if ctx.invoked_with[-1] == '*':
                        breakdown_dict[bucket] += 1
                        textbest_dict[bucket]['sum'] += row[2]
                        textbest_dict[bucket]['count'] += 1
                    else:
                        for i in range(min_bucket, bucket + 1):
                            breakdown_dict[i] += 1

        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        if tb:
            texts_data = load_texts_large()

            if len(user_data) < 10:
                worst = []
                if len(user_data) < 5:
                    top = user_data[::-1]
                else:
                    top = user_data[-5:][::-1]
            else:
                worst = user_data[0:5]
                top = user_data[-5:][::-1]
        else:
            breakdown_text = ''
            max_count_spacer = len(f'{max(breakdown_dict.values()):,}')
            for bucket, count_ in breakdown_dict.items():
                bucket_spacer = 1 + math.floor(
                    math.log10(max_bucket)) - math.floor(math.log10(bucket))
                count_spacer = max_count_spacer - len(f'{count_:,}')
                count_spacer_ = max_count_spacer - len(f'{count - count_:,}')
                breakdown_text += f"{{{bucket * 10}+{' ' * bucket_spacer}WPM}} "
                breakdown_text += f"{' ' * count_spacer}{f'{count_:,}'} [{f'{round(100 * count_ / count, 2):6.2f}'}%] "
                if ctx.invoked_with[-1] == '*':
                    try:
                        average = f"{round(textbest_dict[bucket]['sum'] / textbest_dict[bucket]['count'], 2):6.2f}"
                    except ZeroDivisionError:
                        average = "  ——  "
                    breakdown_text += f"{{{average} WPM}}\n"
                else:
                    breakdown_text += f"({' ' * count_spacer_}{f'{count - count_:,}'} left)\n"

        title = f"{player}'s Text Bests"
        if filter_tb:
            title += f" (Top {f'{num_texts:,}'} Texts Filtered)"
        embed = discord.Embed(title=title, color=discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        embed.add_field(
            name='Texts',
            value=
            (f"**Texts:** {f'{count:,}'}\n"
             f"**Text Bests Average:** {f'{round(sum_ / count, 2):,}'} ("
             f"{f'{round(count * (5 - (sum_ / count) % 5), 2):,}'} total WPM gain "
             f"til {round(5 * ((sum_ / count) // 5 + 1))} WPM)"),
            inline=False
        )

        if tb:
            value = ''
            for i, text in enumerate(top):
                value += f"**{i + 1}. {f'{text[2]:,}'} WPM (Race #{f'{text[0]:,}'})**\n"
                value += f"{texts_data.get(str(text[1]), 'Missing Text')} [:cinema:]({Urls().result(player, text[0], 'play')})\n"
            embed.add_field(name=f"Top {i + 1} Texts",
                            value=value,
                            inline=False)

            value = ''
            for i, text in enumerate(worst):
                value += f"**{i + 1}. {f'{text[2]:,}'} WPM (Race #{f'{text[0]:,}'})**\n"
                value += f"{texts_data.get(str(text[1]), 'Missing Text')} [:cinema:]({Urls().result(player, text[0], 'play')})\n"
            embed.add_field(name=f"Worst {i + 1} Texts",
                            value=value,
                            inline=False)
        else:
            embed.add_field(name='Breakdown',
                            value=f"```css\n{breakdown_text}```",
                            inline=False)

        await ctx.send(embed=embed)
        return

    @commands.cooldown(10, 50, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('personalbest'))
    async def personalbest(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0:
            args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] [text_id]"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        cur_wpm = 0
        if len(args) == 2:
            try:
                if args[1] == '*':
                    text_id = get_cached_id(ctx.message.channel.id)
                    if not text_id:
                        text_id = int(args[1])
                else:
                    text_id = int(args[1])
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx,
                                           ctx.message).incorrect_format(f"**{args[1]}** is not a valid text ID"))
                return
        else:
            try:
                urls = [Urls().get_races(player, 'play', 1)]
                response = (await fetch(urls, 'json'))[0][0]
                text_id = int(response['tid'])
                cur_wpm = float(response['wpm'])
            except:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx,
                                           ctx.message).missing_information())
                return

        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if int(row[0]) == text_id:
                    text = row[1]
                    break
                else:
                    continue

        try:
            if len(text) > 1024:
                text = f"\"{text[0:1020]}…\""
            else:
                text = f"\"{text}\""
        except NameError:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               f"{text_id} is not a valid text ID"))
            return

        count, sum_, best, best_gn, worst_gn = (0, ) * 5
        worst = 100000
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT gn, wpm FROM t_{player} WHERE tid = ?",
                (text_id, )).fetchall()
            for row in user_data:
                count += 1
                sum_ += row[1]
                if row[1] > best:
                    best_gn, best = row
                if row[1] < worst:
                    worst_gn, worst = row
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        if cur_wpm > best:
            color, description = 754944, f"**Improved by {round(cur_wpm - best, 2)} WPM (to {round(cur_wpm, 2)} WPM)**"
        else:
            color, description = MAIN_COLOR, ''

        if not count:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               f"**{player}** has not completed the text yet"))
            return

        value = f"**Times:** {f'{count:,}'}\n"
        if cur_wpm:
            value += f"**Last Race:** {f'{cur_wpm:,}'} WPM\n"
        value += (f"**Average:** {f'{round(sum_ / count, 2):,}'} WPM\n"
                  f"**Fastest:** {f'{best:,}'} WPM "
                  f"(Race #{f'{best_gn:,}'}) [:cinema:]"
                  f"({Urls().result(player, best_gn, 'play')})\n"
                  f"**Slowest:** {f'{worst:,}'} WPM "
                  f"(Race #{f'{worst_gn:,}'}) [:cinema:]"
                  f"({Urls().result(player, worst_gn, 'play')})\n")

        title = f"Quote #{text_id} Statistics for {player}"
        cache_id(ctx.message.channel.id, text_id)
        if description:
            embed = discord.Embed(title=title,
                                  color=discord.Color(color),
                                  url=Urls().text(text_id),
                                  description=description)
        else:
            embed = discord.Embed(title=title,
                                  color=discord.Color(color),
                                  url=Urls().text(text_id))

        embed.set_thumbnail(url=Urls().thumbnail(player))
        embed.add_field(name='Quote', value=text, inline=False)
        embed.add_field(name='Speeds', value=value)

        if ctx.invoked_with[-1] == '*' and len(user_data) > 1:
            ax = plt.subplots()[1]

            data_y = [i[1] for i in user_data]
            if cur_wpm: data_y += [cur_wpm]
            length = len(data_y)
            data_x = [i + 1 for i in range(length)]

            if length < 30:
                ax.plot(data_x, data_y)
            else:
                ax.scatter(data_x,
                           data_y,
                           marker='.',
                           alpha=0.1,
                           color='#000000')
                if length < 500:
                    sma = length // 10
                else:
                    sma = 50

                moving_y = [sum(data_y[0:sma]) / sma]
                moving_y += [
                    sum(data_y[i - sma:i]) / sma for i in range(sma, length)
                ]
                moving_x = [data_x[0]] + data_x[sma:]
                moving_y = reduce_list(moving_y)
                moving_x = reduce_list(moving_x)
                ax.plot(moving_x, moving_y, color='#FF0000')
                title += f"\n(Moving Average of {sma} Races)"

            ax.set_title(title)
            ax.set_xlabel('Attempt #')
            ax.set_ylabel('WPM')
            plt.grid(True)
            file_name = f"{title}.png"

            graph_colors = get_graph_colors(user_id)
            graph_color(ax, graph_colors, False)
            plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
            plt.close()

            file_ = discord.File(file_name, filename='image.png')
            embed.set_image(url='attachment://image.png')
            os.remove(file_name)
            await ctx.send(file=file_, embed=embed)
            return

        await ctx.send(embed=embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('unraced'))
    async def unraced(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0 or (len(args) == 1 and len(args[0]) < 4):
            args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <length>"))
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
                length = int(args[1])
                if length < 1 or length > 999:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).incorrect_format(
                        '`length` must be a positive integer less than 999'))
                return
        else:
            length = 0

        all_tids, user_tids, texts_data = set(), set(), dict()
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                all_tids.add(int(row[0]))
                texts_data.update(
                    {int(row[0]): {
                         'text': row[1],
                         'ghost': row[2]
                     }})

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT DISTINCT tid FROM t_{player}")
            for row in user_data:
                user_tids.add(row[0])
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        unraced_tids = list(all_tids - user_tids)
        if length:
            unraced_tids = list(
                filter(lambda x: len(texts_data[x]['text']) < length,
                       unraced_tids))
        if len(unraced_tids) == 0:
            description = f"{player} has completed all texts"
            if length:
                description += f" under length {length}"
            description += '!'
            await ctx.send(embed=discord.Embed(title='Nothing to Choose From',
                                               color=discord.Color(754944),
                                               description=description))
            return

        title = 'Random Unraced Texts'
        if length:
            title += f" Under Length {length}"
        title += f" for {player} ({f'{len(unraced_tids):,}'} left)"

        embed = discord.Embed(title=title, color=discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        try:
            for i in range(0, 5):
                random_tid = random.choice(unraced_tids)
                value_1 = f"\"{texts_data[random_tid]['text']}\" "
                value_2 = (f"[{TR_INFO}]({Urls().text(random_tid)}) "
                           f"[{TR_GHOST}]({texts_data[random_tid]['ghost']})")
                value = value_1 + value_2
                if len(value) > 1024:
                    value_1 = value_1[0:1019 - len(value_2)]
                    value = f"{value_1}…\" {value_2}"

                embed.add_field(name=f"{i + 1}. Race Text ID: {random_tid}",
                                value=value,
                                inline=False)
                unraced_tids.remove(random_tid)
        except:
            pass

        await ctx.send(embed=embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('textsunder'))
    async def textsunder(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) < 2 or len(args) > 3:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] [speed] <text_length>"))
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
            speed = float(args[1])
            if speed <= 0:
                raise ValueError
            length = 0
            if len(args) == 3:
                length = float(args[2])
                if length <= 0:
                    raise ValueError
        except ValueError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    '`speed` and `length` must be positive numbers'))
            return

        texts_data = dict()
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                texts_data.update(
                    {int(row[0]): {
                         'text': row[1],
                         'ghost': row[2]
                     }})

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT gn, tid, MAX(wpm) FROM t_{player} GROUP BY tid ORDER BY wpm"
            ).fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        tu_dict, tids = dict(), []
        for tid in user_data:
            if tid[2] > speed:
                continue
            if length:
                if len(texts_data[tid[1]]['text']) > length:
                    continue
            tu_dict.update({tid[1]: tid[2]})
            tids.append(tid[1])

        if len(tu_dict) == 0:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    'No texts found that meet the required criteria'))
            return

        title = f"Random Texts Under {f'{speed:,}'} WPM"
        if len(args) == 3:
            title += f" and {f'{length:,}'} Length"
        title += f" for {player} ({f'{len(tu_dict):,}'} left)"

        embed = discord.Embed(title=title, color=discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        for i in range(0, 5):
            try:
                random_tid = random.choice(tids)
                value_1 = f"\"{texts_data[random_tid]['text']}\" "
                value_2 = f"[{TR_INFO}]({Urls().text(random_tid)}) [{TR_GHOST}]({texts_data[random_tid]['ghost']})"
                value = value_1 + value_2
                if len(value) > 1024:
                    value_1 = value_1[0:1019 - len(value_2)]
                    value = value_1 + "…\" " + value_2
                embed.add_field(
                    name=(f"{i + 1}. {f'{tu_dict[random_tid]:,}'} WPM"
                          f" (Race Text ID: {random_tid})"),
                    value=value,
                    inline=False)
                tids.remove(random_tid)
            except IndexError:
                pass

        await ctx.send(embed=embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('textslessequal'))
    async def textslessequal(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) < 2 or len(args) > 3:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] [num] <wpm/points/time>"))
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
            num = float(args[1])
            if num <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    '`speed` and `length` must be positive numbers'))
            return

        if len(args) == 2:
            category = 'wpm'
        else:
            category = args[2].lower()
            if category not in ['wpm', 'points', 'times']:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).incorrect_format(
                        'Must provide a valid category: `wpm/points/times`'))
                return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            count = len(
                c.execute(f"SELECT DISTINCT tid from t_{player}").fetchall())
            if category == 'wpm':
                user_data = c.execute(
                    f"""SELECT tid, COUNT(tid)
                                          FROM t_{player}
                                          WHERE wpm >= ?
                                          GROUP BY tid
                                          ORDER BY COUNT(tid) DESC""",
                    (num, )).fetchall()
            elif category == 'points':
                user_data = c.execute(
                    f"""SELECT tid, COUNT(tid)
                                          FROM t_{player}
                                          WHERE pts >= ?
                                          GROUP BY tid
                                          ORDER BY COUNT(tid) DESC""",
                    (num, )).fetchall()
            else:
                user_data = c.execute(
                    f"""SELECT tid, COUNT(tid)
                                          FROM t_{player}
                                          GROUP BY tid
                                          HAVING COUNT(tid) >= ?
                                          ORDER BY COUNT(tid) DESC""",
                    (num, )).fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        texts_data = load_texts_large()
        category = {
            'wpm': 'WPM',
            'points': 'Points',
            'times': 'Times'
        }[category]
        if category == 'Times':
            num = int(num)

        embed = discord.Embed(
            title=f"{player}'s Total Texts Typed Over {f'{num:,}'} {category}",
            color=discord.Color(MAIN_COLOR),
            description=
            (f"**Texts Typed:** {f'{count:,}'}\n"
             f"**Texts Over {f'{num:,}'} {category}:** "
             f"{f'{len(user_data):,}'} ({round(100 * len(user_data) / count, 2)}%)"
             ))
        embed.set_thumbnail(url=Urls().thumbnail(player))
        for i in range(0, 10):
            try:
                value_1 = f"\"{texts_data[str(user_data[i][0])]}\" "
                value_2 = f"[{TR_INFO}]({Urls().text(user_data[i][0])})"
                value = value_1 + value_2
                if len(value) > 1024:
                    value_1 = value_1[0:1019 - len(value_2)]
                    value = value_1 + "…\" " + value_2
                embed.add_field(
                    name=(f"{i + 1}. {f'{user_data[i][1]:,}'} times "
                          f"(Race Text ID: {user_data[i][0]})"),
                    value=value,
                    inline=False)
            except:
                pass

        await ctx.send(embed=embed)
        return


def setup(bot):
    bot.add_cog(TextStats(bot))
