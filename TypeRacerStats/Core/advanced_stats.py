import datetime
import sqlite3
import sys
import time
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, seconds_to_text
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.texts import load_texts_large, load_texts_json
from TypeRacerStats.Core.Common.urls import Urls


class AdvancedStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(20, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('top') + get_aliases('worst') +
                      ['worst'])
    async def top(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) <= 1: args = check_account(user_id)(args)

        if len(args) == 1: args += ('wpm', )

        if len(args) != 2:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] [wpm/points/weightedwpm]"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        categories = ['wpm', 'points', 'weightedwpm']

        if not args[1].lower() in categories:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               '`category` must be `wpm/points/weightedwpm`'))
            return

        if args[1].lower() == 'points':
            category = 'pts'
        elif args[1].lower() == 'wpm':
            category = 'wpm'
        else:
            category = 'weightedwpm'

        texts_length = load_texts_json()
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            if ctx.invoked_with in ['top'] + get_aliases('top'):
                order_by, reverse = 'DESC', True
            else:
                order_by, reverse = 'ASC', False
            if category != 'weightedwpm':
                user_data = c.execute(
                    f"SELECT * FROM t_{player} ORDER BY {category} {order_by} LIMIT 10"
                )
                user_data = user_data.fetchall()
            else:
                raw_data = c.execute(f"SELECT * FROM t_{player}")
                user_data = sorted(
                    raw_data,
                    key=lambda x: x[3] * texts_length[str(x[2])]['length'],
                    reverse=reverse)[:10]
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        embed = discord.Embed(
            title=
            f"{player}'s {['Worst', 'Top'][reverse]} {len(user_data)} Races (Lagged)",
            color=discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        formatted_category = {
            'pts': 'points',
            'wpm': 'WPM',
            'weightedwpm': 'WPM'
        }[category]
        texts = load_texts_large()
        for i, race in enumerate(user_data):
            value = f"{texts[str(race[2])]} [:cinema:]({Urls().result(player, race[0], 'play')})"
            if formatted_category == 'points':
                name = f"{i + 1}. {race[4]} {formatted_category} (Race #{f'{race[0]:,}'}, Text ID: {race[2]})"
            else:
                name = f"{i + 1}. {race[3]} {formatted_category} (Race #{f'{race[0]:,}'}, Text ID: {race[2]})"
            embed.add_field(name=name, value=value, inline=False)
            if category == 'weightedwpm':
                embed.set_footer(
                    text='Sorted by weighted WPM (text_length • wpm)')
        await ctx.send(embed=embed)
        return

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(20, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('racedetails'))
    async def racedetails(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        texts_length = load_texts_json()
        races, words_typed, chars_typed, points, retro, time_spent, total_wpm = (
            0, ) * 7
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        try:
            user_data = c.execute(f"SELECT * FROM t_{player}")
            first_race = user_data.fetchone()
            first_point_race = 0
            text_id = str(first_race[2])
            races += 1
            total_wpm += first_race[3]
            words_typed += texts_length.get(text_id, {"word count": 0})['word count']
            chars_typed += texts_length.get(text_id, {"length": 0})['length']
            fastest_race, slowest_race = (first_race[3],
                                          first_race[0]), (first_race[3],
                                                           first_race[0])
            try:
                time_spent += 12 * texts_length.get(text_id, {"length": 0})['length'] / first_race[3]
            except ZeroDivisionError:
                pass
            if first_race[4] == 0:
                retro += first_race[3] / 60 * texts_length.get(text_id, {"word count": 0})['word count']
            else:
                if not first_point_race:
                    first_point_race = first_race[1]
                points += first_race[4]
            first_race = first_race[1]
            for row in user_data:
                race_wpm = row[3]
                total_wpm += race_wpm
                if race_wpm > fastest_race[0]:
                    fastest_race = (race_wpm, row[0])
                if race_wpm < slowest_race[0]:
                    slowest_race = (race_wpm, row[0])
                text_id = str(row[2])
                races += 1
                words_typed += texts_length.get(text_id, {'word count': 0})['word count']
                chars_typed += texts_length.get(text_id, {'length': 0})['length']
                if row[4] == 0:
                    retro += race_wpm / 60 * texts_length.get(text_id, {'word count': 0})['word count']
                else:
                    if not first_point_race:
                        first_point_race = row[1]
                    points += row[4]
                try:
                    time_spent += 12 * texts_length.get(text_id, {'length': 0})['length'] / race_wpm
                except ZeroDivisionError:
                    races -= 1
                    pass
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        today = time.time()
        num_days = (today - first_race) / 86400
        num_point_days = (today - first_point_race) / 86400

        embed = discord.Embed(title=f"Race Details for {player}",
                              color=discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))
        embed.set_footer(
            text=('Retroactive points represent the total number of points '
                  'a user would have gained, before points were introduced '
                  'in 2017'))

        embed.add_field(
            name='Races',
            value=
            (f"**Total Races:** {f'{races:,}'}\n"
             f"**Average Daily Races:** {f'{round(races / num_days, 2):,}'}\n"
             f"**Total Words Typed:** {f'{words_typed:,}'}\n"
             f"**Average Words Per Race:** {f'{round(words_typed / races, 2):,}'}\n"
             f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
             f"**Average Chars Per Race: **{f'{round(chars_typed / races, 2):,}'}\n"
             ))
        embed.add_field(
            name='Points',
            value=
            (f"**Current Points:** {f'{round(points):,}'}\n"
             f"**Average Daily Points:** {f'{round(points / num_point_days, 2):,}'}\n"
             f"**Average Points Per Race:** {f'{round((points + retro) / races, 2):,}'}\n"
             f"**Retroactive Points:** {f'{round(retro):,}'}\n"
             f"**Total Points:** {f'{round(points + retro):,}'}"))
        embed.add_field(
            name='Speed',
            value=
            (f"**Average (Lagged):** {f'{round(total_wpm / races, 2):,}'} WPM\n"
             f"**Fastest Race:** {f'{fastest_race[0]:,}'} WPM "
             f"[:cinema:]({Urls().result(player, fastest_race[1], 'play')})\n"
             f"**Slowest Race:** {f'{slowest_race[0]:,}'} WPM "
             f"[:cinema:]({Urls().result(player, slowest_race[1], 'play')})"),
            inline=False)
        embed.add_field(
            name='Time',
            value=
            (f"**Total Time Spent Racing:** {seconds_to_text(time_spent)}\n"
             f"**Average Daily Time:** {seconds_to_text(time_spent / num_days)}\n"
             f"**Average Time Per Race:** {seconds_to_text(time_spent / races)}"
             ))
        await ctx.send(embed=embed)
        return

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(20, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('longestbreak'))
    async def longestbreak(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <seconds>"))
            return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        duration = 0
        if len(args) == 2:
            try:
                duration = int(args[1])
                if duration <= 0 or duration > 1_000_000_000_000:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).incorrect_format(
                        '`seconds` must be a positive number less than 1,000,000,000,000'
                    ))
                return

        count, longest_break = (0, ) * 2
        longest_break_gn, longest_break_time = (1, ) * 2
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT t, gn FROM t_{player} ORDER BY t")
            previous_time, previous_gn = user_data.fetchone()
            for row in user_data:
                break_ = row[0] - previous_time
                if break_ >= duration: count += 1
                if break_ > longest_break:
                    longest_break = break_
                    longest_break_gn = previous_gn
                    longest_break_time = previous_time
                previous_time, previous_gn = row
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        break_ = time.time() - previous_time
        on_break = break_ > longest_break
        if break_ >= duration: count += 1
        if on_break:
            longest_break = break_
            longest_break_gn = previous_gn
            longest_break_time = previous_time

        if duration:
            await ctx.send(embed=discord.Embed(
                color=discord.Color(MAIN_COLOR),
                description=
                f"**{player}** had **{f'{count:,}'}** breaks longer than **{seconds_to_text(duration)}**"
            ))
            return

        embed = discord.Embed(
            color=discord.Color(MAIN_COLOR),
            description=
            (f"**{player}**'s longest break was **{seconds_to_text(longest_break)}**, "
             f"and it started on race **{f'{longest_break_gn:,}'}** "
             f" / **{datetime.datetime.fromtimestamp(longest_break_time).strftime('%B %-d, %Y, %-I:%M:%S %p')}**"
             ))
        if on_break: embed.set_footer(text='Currently on break')

        await ctx.send(embed=embed)
        return


def setup(bot):
    bot.add_cog(AdvancedStats(bot))
