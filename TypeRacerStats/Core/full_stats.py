import datetime
import sqlite3
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account, check_banned_status
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, num_to_text, seconds_to_text
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls

class FullStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases = get_aliases('racesover'))
    async def racesover(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) != 3:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [num] [wpm/points]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return

        try:
            num = float(args[1])
            if num <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`num` must be a positive number'))
            return

        categories = ['wpm', 'points']

        if not args[2] in categories:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`category` must be `wpm/points`'))
            return

        if args[2] == 'points':
            category = 'pts'
        else:
            category = 'wpm'

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        meeting, total = 0, 0
        try:
            user_data = c.execute(f"SELECT {category} FROM t_{player}")
            for row in user_data:
                total += 1
                if row[0] > num:
                    meeting += 1
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        category = {'wpm': 'WPM', 'pts': 'points'}[category]

        embed = discord.Embed(title = f"{player}'s Total Races Over {f'{num:,}'} {category}",
                              color = discord.Color(MAIN_COLOR),
                              description = (f"{f'{meeting:,}'} of {player}'s {f'{total:,}'} are above "
                                             f"{f'{num:,}'} {category} ({f'{round(100 * meeting / total, 2):,}'}%)"))
        embed.set_footer(text = 'Counts texts GREATER than specified parameter (not equal to)')

        await ctx.send(embed = embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases = get_aliases('milestone'))
    async def milestone(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) != 3:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [num] [races/wpm/points]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return

        try:
            num = int(args[1])
            if num <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`num` must be a positive integer'))
            return

        categories = ['races', 'wpm', 'points']

        if not args[2] in categories:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`category` must be `races/wpm/points`'))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        try:
            first_race = c.execute(f"SELECT t FROM t_{player} LIMIT 1").fetchone()[0]
            if args[2] == 'wpm':
                achieved, race_num = c.execute(f"SELECT t, gn FROM t_{player} WHERE wpm >= ? ORDER BY t LIMIT 1", (num,)).fetchone()
            elif args[2] == 'races':
                achieved, race_num = c.execute(f"SELECT t, gn FROM t_{player} WHERE gn == ?", (num,)).fetchone()
            else:
                user_data = c.execute(f"SELECT t, pts, gn FROM t_{player} ORDER BY t")
                sum_, achieved = 0, 0
                for row in user_data:
                    sum_ += row[1]
                    if sum_ >= num:
                        achieved = row[0]
                        race_num = row[2]
                        break
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        except TypeError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('The user has not achieved the milestone yet'))
            return
        conn.close()

        if not achieved:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"[**{player}**]({Urls().user(player, 'play')}) has not achieved the milestone yet"))
            return

        category_1 = {'races': '', 'wpm': ' WPM', 'points': ' Point'}[args[2]]
        category_2 = {'races': 'races', 'wpm': 'WPM', 'points': 'points'}[args[2]]
        embed = discord.Embed(title = f"{player}'s {num_to_text(num)}{category_1} Race",
                              color = discord.Color(MAIN_COLOR),
                              url = Urls().result(player, race_num, 'play'))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.add_field(name = f"{player} achieved {f'{num:,}'} {category_2} on:",
                        value = f"{datetime.datetime.fromtimestamp(achieved).strftime('%B %d, %Y, %I:%M:%S %p')} UTC")
        embed.add_field(name = 'It took:',
                        value = seconds_to_text(achieved - first_race))

        await ctx.send(embed = embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases = get_aliases('marathon'))
    async def marathon(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args) + 86400, 'races')
        elif len(args) == 1: args += (86400, 'races')
        elif len(args) == 2: args += ('races',)

        if len(args) != 3:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <seconds> <races/points>"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return
        try:
            session_length = float(args[1])
            if session_length <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`seconds` must be a positive number'))
            return

        category = args[2].lower()
        if not category in ['races', 'points']:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format("`category` must be `races/points`"))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM t_{player} ORDER BY t").fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        length = len(user_data)
        if category == 'races':
            cur_min, max_start, max_end = (0,) * 3
            for i in range(0, length):
                if user_data[i][1] - user_data[cur_min][1] >= session_length:
                    if i - cur_min > max_end - max_start:
                        max_start, max_end = cur_min, i
                while user_data[i][1] - user_data[cur_min][1] > session_length:
                    cur_min += 1
            if length - cur_min - 1 > max_end - max_start:
                max_start, max_end = cur_min, length - 1
        elif category == 'points':
            cur_min, max_start, max_end, cur_points, max_points = (0,) * 5
            for i in range(0, length):
                cur_points += user_data[i][4]
                if user_data[i][1] - user_data[cur_min][1] >= session_length:
                    if cur_points > max_points:
                        max_start, max_end, max_points = cur_min, i, cur_points
                while user_data[i][1] - user_data[cur_min][1] > session_length:
                    cur_points -= user_data[cur_min][4]
                    cur_min += 1
            if cur_points + user_data[length - 1][4] > max_points:
                max_start, max_end = cur_min, length - 1

        races, seconds_played, chars_typed, words_typed, points, wpm_sum, wpm_max = (0,) * 7
        wpm_min = 100000
        text_data = load_texts_json()
        for i in range(max_start, max_end):
            races += 1
            cur = user_data[i]
            wpm = cur[3]
            tid = str(cur[2])

            wpm_sum += wpm
            wpm_min = min(wpm, wpm_min)
            wpm_max = max(wpm, wpm_max)

            words = text_data[tid]['word count']
            chars = text_data[tid]['length']
            words_typed += words
            chars_typed += chars
            seconds_played += 12 * chars / wpm
            points += cur[4]
            if cur[4] == 0:
                points += wpm * words / 60

        f_category = {'races': 'Races', 'points': 'Points'}[category]

        max_end -= 1

        embed = discord.Embed(title = (f"{f_category} Marathon Stats for {player} "
                                       f"({seconds_to_text(session_length, True)} period)"),
                              color = discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.set_footer(text = (f"First Race (#{f'{max_start + 1:,}'}): {datetime.datetime.fromtimestamp(user_data[max_start][1]).strftime('%B %-d, %Y, %-I:%M:%S %p')} | "
                                 "(Retroactive points represent the total number of "
                                 "points a user would have gained, before points were introduced in 2017)"))
        embed.add_field(name = 'Races',
                        value = (f"**Total Races:** {f'{races:,}'}\n"
                                 f"**Total Words Typed:** {f'{words_typed:,}'}\n"
                                 f"**Average Words Per Races:** {f'{round(words_typed / races, 2):,}'}\n"
                                 f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
                                 f"**Average Chars Per Race:** {f'{round(chars_typed / races, 2):,}'}\n"
                                 f"**Total Time Spent Racing:** {seconds_to_text(seconds_played)}\n"
                                 f"**Total Time Elapsed:** {seconds_to_text(user_data[max_end][1] - user_data[max_start][1])}\n"
                                 f"**Average Time Per Race:** {seconds_to_text(seconds_played / races)}"),
                        inline = False)
        embed.add_field(name = 'Points (Retroactive Included)',
                        value = (f"**Total Points:** {f'{round(points):,}'}\n"
                                 f"**Average Points Per Race:** {f'{round(points / races, 2):,}'}\n"),
                        inline = False)
        embed.add_field(name = 'Speed',
                        value = (f"**Average (Lagged):** {f'{round(wpm_sum / races, 2):,}'} WPM\n"
                                 f"**Fastest Race:** {f'{wpm_max:,}'} WPM\n"
                                 f"**Slowest Race:** {f'{wpm_min:,}'} WPM"),
                        inline = False)

        await ctx.send(embed = embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases = get_aliases('sessionstats'))
    async def sessionstats(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <seconds>"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return
        try:
            if len(args) == 1:
                session_length = 1800
            else:
                session_length = float(args[1])
            if session_length <= 0:
                raise ValueError
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`seconds` must be a positive number'))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        max_start, max_end, cur_start, cur_end = (0,) * 4
        max_tstart, max_tend, cur_tstart, cur_tend = (0,) * 4
        try:
            user_data = c.execute(f"SELECT t FROM t_{player} ORDER BY t")
            user_data = user_data.fetchall()
            for i in range(1, len(user_data)):
                if user_data[i][0] - user_data[i - 1][0] > session_length:
                    if cur_end - cur_start > max_end - max_start:
                        max_start, max_end = cur_start, cur_end
                    cur_end += 1
                    cur_start = cur_end
                    if user_data[cur_tend][0] - user_data[cur_tstart][0] > \
                    user_data[max_tend][0] - user_data[max_tstart][0]:
                        max_tstart, max_tend = cur_tstart, cur_tend
                    cur_tend += 1
                    cur_tstart = cur_tend
                else:
                    cur_end += 1
                    cur_tend += 1
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        embed = discord.Embed(title = f"Session Stats for {player} ({seconds_to_text(session_length, True)} interval)",
                              color = discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.add_field(name = 'Highest Race Session',
                        value = (f"{f'{max_end - max_start + 1:,}'} races in "
                                 f"{seconds_to_text(user_data[max_end][0] - user_data[max_start][0])}"))
        embed.add_field(name = 'Longest Session',
                        value = (f"{f'{max_tend - max_tstart + 1:,}'} races in "
                                 f"{seconds_to_text(user_data[max_tend][0] - user_data[max_tstart][0])}"))

        await ctx.send(embed = embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases = get_aliases('fastestcompletion'))
    async def fastestcompletion(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 1: args = check_account(user_id)(args) + ('races',)
        elif len(args) == 2: args += ('races',)

        if len(args) != 3:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [num] <races/points>"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return
        try:
            num = float(args[1])
            if num <= 0 or num % 1 != 0:
                raise ValueError
            num = int(num)
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`num` must be a positive number'))
            return

        category = args[2].lower()
        if not category in ['races', 'points']:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`category` must be `races/points`'))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM t_{player} ORDER BY t").fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        try:
            if category == 'races':
                user_data[num - 1]
        except IndexError:
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .incorrect_format("`num` must not exceed user's race count"))
            return

        length = len(user_data)
        if category == 'races':
            min_start, min_end, cur_start, = 0, num - 1, 0
            for i in range(num, length):
                cur_start += 1
                if user_data[i][1] - user_data[cur_start][1] <\
                user_data[min_end][1] - user_data[min_start][1]:
                    min_start, min_end = cur_start, i

        elif category == 'points':
            min_start, cur_start, cur_end, cur_points = (0,) * 4
            min_end = length - 1
            exceeds_point_count = True
            for i in range(0, length):
                cur_points += user_data[i][4]
                if cur_points >= num:
                    exceeds_point_count = False
                    cur_end = i
                    while cur_points - user_data[cur_start][4] >= num:
                        cur_points -= user_data[cur_start][4]
                        cur_start += 1
                    if user_data[cur_end][1] - user_data[cur_start][1] <\
                    user_data[min_end][1] - user_data[min_start][1]:
                        min_start, min_end = cur_start, cur_end

            if exceeds_point_count:
                await ctx.send(content = f"<@{user_id}>",
                                embed = Error(ctx, ctx.message)
                                        .incorrect_format("`num` must not exceed user's point count"))
                return

        races, seconds_played, chars_typed, words_typed, points, wpm_sum, wpm_max = (0,) * 7
        wpm_min = 100000
        tids = []
        text_data = load_texts_json()
        for i in range(min_start, min_end + 1):
            races += 1
            cur = user_data[i]
            wpm = cur[3]
            tid = str(cur[2])
            tids.append(tid)

            wpm_sum += wpm
            if wpm < wpm_min:
                wpm_min = wpm
            if wpm > wpm_max:
                wpm_max = wpm

            words = text_data[tid]['word count']
            chars = text_data[tid]['length']
            words_typed += words
            chars_typed += chars
            seconds_played += 12 * chars / wpm
            points += cur[4]
            if cur[4] == 0:
                points += wpm * words / 60

        f_category = {'races': 'Races', 'points': 'Points'}[category]

        embed = discord.Embed(title = f"{player}'s Fastest Time to Complete {f'{num:,}'} {f_category}",
                              color = discord.Color(MAIN_COLOR),
                              description = f"**Took:** {seconds_to_text(user_data[min_end][1] - user_data[min_start][1])}")
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.set_footer(text = (f"First Race (#{f'{min_start + 1:,}'}): {datetime.datetime.fromtimestamp(user_data[min_start][1]).strftime('%B %-d, %Y, %-I:%M:%S %p')} | "
                                 "(Retroactive points represent the total number of "
                                 "points a user would have gained, before points were introduced in 2017)"))
        embed.add_field(name = 'Races',
                        value = (f"**Total Races:** {f'{min_end - min_start + 1:,}'}\n"
                                 f"**Total Words Typed:** {f'{words_typed:,}'}\n"
                                 f"**Average Words Per Races:** {f'{round(words_typed / races, 2):,}'}\n"
                                 f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
                                 f"**Average Chars Per Race:** {f'{round(chars_typed / races, 2):,}'}\n"
                                 f"**Total Time Spent Racing:** {seconds_to_text(seconds_played)}\n"
                                 f"**Total Time Elapsed:** {seconds_to_text(user_data[min_end][1] - user_data[min_start][1])}\n"
                                 f"**Average Time Per Race:** {seconds_to_text(seconds_played / races)}"),
                        inline = False)
        embed.add_field(name = 'Points (Retroactive Included)',
                        value = (f"**Total Points:** {f'{round(points):,}'}\n"
                                 f"**Average Points Per Race:** {f'{round(points / races, 2):,}'}\n"),
                        inline = False)
        embed.add_field(name = 'Speed',
                        value = (f"**Average (Lagged):** {f'{round(wpm_sum / races, 2):,}'} WPM\n"
                                 f"**Fastest Race:** {f'{wpm_max:,}'} WPM\n"
                                 f"**Slowest Race:** {f'{wpm_min:,}'} WPM"),
                        inline = False)
        embed.add_field(name = 'Quotes',
                        value = f"**Number of Unique Quotes:** {f'{len(set(tids)):,}'}",
                        inline = False)

        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(FullStats(bot))
