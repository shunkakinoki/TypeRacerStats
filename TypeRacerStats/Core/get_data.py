import datetime
import sys
import time
import discord
from discord.ext import commands
import sqlite3
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_ADMIN_IDS
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.file_paths import TEMPORARY_DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.urls import Urls

class GetData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 7200, commands.BucketType.default)
    @commands.command(aliases = get_aliases('getdata'))
    async def getdata(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0]
        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
            total_races = int(api_response[0][0]['gn'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information('`user` must be a TypeRacer username'))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM t_{player} ORDER BY gn DESC LIMIT 1")
            last_race = user_data.fetchone()
            last_race_timestamp = last_race[1]
            races_remaining = total_races - last_race[0]
        except sqlite3.OperationalError:
            races_remaining = total_races
            if races_remaining == 0:
                conn.close()
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .missing_information(f"{player} has no races"))
                return
            else:
                c.execute(f"CREATE TABLE t_{player} (gn integer PRIMARY KEY, t, tid, wpm, pts)")
        if races_remaining > 5000 and not user_id in BOT_ADMIN_IDS:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .lacking_permissions(('Data request exceeds 5,000 races. '
                                                         'Have a bot admin run the command.')))
            return
        if races_remaining == 0:
            await ctx.send(embed = discord.Embed(title = 'Data Request',
                                                color = discord.Color(MAIN_COLOR),
                                                description = (f"{player}'s data successfully created/updated\n"
                                                               '0 races added')))
            return

        start_ = time.time()
        await ctx.send(embed = discord.Embed(title = 'Data Request',
                                             color = discord.Color(MAIN_COLOR),
                                             description = ('Request successful\n'
                                                            f"Estimated download time: {seconds_to_text(0.00441911 * races_remaining + 0.75)}")))

        try:
            data = await fetch_data(player, 'play', last_race_timestamp + 0.01)
        except UnboundLocalError:
            data = await fetch_data(player, 'play')
        c.executemany(f"INSERT INTO {player} VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()

        length = round(time.time() - start_, 3)
        await ctx.send(content = f"<@{user_id}>",
                       embed = discord.Embed(title = 'Data Request',
                                             color = discord.Color(MAIN_COLOR),
                                             description = (f"{player}'s data successfully created/updated\n"
                                                            f"{f'{races_remaining:,}'} races added\n"
                                                            f"Took {seconds_to_text(length)}")))
        return

    @commands.cooldown(5, 7200, commands.BucketType.default)
    @commands.command(aliases = get_aliases('today'))
    async def today(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)
        today_timestamp = (datetime.datetime.utcnow().date() - datetime.date(1970, 1, 1)).total_seconds()

        if len(args) == 2:
            try:
                today_timestamp_temp = (datetime.datetime.strptime(args[1], "%Y-%m-%d").date() - datetime.date(1970, 1, 1)).total_seconds()
                if today_timestamp_temp > today_timestamp:
                    await ctx.send(content = f"<@{user_id}>",
                                   embed = Error(ctx, ctx.message)
                                           .incorrect_format('`date` must not exceed today'))
                    return
                today_timestamp = today_timestamp_temp
            except ValueError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`date` must be in the yyyy-mm-dd format'))
                return

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <yyyy-mm-dd>"))
            return

        player = args[0]
        urls = [Urls().get_races(player, 'play', 1)]
        try:
            api_response = await fetch(urls, 'json')
            total_races = int(api_response[0][0]['gn'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information('`user` must be a TypeRacer username'))
            return

        file_name = f"t_{player}_{today_timestamp}_{today_timestamp + 86400}".replace('.', '_')
        conn = sqlite3.connect(TEMPORARY_DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM {file_name} ORDER BY gn DESC LIMIT 1")
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
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .missing_information(f"{player} has no races"))
            else:
                c.execute(f"CREATE TABLE {file_name} (gn, t, tid, wpm, pts)")
        if races_remaining > 5000 and not user_id in BOT_ADMIN_IDS:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .lacking_permissions(('Data request exceeds 5,000 races. '
                                                         'Have a bot admin run the command.')))
            return

        try:
            data = await fetch_data(player, 'play', last_race_timestamp + 0.01, today_timestamp + 86400)
        except UnboundLocalError:
            data = await fetch_data(player, 'play', today_timestamp, today_timestamp + 86400)
    
        date = datetime.datetime.fromtimestamp(today_timestamp).strftime('%B %d, %Y')
        embed = discord.Embed(title = f"{date} Stats for {player}",
                              color = discord.Color(MAIN_COLOR),
                              url = Urls().user(player, 'play'))
        embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")

        if data:
            c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)", data)

        conn.commit()
        data = c.execute(f"SELECT * FROM {file_name}").fetchall()
        if not data:
            embed.add_field(name = 'Average Speed', value = '—')
            embed.add_field(name = 'Races', value = '0')
            embed.add_field(name = 'Points', value = '0')
            await ctx.send(embed=embed)
            return
        conn.close()


        texts_data = load_texts_json()
        races, wpm, points, seconds_played, chars_typed, words_typed = (0,) * 6
        for row in data:
            races += 1
            race_text_id = str(row[2])
            race_wpm = row[3]; wpm += race_wpm
            points += row[4]
            word_count = texts_data[race_text_id]['word count']
            race_text_length = texts_data[race_text_id]['length']
            seconds_played += 12 * race_text_length / race_wpm
            chars_typed += race_text_length
            words_typed += word_count
        
        average_wpm = round(wpm / races, 2)
        total_points = round(points)
        embed.add_field(name = 'Summary',
                        value = (f"**Average Speed:** {average_wpm} WPM\n"
                                 f"**Total Races:** {f'{races:,}'}\n"
                                 f"**Total Points:** {f'{total_points:,}'} ({f'{round(points / races, 2)}'} points/race)"),
                                 inline = False)
        embed.add_field(name = 'Details',
                        value = (f"**Total Words Typed:** {f'{words_typed:,}'}\n"
                                 f"**Average Words Per Race:** {round(words_typed / races, 2)}\n"
                                 f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
                                 f"**Average Chars Per Race:** {round(chars_typed / races, 2)}\n"
                                 f"**Total Time Spent Racing:** {seconds_to_text(seconds_played)}\n"
                                 f"**Average Time Per Race:** {seconds_to_text(seconds_played / races)}"),
                        inline = False)
        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(GetData(bot))
