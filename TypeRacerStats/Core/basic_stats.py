import datetime
import json
import sqlite3
import sys
import time
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR, NUMBERS
from TypeRacerStats.file_paths import TEMPORARY_DATABASE_PATH, TOPTENS_FILE_PATH
from TypeRacerStats.Core.Common.accounts import account_information, check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import href_universe, seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.urls import Urls

class BasicStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.command(aliases = get_aliases('stats'))
    async def stats(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()
        urls = [Urls().get_user(player, universe)]
        try:
            user_api = await fetch(urls, 'json')
            user_api = user_api[0]
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                   "doesn't exist")))
            return

        country = f":flag_{user_api['country']}: " if user_api['country'] else ''
        name = user_api['name'] if user_api['name'] else ''
        name += user_api['lastName'] if user_api['lastName'] else ''
        premium = 'Premium' if user_api['premium'] else 'Basic'
        try:
            banned = user_api['tstats']['disqualified']
            banned = '' if banned == 'false' or not banned else '\n**Status:** Banned'
        except KeyError:
            banned = ''

        urls = [[Urls().trd_user(player, universe), 'json']]
        try:
            trd_user_api = (await fetch(urls, 'json'))[0]
            textbests = round(float(trd_user_api['account']['wpm_textbests']), 2)
            textsraced = trd_user_api['account']['texts_raced']
            extra_stats = (f"**Text Bests: **{textbests} WPM\n"
                           f"**Texts Typed: **{textsraced}\n")
        except:
            textbests, textsraced, extra_stats = ('',) * 3

        urls = [Urls().user(player, universe)]
        try:
            response = await fetch(urls, 'text')
            response = response[0]
            soup = BeautifulSoup(response, 'html.parser')
            rows = soup.select("table[class='profileDetailsTable']")[0].select('tr')
            medal_count = 0
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2: continue
                if cells[0].text.strip() == 'Racing Since':
                    date_joined = cells[1].text.strip()
                if cells[0].text.strip() == 'Awards':
                    medal_count = len(cells[1].select('a'))
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                                         "doesn't exist")))
            return

        if banned:
            color = 0xe0001a
        else:
            color = MAIN_COLOR

        embed = discord.Embed(title = f"{country}{player}",
                              colour = discord.Colour(color),
                              description = f"**Universe:** {href_universe(universe)}",
                              url = urls[0])
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.add_field(name = "General",
                        value = (f"**Name:** {name}\n"
                                 f"**Joined: **{date_joined}\n"
                                 f"**Membership: **{premium}{banned}"),
                        inline = False)
        embed.add_field(name = "Stats",
                        value = (f"""**Races: **{f"{user_api['tstats']['cg']:,}"}\n"""
                                 f"""**Races Won: **{f"{user_api['tstats']['gamesWon']:,}"}\n"""
                                 f"""**Points: **{f"{round(user_api['tstats']['points']):,}"}\n"""
                                 f"""**Full Average: **{round(user_api['tstats']['wpm'], 2)} WPM\n"""
                                 f"""**Fastest Race: **{round(user_api['tstats']['bestGameWpm'], 2)} WPM\n"""
                                 f"""**Captcha Speed: **{round(user_api['tstats']['certWpm'], 2)} WPM\n"""
                                 f"""{extra_stats}**Medals: **{f'{medal_count:,}'}\n"""),
                        inline = False)

        await ctx.send(embed = embed)
        await fetch([Urls().trd_import(player)], 'text')
        return

    @commands.command(aliases = get_aliases('lastonline'))
    async def lastonline(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()

        try:
            urls = [Urls().get_races(player, universe, 1)]
            response = await fetch(urls, 'json', lambda x: x[0]['t'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                                                         "doesn't exist or has no races in the "
                                                         f"{href_universe(universe)} universe")))
            return

        time_difference = time.time() - response[0]

        await ctx.send(embed = discord.Embed(colour = discord.Colour(MAIN_COLOR),
                       description = (f"**{player}** last played {seconds_to_text(time_difference)}\n"
                                      f"ago on the {href_universe(universe)} universe")))
        return

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.command(aliases = get_aliases('medals'))
    async def medals(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
        player = args[0].lower()
        try:
            urls = [Urls().user(player, 'play')]
            response = await fetch(urls, 'text')
            soup = BeautifulSoup(response[0], 'lxml')
            rows = soup.select("table[class='personalInfoTable']")[0].select('tr')
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                                         "doesn't exist")))
            return

        medals = []
        for row in rows:
            cells = row.select('td')
            if len(cells) < 2: continue
            if cells[0].text.strip() == "Awards":
                medals = cells[1].select('img')
                break

        breakdown = {
            "g": {1: 0, 2: 0, 3: 0},
            "d": {1: 0, 2: 0, 3: 0},
            "w": {1: 0, 2: 0, 3: 0},
            "m": {1: 0, 2: 0, 3: 0},
            "y": {1: 0, 2: 0, 3: 0}
        }
        for medal in medals:
            title = medal['title']
            breakdown["g"][int(title[0])] += 1
            breakdown[title[17]][int(title[0])] += 1

        general = list(breakdown['g'].values())
        daily = list(breakdown['d'].values())
        weekly = list(breakdown['w'].values())
        monthly = list(breakdown['m'].values())
        yearly = list(breakdown['y'].values())

        if not sum(general):
            embed = discord.Embed(title = f"Medal Stats for {player}",
                                  colour = discord.Colour(MAIN_COLOR),
                                  description = "It's empty here.")
            embed.set_thumbnail(url = Urls().thumbnail(player))
            await ctx.send(embed = embed)
            return

        embed = discord.Embed(title = f"Medals Stats for {player}",
                              colour=discord.Colour(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        helper_constructor = lambda count: (f"**Total: **{sum(count)}\n"
                                            f":first_place: x {count[0]}\n"
                                            f":second_place: x {count[1]}\n"
                                            f":third_place: x {count[2]}")
        embed.add_field(name = "General",
                        value = helper_constructor(general),
                        inline = False)
        if sum(daily):
            embed.add_field(name = "Daily",
                            value = helper_constructor(daily),
                            inline = True)
        if sum(weekly):
            embed.add_field(name = "Weekly",
                            value = helper_constructor(weekly),
                            inline = True)
        if sum(monthly):
            embed.add_field(name = "Monthly",
                            value = helper_constructor(monthly),
                            inline = True)
        if sum(yearly):
            embed.add_field(name = "Yearly",
                            value = helper_constructor(yearly),
                            inline = True)

        await ctx.send(embed = embed)
        return

    @commands.command(aliases = get_aliases('toptens'))
    async def toptens(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()
        with open(TOPTENS_FILE_PATH, 'r') as jsonfile:
            player_top_tens = json.load(jsonfile)

        try:
            player_data = player_top_tens[player]
            last_updated = float(player_top_tens['last updated'])
        except KeyError:
            embed = discord.Embed(title = f"Text Top 10 Statistics for {player}",
                                  color = discord.Color(MAIN_COLOR),
                                  description = "It's empty here.")
            embed.set_thumbnail(url = Urls().thumbnail(player))

            await ctx.send(embed = embed)
            return

        total = 0
        for value in player_data.values():
            total += int(value)

        breakdown = ''
        for i in range(1, 4):
            breakdown += f"**{i}:** {f'{int(player_data[str(i)]):,}'}\n"
        for i in range(4, 11):
            breakdown += f"**{i}:** {f'{int(player_data[str(i)]):,}'} | "
        breakdown = breakdown[:-3]

        embed = discord.Embed(title = f"Text Top 10 Statistics for {player}",
                              color = discord.Color(MAIN_COLOR),
                              description = f"**{f'{total}'}** text top 10s")
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.set_footer(text = f"Text top 10 data was last updated {seconds_to_text(time.time() - last_updated)} ago")
        embed.add_field(name = "Breakdown", value = breakdown, inline = False)

        await ctx.send(embed = embed)
        return

    @commands.cooldown(1, 20, commands.BucketType.default)
    @commands.command(aliases = get_aliases('leaderboard'))
    async def leaderboard(self, ctx, *args):
        user_id = ctx.message.author.id
        num_lb = 10
        error_one = Error(ctx, ctx.message) \
                    .parameters(f"{ctx.invoked_with} [races/points/textbests/textstyped/toptens] <num>")
        error_two = Error(ctx, ctx.message) \
                    .incorrect_format('`num` must be a positive integer between 1 and 10')

        if len(args) == 0:
            await ctx.send(content = f"<@{user_id}>", embed = error_one)
            return
        elif len(args) == 2:
            if args[0].lower() != "toptens":
                await ctx.send(content = f"<@{user_id}>", embed = error_one)
                return
            try:
                num_lb = int(args[1])
                if num_lb < 1 or num_lb > 10:
                    await ctx.send(content = f"<@{user_id}>", embed = error_two)
                    return
            except ValueError:
                await ctx.send(content = f"<@{user_id}>", embed = error_two)
                return
        elif len(args) > 2:
            await ctx.send(content = f"<@{user_id}>", embed = error_one)
            return

        category_dict = {
            'races': 'races',
            'points': 'points',
            'textbests': 'wpm_textbests',
            'textstyped': 'texts_raced',
            'toptens': 'toptens'
        }

        try:
            category = category_dict[args[0].lower()]
            urls = [Urls().leaders(category)]
        except KeyError:
            await ctx.send(content = f"<@{user_id}>", embed = error_two)
            return

        def helper_formatter(player, country, parameter, index, *args):
            formatted = NUMBERS[index - 1]
            if country:
                formatted += f":flag_{country}: "
            else:
                formatted += '<:flagblank:744520567113252926> '
            if isinstance(parameter, str):
                formatted += f"{player} - {parameter}\n"
                return formatted
            if args:
                formatted += f"{player} - {f'{parameter:,}'} WPM\n"
                return formatted
            formatted += f"{player} - {f'{round(parameter):,}'}\n"
            return formatted

        value = ''
        if category == 'races': name = '**Races Leaderboard**'
        elif category == 'points': name = '**Points Leaderboard**'
        elif category == 'wpm_textbests': name = '**Text Bests Leaderboard**'
        elif category == 'texts_raced': name = '**Texts Raced Leaderboard**'

        top_players = []
        if category != 'toptens':
            response = await fetch(urls, 'read')
            soup = BeautifulSoup(response[0], 'html.parser')
            rows = soup.select('table')[0].select('tr')
            for i in range(1, 16):
                player = rows[i].select('td')[1].select('a')[0]['href'][18:]
                player_urls = [Urls().get_user(player, 'play')]
                player_response = await fetch(player_urls, 'json')
                player_response = player_response[0]
                country = player_response['country']
                if category == 'races': parameter = int(player_response['tstats']['cg'])
                elif category == 'points': parameter = float(player_response['tstats']['points'])
                elif category == 'wpm_textbests': parameter = float(rows[i].select('td')[2].text)
                elif category == 'texts_raced': parameter = rows[i].select('td')[4].text
                top_players.append([player, parameter, country])

            if category != 'texts_raced':
                top_players = sorted(top_players, key = lambda x: x[1], reverse = True)
            if category != 'wpm_textbests':
                for i in range(0, 10):
                    player_info = top_players[i]
                    value += helper_formatter(player_info[0], player_info[2], player_info[1], i + 1)
            else:
                for i in range(0, 10):
                    player_info = top_players[i]
                    value += helper_formatter(player_info[0], player_info[2], player_info[1], i + 1, True)
        else:
            with open(TOPTENS_FILE_PATH, 'r') as jsonfile:
                player_top_tens = json.load(jsonfile)
            last_updated = float(player_top_tens['last updated'])
            del player_top_tens['last updated']

            for player, top_tens in player_top_tens.items():
                top_count = 0
                top_tens_values = list(top_tens.values())
                for count in range(0, num_lb):
                    top_count += int(top_tens_values[count])
                top_players.append([player, top_count])

            top_players = [player for player in top_players if player[1] != 0]
            top_players = sorted(top_players, key = lambda x: x[1])
            players_with_top_tens = len(top_players)

            value += f"{f'{players_with_top_tens:,}'} players have top {num_lb}s\n"
            for i in range(0, 10):
                num = NUMBERS[i]
                value += (f"{num} {top_players[-(i + 1)][0]} "
                          f"- {f'{top_players[-(i + 1)][1]:,}'}\n")
            value = value[:-1]
            name = {
                1: 'Ones',
                2: 'Twos',
                3: 'Threes',
                4: 'Fours',
                5: 'Fives',
                6: 'Sixes',
                7: 'Sevens',
                8: 'Eights',
                9: 'Nines',
                10: 'Tens'
            }
            name = f"Text Top {name[num_lb]}"

        embed = discord.Embed(color = discord.Color(MAIN_COLOR))
        embed.add_field(name = name, value = value)
        if category == 'wpm_textbests':
            embed.set_footer(text = 'All users have at least 1,000 races and \n 400 texts typed')
        elif category == 'toptens':
            embed.set_footer(text = ("Text top 10 data was last updated\n"
                                     f"{seconds_to_text(time.time() - last_updated)} ago"))
        await ctx.send(embed = embed)

        if category != 'toptens':
            urls = []
            for player in top_players:
                urls.append(Urls().trd_import(player))
            await fetch(urls, 'text')
        return

    @commands.cooldown(2, 25, commands.BucketType.default)
    @commands.command(aliases = get_aliases('competition'))
    async def competition(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        universe = account['universe']

        categories = {
            'races': 'gamesFinished',
            'points': 'points',
            'wpm': 'wpm'
        }

        if len(args) == 0:
            args = ('points',)
        if len(args) == 1:
            try:
                category = categories[args[0].lower()]
            except KeyError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('Must provide a valid cateogry: `races/points/wpm`'))
                return
        else:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [races/points/wpm]"))
            return

        urls = [Urls().get_competition('day', category, universe)]
        competition = await fetch(urls, 'json')
        competition = competition[0]

        def helper_formatter(player, country, points, races, wpm_sum, index):
            formatted = NUMBERS[index]
            if country:
                formatted += f":flag_{country}: "
            else:
                formatted += "<:flagblank:744520567113252926> "
            formatted += f"{player} - {f'{points:,}'} | {f'{races:,}'} | {f'{round(wpm_sum / races, 2):,}'} WPM\n"
            return formatted

        players = []
        conn = sqlite3.connect(TEMPORARY_DATABASE_PATH)
        c = conn.cursor()
        for competitor in competition:
            player = competitor[1]['typeracerUid'][3:]
            if competitor[0]['country']:
                country = competitor[0]['country']
            else:
                country = ''

            today_timestamp = (datetime.datetime.utcnow().date() \
                               - datetime.date(1970, 1, 1)).total_seconds()
            file_name = f"t_{player}_{universe}_{today_timestamp}_{today_timestamp + 86400}".replace('.', '_')

            try:
                user_data = c.execute(f"SELECT * FROM {file_name} ORDER BY gn DESC LIMIT 1")
                last_race = user_data.fetchone()
                time_stamp = last_race[1] + 0.01
            except sqlite3.OperationalError:
                time_stamp = today_timestamp
                c.execute(f"CREATE TABLE {file_name} (gn, t, tid, wpm, pts)")

            races = await fetch_data(player, universe, time_stamp, today_timestamp + 86400)
            if races:
                c.executemany(f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)", races)
                conn.commit()
            points, wpm = [], []
            data = c.execute(f"SELECT * FROM {file_name}").fetchall()
            for row in data:
                points.append(row[4])
                wpm.append(row[3])
            players.append([player, country, round(sum(points)), len(points), round(sum(wpm), 2)])

        conn.close()

        if category == 'points':
            players = sorted(players, key = lambda x: x[2])[-10:][::-1]
        elif category == 'gamesFinished':
            players = sorted(players, key = lambda x: x[3])[-10:][::-1]
        elif category == 'wpm':
            players = sorted(players, key = lambda x: x[4] / x[3])[-10:][::-1]

        value = ''
        for i in range(0, 10):
            player = players[i]
            value += helper_formatter(player[0], player[1], player[2], player[3], player[4], i)

        embed = discord.Embed(title = f"Daily Competition ({args[0]})",
                              color = discord.Color(MAIN_COLOR),
                              description = f"**Universe:** {href_universe(universe)}",
                              url = urls[0])
        embed.add_field(name = datetime.datetime.utcnow().date().strftime("%B %d, %Y"),
                        value = value)
        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(BasicStats(bot))
