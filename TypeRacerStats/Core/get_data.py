import csv
import datetime
import os
import sqlite3
import sys
import time
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_ADMIN_IDS, MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH, TEMPORARY_DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls


class GetData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 7200, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('getdata'))
    async def getdata(self, ctx, *args):
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

        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
            total_races = int(api_response[0][0]['gn'])
        except:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist or has no races")))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT * FROM t_{player} ORDER BY t DESC LIMIT 1")
            last_race = user_data.fetchone()
            last_race_timestamp = last_race[1]
            races_remaining = total_races - last_race[0]
        except sqlite3.OperationalError:
            races_remaining = total_races
            if races_remaining == 0:
                conn.close()
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx,
                                           ctx.message).missing_information(
                                               f"{player} has no races"))
                return
            else:
                if races_remaining > 10000 and not user_id in BOT_ADMIN_IDS:
                    pass
                else:
                    c.execute(
                        f"CREATE TABLE t_{player} (gn integer PRIMARY KEY, t, tid, wpm, pts)"
                    )
        if races_remaining > 10000 and not user_id in BOT_ADMIN_IDS:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).lacking_permissions(
                               ('Data request exceeds 10,000 races. '
                                'Have a bot admin run the command.')))
            return
        if races_remaining == 0:
            conn.close()
            await ctx.send(embed=discord.Embed(
                title='Data Request',
                color=discord.Color(MAIN_COLOR),
                description=(f"{player}'s data successfully created/updated\n"
                             '0 races added')))
            return

        start_ = time.time()
        await ctx.send(embed=discord.Embed(
            title='Data Request',
            color=discord.Color(MAIN_COLOR),
            description=
            ('Request successful\n'
             f"Estimated download time: {seconds_to_text(0.005125 * races_remaining + 0.5)}"
             )))

        try:
            data = await fetch_data(player, 'play', last_race_timestamp + 0.01,
                                    time.time())
        except UnboundLocalError:
            data = await fetch_data(player, 'play', 1204243200, time.time())
        c.executemany(f"INSERT INTO t_{player} VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()

        length = round(time.time() - start_, 3)
        await ctx.send(
            content=f"<@{user_id}>",
            embed=discord.Embed(
                title='Data Request',
                color=discord.Color(MAIN_COLOR),
                description=(f"{player}'s data successfully created/updated\n"
                             f"{f'{races_remaining:,}'} races added\n"
                             f"Took {seconds_to_text(length)}")))
        return

    @commands.cooldown(5, 7200, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('today'))
    async def today(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0 or (len(args) == 1 and '-' in args[0]):
            args = check_account(user_id)(args)

        is_today = True
        today_timestamp = (datetime.datetime.utcnow().date() -
                           datetime.date(1970, 1, 1)).total_seconds()

        if ctx.invoked_with.lower() in ['yesterday', 'yday', 'yd']:
            today_timestamp = (datetime.datetime.utcnow().date() -
                               datetime.date(1970, 1, 2)).total_seconds()
            is_today = False
            if len(args) > 1 or len(args) == 0:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(
                        ctx,
                        ctx.message).parameters(f"{ctx.invoked_with} [user]"))
                return

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <yyyy-mm-dd>"))
            return

        if len(args) == 2:
            try:
                today_timestamp_temp = (
                    datetime.datetime.strptime(args[1], "%Y-%m-%d").date() -
                    datetime.date(1970, 1, 1)).total_seconds()
                if today_timestamp_temp != today_timestamp: is_today = False
                if today_timestamp_temp > today_timestamp:
                    await ctx.send(content=f"<@{user_id}>",
                                   embed=Error(
                                       ctx, ctx.message).incorrect_format(
                                           '`date` must not exceed today'))
                    return
                today_timestamp = today_timestamp_temp
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   '`date` must be in the yyyy-mm-dd format'))
                return

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
            total_races = int(api_response[0][0]['gn'])
        except:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist or has no races")))
            return

        file_name = f"t_{player}_play_{today_timestamp}_{today_timestamp + 86400}".replace(
            '.', '_')
        conn = sqlite3.connect(TEMPORARY_DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(
                f"SELECT * FROM {file_name} ORDER BY t DESC LIMIT 1")
            last_race = user_data.fetchone()
            if last_race:
                last_race_timestamp = last_race[1]
                races_remaining = total_races - last_race[0]
            else:
                races_remaining = total_races
        except sqlite3.OperationalError:
            races_remaining = total_races
            if races_remaining == 0:
                conn.close()
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx,
                                           ctx.message).missing_information(
                                               f"{player} has no races"))
            else:
                c.execute(
                    f"CREATE TABLE {file_name} (gn integer PRIMARY KEY, t, tid, wpm, pts)"
                )

        try:
            data = await fetch_data(player, 'play', last_race_timestamp + 0.01,
                                    today_timestamp + 86400)
        except UnboundLocalError:
            data = await fetch_data(player, 'play', today_timestamp,
                                    today_timestamp + 86400)

        date = datetime.datetime.fromtimestamp(today_timestamp).strftime(
            '%B %-d, %Y')

        user_is_leader = await self.check_if_leader(player, 'day')
        if user_is_leader and is_today:
            embed = discord.Embed(
                title=f"{date} Stats for {player}",
                color=discord.Color(MAIN_COLOR),
                url=Urls().user(player, 'play'),
                description=':crown: **Daily Leader** :crown:')
        else:
            embed = discord.Embed(title=f"{date} Stats for {player}",
                                  color=discord.Color(MAIN_COLOR),
                                  url=Urls().user(player, 'play'))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        if data:
            c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)",
                          data)

        conn.commit()
        data = c.execute(f"SELECT * FROM {file_name}").fetchall()
        conn.close()
        if not data:
            embed.add_field(name='Average Speed', value='—')
            embed.add_field(name='Races', value='0')
            embed.add_field(name='Points', value='0')
            await ctx.send(embed=embed)
            return

        texts_data = load_texts_json()
        races, wpm, points, seconds_played, chars_typed, words_typed = (
            0, ) * 6
        fastest_race, slowest_race = (data[0][3], data[0][0]), (data[0][3],
                                                                data[0][0])
        for row in data:
            races += 1
            race_text_id = str(row[2])
            race_wpm = row[3]
            wpm += race_wpm
            if race_wpm > fastest_race[0]: fastest_race = (race_wpm, row[0])
            if race_wpm < slowest_race[0]: slowest_race = (race_wpm, row[0])
            points += row[4]
            word_count = texts_data.get(race_text_id, {"word count": 0})['word count']
            race_text_length = texts_data.get(race_text_id, {"length": 0})['length']
            seconds_played += 12 * race_text_length / race_wpm
            chars_typed += race_text_length
            words_typed += word_count

        average_wpm = round(wpm / races, 2)
        total_points = round(points)
        embed.add_field(
            name='Summary',
            value=
            (f"**Average Speed:** {average_wpm} WPM "
             f"([{slowest_race[0]}]({Urls().result(player, slowest_race[1], 'play')})"
             f" - [{fastest_race[0]}]({Urls().result(player, fastest_race[1], 'play')}))\n"
             f"**Total Races:** {f'{races:,}'}\n"
             f"**Total Points:** {f'{total_points:,}'} ({f'{round(points / races, 2)}'} points/race)"
             ),
            inline=False)
        embed.add_field(
            name='Details',
            value=
            (f"**Total Words Typed:** {f'{words_typed:,}'}\n"
             f"**Average Words Per Race:** {round(words_typed / races, 2)}\n"
             f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
             f"**Average Chars Per Race:** {round(chars_typed / races, 2)}\n"
             f"**Total Time Spent Racing:** {seconds_to_text(seconds_played)}\n"
             f"**Average Time Per Race:** {seconds_to_text(seconds_played / races)}"
             ),
            inline=False)

        await ctx.send(embed=embed)
        return

    @commands.cooldown(5, 7200, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('week') + ['month'] +
                      get_aliases('month') + ['year'] + get_aliases('year'))
    async def week(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        week = ctx.invoked_with in ['week'] + get_aliases('week')
        month = ctx.invoked_with in ['month'] + get_aliases('month')
        year = ctx.invoked_with in ['year'] + get_aliases('year')

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <date>"))
            return

        same_day = True
        today = datetime.datetime.utcnow().date()
        if len(args) == 2:
            try:
                parse_string = '%Y'
                date_format = len(args[1].split('-'))
                if date_format == 1:
                    pass
                elif date_format == 2:
                    parse_string += '-%m'
                elif date_format == 3:
                    parse_string += '-%m-%d'
                else:
                    raise ValueError

                today_temp = datetime.datetime.strptime(args[1],
                                                        parse_string).date()
                if today_temp != today: same_day = False
                if today_temp > today:
                    await ctx.send(content=f"<@{user_id}>",
                                   embed=Error(
                                       ctx, ctx.message).incorrect_format(
                                           '`date` must not exceed today'))
                    return
                today = today_temp
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   '`date` must be in the yyyy-mm-dd format'))
                return

        if week:
            normalizer = today.isocalendar()[2]
            start_time = today - datetime.timedelta(days=normalizer - 1)
            end_time = today + datetime.timedelta(days=7 - normalizer)
            formatted_sort = 'Weekly'
        elif month:
            start_time = today.replace(day=1)
            end_time = (today.replace(day=1) + datetime.timedelta(days=32)
                        ).replace(day=1) - datetime.timedelta(days=1)
            formatted_sort = 'Monthly'
        elif year:
            start_time = datetime.date(today.year, 1, 1)
            end_time = datetime.date(today.year, 12, 31)
            formatted_sort = 'Yearly'

        delta_start = start_time
        delta = end_time - start_time
        start_time = (start_time - datetime.date(1970, 1, 1)).total_seconds()
        end_time = (end_time - datetime.date(1970, 1, 1)).total_seconds()
        end_time += 86400

        player = get_player(user_id, args[0])
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

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

        data = await fetch_data(player, 'play', last_race_timestamp + 0.01,
                                end_time)

        if data:
            c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)",
                          data)

        conn.commit()
        data = c.execute(
            f"""SELECT * FROM {file_name}
                             WHERE t > ? AND t < ?""", (
                start_time,
                end_time,
            )).fetchall()
        conn.close()

        if week:
            day_one = datetime.datetime.fromtimestamp(start_time).day
            day_two = datetime.datetime.fromtimestamp(end_time - 86400).day
            if day_one > day_two: format_string = '%B %-d, %Y'
            else: format_string = '%-d, %Y'
            title = (
                f"Weekly ({datetime.datetime.fromtimestamp(start_time).strftime('%B %-d')}—"
                f"{datetime.datetime.fromtimestamp(end_time - 86400).strftime(format_string)})"
            )
        elif month:
            title = f"Monthly ({datetime.datetime.fromtimestamp(start_time).strftime('%B %Y')})"
        elif year:
            title = f"Yearly ({datetime.datetime.fromtimestamp(start_time).strftime('%Y')})"

        title += f" Stats for {player}"
        user_is_leader = await self.check_if_leader(
            player,
            formatted_sort.lower()[:-2])
        if user_is_leader and same_day:
            embed = discord.Embed(
                title=title,
                color=discord.Color(MAIN_COLOR),
                url=Urls().user(player, 'play'),
                description=f":crown: **{formatted_sort} Leader** :crown:")
        else:
            embed = discord.Embed(title=title,
                                  color=discord.Color(MAIN_COLOR),
                                  url=Urls().user(player, 'play'))
        embed.set_thumbnail(url=Urls().thumbnail(player))

        if not data:
            embed.add_field(name='Average Speed', value='—')
            embed.add_field(name='Races', value='0')
            embed.add_field(name='Points', value='0')
            await ctx.send(embed=embed)
            return

        texts_length = load_texts_json()

        csv_dict = {}
        for i in range(delta.days + 1):
            csv_dict.update({
                (delta_start + datetime.timedelta(days=i)).isoformat(): {
                    'races': 0,
                    'words_typed': 0,
                    'chars_typed': 0,
                    'points': 0,
                    'time_spent': 0,
                    'average_wpm': 0,
                    'best_wpm': 0,
                    'worst_wpm': 0
                }
            })

        races, words_typed, chars_typed, points, retro, time_spent = (0, ) * 6
        wpm_total, wpm_best, wpm_worst = (0, ) * 3
        for row in data:
            date = datetime.datetime.fromtimestamp(row[1]).date().isoformat()
            text_id = str(row[2])
            wpm = row[3]
            races += 1
            words_typed_ = texts_length.get(text_id, {"word count": 0})['word count']
            chars_typed_ = texts_length.get(text_id, {"length": 0})['length']
            words_typed += words_typed_
            chars_typed += chars_typed_

            wpm_total += wpm
            if not wpm_best or wpm_best < wpm: wpm_best = wpm
            if not wpm_worst or wpm_worst > wpm: wpm_worst = wpm

            csv_day = csv_dict[date]
            csv_day['races'] += 1
            csv_day['words_typed'] += words_typed_
            csv_day['chars_typed'] += chars_typed_
            csv_day['average_wpm'] = (csv_day['average_wpm'] *\
                                     (csv_day['races'] - 1) + wpm) /\
                                     csv_day['races']
            if not csv_day['best_wpm'] or csv_day['best_wpm'] < wpm:
                csv_day['best_wpm'] = wpm
            if not csv_day['worst_wpm'] or csv_day['worst_wpm'] > wpm:
                csv_day['worst_wpm'] = wpm

            if row[4] == 0:
                retro_ = row[3] / 60 * texts_length.get(text_id, {"word count": 0})['word count']
                retro += retro_
                csv_day['points'] += row[4]
            else:
                points += row[4]
                csv_day['points'] += row[4]
            try:
                time_spent_ = 12 * texts_length.get(text_id, {"length": 0})['length'] / row[3]
                time_spent += time_spent_
                csv_day['time_spent'] += time_spent_
            except ZeroDivisionError:
                races -= 1
                csv_day['races'] -= 1
                pass

        today = time.time() if time.time() < end_time else end_time
        num_days = (today - start_time) / 86400

        retro_text = f"**Retroactive Points:** {f'{round(retro):,}'}\n" if retro else ""

        if retro_text:
            embed.set_footer(text=(
                'Retroactive points represent the total number of points '
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
             f"**Average Chars Per Race: **{f'{round(chars_typed / races, 2):,}'}"
             ))
        embed.add_field(
            name='Points',
            value=
            (f"**Points:** {f'{round(points):,}'}\n"
             f"**Average Daily Points:** {f'{round(points / num_days, 2):,}'}\n"
             f"**Average Points Per Race:** {f'{round((points + retro) / races, 2):,}'}\n"
             f"{retro_text}"
             f"**Total Points:** {f'{round(points + retro):,}'}"))
        embed.add_field(
            name='Speed',
            value=
            (f"**Average (Lagged):** {f'{round(wpm_total / races, 2):,}'} WPM\n"
             f"**Fastest Race:** {f'{wpm_best:,}'} WPM\n"
             f"**Slowest Race:** {f'{wpm_worst:,}'} WPM"),
            inline=False)
        embed.add_field(
            name='Time',
            value=
            (f"**Total Time Spent Racing:** {seconds_to_text(time_spent)}\n"
             f"**Average Daily Time:** {seconds_to_text(time_spent / num_days)}\n"
             f"**Average Time Per Race:** {seconds_to_text(time_spent / races)}"
             ))

        if ctx.invoked_with[-1] == '*':
            csv_data = [['date'] + list(next(iter(csv_dict.values())).keys())]
            for key, value in csv_dict.items():
                values = [round(i, 2) for i in list(value.values())]
                csv_data.append([key] + values)

            with open('temporary.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(csv_data)

            title_ = title.split(' (')
            await ctx.send(file=discord.File(
                'temporary.csv',
                f"{player}_{title_[0].lower()}_{title_[1].split(')')[0].lower()}.csv"
            ),
                           embed=embed)
            os.remove('temporary.csv')
            return

        await ctx.send(embed=embed)
        return

    async def check_if_leader(self, user, kind):
        urls = [Urls().get_competition(1, kind, 'points', 'play')]
        competition = await fetch(urls, 'json')
        competition = competition[0]

        return competition[0][1]['typeracerUid'][3:] == user


def setup(bot):
    bot.add_cog(GetData(bot))
