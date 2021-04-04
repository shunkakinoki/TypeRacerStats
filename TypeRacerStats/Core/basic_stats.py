import datetime
import json
import os
import sqlite3
import sys
import time
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_ADMIN_IDS, MAIN_COLOR, NUMBERS
from TypeRacerStats.file_paths import TEMPORARY_DATABASE_PATH, TOPTENS_FILE_PATH, TOPTENS_JSON_FILE_PATH, DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import account_information, check_account, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import href_universe, seconds_to_text, num_to_text, escape_sequence
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.scrapers import timestamp_scraper
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls


class BasicStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('stats'))
    async def stats(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
            return

        player = get_player(user_id, args[0])
        urls = [Urls().get_user(player, universe)]
        try:
            user_api = (await fetch(urls, 'json'))[0]
        except:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               (f"[**{player}**]({urls[0]}) "
                                "doesn't exist")))
            return

        country = f":flag_{user_api['country']}: " if user_api[
            'country'] else ''
        name = user_api['name'] if user_api['name'] else ''
        name += ' ' if user_api['name'] and user_api['lastName'] else ''
        name += user_api['lastName'] if user_api['lastName'] else ''
        premium = 'Premium' if user_api['premium'] else 'Basic'
        try:
            banned = user_api['tstats']['disqualified']
            banned = '' if banned == 'false' or not banned else '\n**Status:** Banned'
        except KeyError:
            banned = ''

        urls = [Urls().trd_user(player, universe)]
        try:
            if universe != 'play':
                raise NotImplementedError
            trd_user_api = (await fetch(urls, 'json'))[0]
            textbests = round(float(trd_user_api['account']['wpm_textbests']),
                              2)
            textsraced = trd_user_api['account']['texts_raced']
            extra_stats = (f"**Text Bests: **{textbests} WPM\n"
                           f"**Texts Typed: **{textsraced}\n")
        except:
            textbests, textsraced, extra_stats = ('', ) * 3

        urls = [Urls().user(player, universe)]
        try:
            response = (await fetch(urls, 'text'))[0]
            soup = BeautifulSoup(response, 'html.parser')
            rows = soup.select("table[class='profileDetailsTable']")[0].select(
                'tr')
            medal_count = 0
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2: continue
                if cells[0].text.strip() == 'Racing Since':
                    date_joined = cells[1].text.strip()

            rows = soup.select("table[class='personalInfoTable']")[0].select(
                'tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2: continue
                if cells[0].text.strip() == 'Awards':
                    medal_count = len(cells[1].select('a'))
        except:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               (f"[**{player}**]({urls[0]}) "
                                "doesn't exist")))
            return

        if banned:
            color = 0xe0001a
        else:
            color = MAIN_COLOR

        embed = discord.Embed(
            title=f"{country}{player}",
            colour=discord.Colour(color),
            description=f"**Universe:** {href_universe(universe)}",
            url=urls[0])
        embed.set_thumbnail(url=Urls().thumbnail(player))
        embed.add_field(name="General",
                        value=(f"**Name:** {name}\n"
                               f"**Joined: **{date_joined}\n"
                               f"**Membership: **{premium}{banned}"),
                        inline=False)
        embed.add_field(
            name="Stats",
            value=
            (f"""**Races: **{f"{user_api['tstats']['cg']:,}"}\n"""
             f"""**Races Won: **{f"{user_api['tstats']['gamesWon']:,}"}\n"""
             f"""**Points: **{f"{round(user_api['tstats']['points']):,}"}\n"""
             f"""**Full Average: **{round(user_api['tstats']['wpm'], 2)} WPM\n"""
             f"""**Fastest Race: **{round(user_api['tstats']['bestGameWpm'], 2)} WPM\n"""
             f"""**Captcha Speed: **{round(user_api['tstats']['certWpm'], 2)} WPM\n"""
             f"""{extra_stats}**Medals: **{f'{medal_count:,}'}\n"""),
            inline=False)

        await ctx.send(embed=embed)
        await fetch([Urls().trd_import(player)], 'text')
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('lastonline'))
    async def lastonline(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
            return

        player = get_player(user_id, args[0])

        try:
            urls = [Urls().get_races(player, universe, 1)]
            response = (await fetch(urls, 'json', lambda x: x[0]['t']))[0]
        except:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information((
                    f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                    "doesn't exist or has no races in the "
                    f"{href_universe(universe)} universe")))
            return

        time_difference = time.time() - response

        await ctx.send(embed=discord.Embed(
            colour=discord.Colour(MAIN_COLOR),
            description=(
                f"**{player}** last played {seconds_to_text(time_difference)}\n"
                f"ago on the {href_universe(universe)} universe")))
        return

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('medals'))
    async def medals(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
        player = get_player(user_id, args[0])
        try:
            urls = [Urls().user(player, 'play')]
            response = (await fetch(urls, 'text'))[0]
            soup = BeautifulSoup(response, 'lxml')
            rows = soup.select("table[class='personalInfoTable']")[0].select(
                'tr')
        except:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               (f"[**{player}**]({urls[0]}) "
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
            "g": {
                1: 0,
                2: 0,
                3: 0
            },
            "d": {
                1: 0,
                2: 0,
                3: 0
            },
            "w": {
                1: 0,
                2: 0,
                3: 0
            },
            "m": {
                1: 0,
                2: 0,
                3: 0
            },
            "y": {
                1: 0,
                2: 0,
                3: 0
            }
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
            embed = discord.Embed(title=f"Medal Stats for {player}",
                                  colour=discord.Colour(MAIN_COLOR),
                                  description="It's empty here.")
            embed.set_thumbnail(url=Urls().thumbnail(player))
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title=f"Medals Stats for {player}",
                              colour=discord.Colour(MAIN_COLOR))
        embed.set_thumbnail(url=Urls().thumbnail(player))
        helper_constructor = lambda count: (f"**Total: **{sum(count)}\n"
                                            f":first_place: x {count[0]}\n"
                                            f":second_place: x {count[1]}\n"
                                            f":third_place: x {count[2]}")
        embed.add_field(name="General",
                        value=helper_constructor(general),
                        inline=False)
        if sum(daily):
            embed.add_field(name="Daily",
                            value=helper_constructor(daily),
                            inline=True)
        if sum(weekly):
            embed.add_field(name="Weekly",
                            value=helper_constructor(weekly),
                            inline=True)
        if sum(monthly):
            embed.add_field(name="Monthly",
                            value=helper_constructor(monthly),
                            inline=True)
        if sum(yearly):
            embed.add_field(name="Yearly",
                            value=helper_constructor(yearly),
                            inline=True)

        await ctx.send(embed=embed)
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('toptens'))
    async def toptens(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        is_admin = user_id in BOT_ADMIN_IDS
        send_json = is_admin and ctx.invoked_with[-1] == '*'

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
            return

        player = get_player(user_id, args[0])
        with open(TOPTENS_FILE_PATH, 'r') as jsonfile:
            player_top_tens = json.load(jsonfile)
        last_updated = float(player_top_tens['last updated'])

        if send_json:
            if player == '*':
                await ctx.send(file=discord.File(
                    TOPTENS_JSON_FILE_PATH, f"top_ten_{last_updated}.json"))
                return

            subset = dict()
            with open(TOPTENS_JSON_FILE_PATH, 'r') as jsonfile:
                top_tens = json.load(jsonfile)
            for item, value in top_tens.items():
                if player in value.values():
                    subset.update({item: value})
            with open('temporary.json', 'w') as jsonfile:
                json.dump(subset, jsonfile)
            await ctx.send(file=discord.File(
                'temporary.json', f"top_ten_{player}_{last_updated}.json"))
            os.remove('temporary.json')
            return

        try:
            player_data = player_top_tens[player]
        except KeyError:
            embed = discord.Embed(title=f"Text Top 10 Statistics for {player}",
                                  color=discord.Color(MAIN_COLOR),
                                  description="It's empty here.")
            embed.set_thumbnail(url=Urls().thumbnail(player))

            await ctx.send(embed=embed)
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

        embed = discord.Embed(title=f"Text Top 10 Statistics for {player}",
                              color=discord.Color(MAIN_COLOR),
                              description=f"**{f'{total:,}'}** text top 10s")
        embed.set_thumbnail(url=Urls().thumbnail(player))
        embed.set_footer(
            text=
            f"Text top 10 data was last updated {seconds_to_text(time.time() - last_updated)} ago"
        )
        embed.add_field(name="Breakdown", value=breakdown, inline=False)

        await ctx.send(embed=embed)
        return

    @commands.cooldown(1, 20, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('leaderboard'))
    async def leaderboard(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        num_lb = 10
        error_one = Error(ctx, ctx.message) \
                    .parameters(f"{ctx.invoked_with} [races/points/textbests/textstyped/toptens] <num>")
        error_two = Error(ctx, ctx.message) \
                    .incorrect_format('`num` must be a positive integer between 1 and 10')

        if len(args) == 0:
            await ctx.send(content=f"<@{user_id}>", embed=error_one)
            return
        elif len(args) == 2:
            if args[0].lower() != "toptens":
                await ctx.send(content=f"<@{user_id}>", embed=error_one)
                return
            try:
                num_lb = int(args[1])
                if num_lb < 1 or num_lb > 10:
                    await ctx.send(content=f"<@{user_id}>", embed=error_two)
                    return
            except ValueError:
                await ctx.send(content=f"<@{user_id}>", embed=error_two)
                return
        elif len(args) > 2:
            await ctx.send(content=f"<@{user_id}>", embed=error_one)
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
            await ctx.send(content=f"<@{user_id}>", embed=error_two)
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
                if category == 'races':
                    parameter = int(player_response['tstats']['cg'])
                elif category == 'points':
                    parameter = float(player_response['tstats']['points'])
                elif category == 'wpm_textbests':
                    parameter = float(rows[i].select('td')[2].text)
                elif category == 'texts_raced':
                    parameter = rows[i].select('td')[4].text
                top_players.append([player, parameter, country])

            if category != 'texts_raced':
                top_players = sorted(top_players,
                                     key=lambda x: x[1],
                                     reverse=True)
            if category != 'wpm_textbests':
                for i in range(0, 10):
                    player_info = top_players[i]
                    value += helper_formatter(player_info[0], player_info[2],
                                              player_info[1], i + 1)
            else:
                for i in range(0, 10):
                    player_info = top_players[i]
                    value += helper_formatter(player_info[0], player_info[2],
                                              player_info[1], i + 1, True)
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
            top_players = sorted(top_players, key=lambda x: x[1])
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

        embed = discord.Embed(color=discord.Color(MAIN_COLOR))
        embed.add_field(name=name, value=value)
        if category == 'wpm_textbests':
            embed.set_footer(
                text=
                'All users have at least 1,000 races and \n 400 texts typed')
        elif category == 'toptens':
            embed.set_footer(
                text=("Text top 10 data was last updated\n"
                      f"{seconds_to_text(time.time() - last_updated)} ago"))
        await ctx.send(embed=embed)

        if category != 'toptens':
            urls = []
            for player in top_players:
                urls.append(Urls().trd_import(player))
            await fetch(urls, 'text')
        return

    @commands.cooldown(2, 25, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('competition'))
    async def competition(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        categories = {
            'races': 'gamesFinished',
            'points': 'points',
            'wpm': 'wpm'
        }

        try:
            if len(args) == 0:
                sort, category = 'day', 'points'
            elif len(args) == 1:
                param = args[0].lower()
                if param in categories.keys():
                    sort, category = 'day', categories[param]
                elif param in ['day', 'week', 'month', 'year']:
                    sort, category = param, 'points'
                else:
                    raise KeyError
            elif len(args) == 2:
                sort, category = args[0].lower(), categories[args[1].lower()]
            else:
                raise ValueError
        except KeyError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    'Must provide a valid category: `races/points/wpm`'))
            return
        except ValueError:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [races/points/wpm]"))
            return

        urls = [Urls().get_competition(12, sort, category, universe)]
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
        if sort == 'day':
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
                file_name = f"t_{player}_{universe}_{today_timestamp}_{today_timestamp + 86400}".replace(
                    '.', '_')

                try:
                    user_data = c.execute(
                        f"SELECT * FROM {file_name} ORDER BY gn DESC LIMIT 1")
                    last_race = user_data.fetchone()
                    time_stamp = last_race[1] + 0.01
                except sqlite3.OperationalError:
                    time_stamp = today_timestamp
                    c.execute(
                        f"CREATE TABLE {file_name} (gn integer PRIMARY KEY, t, tid, wpm, pts)"
                    )

                races = await fetch_data(player, universe, time_stamp,
                                         today_timestamp + 86400)
                if races:
                    c.executemany(
                        f"INSERT INTO {file_name} VALUES (?, ?, ?, ?, ?)",
                        races)
                    conn.commit()
                points, wpm = [], []
                data = c.execute(f"SELECT * FROM {file_name}").fetchall()
                for row in data:
                    points.append(row[4])
                    wpm.append(row[3])
                players.append([
                    player, country,
                    round(sum(points)),
                    len(points),
                    round(sum(wpm), 2)
                ])

            conn.close()
        else:
            for competitor in competition:
                player = competitor[1]['typeracerUid'][3:]
                if competitor[0]['country']:
                    country = competitor[0]['country']
                else:
                    country = ''
                comp_stats = competitor[1]
                players.append([
                    player, country,
                    round(comp_stats['points']),
                    round(comp_stats['gamesFinished']),
                    comp_stats['gamesFinished'] * comp_stats['wpm']
                ])

        if category == 'points':
            players = sorted(players, key=lambda x: x[2])[-10:][::-1]
        elif category == 'gamesFinished':
            players = sorted(players, key=lambda x: x[3])[-10:][::-1]
        elif category == 'wpm':
            players = sorted(players, key=lambda x: x[4] / x[3])[-10:][::-1]

        value = ''
        for i in range(0, 10):
            player = players[i]
            value += helper_formatter(player[0], player[1], player[2],
                                      player[3], player[4], i)

        today = datetime.datetime.utcnow().date()

        if sort == 'day': date = today.strftime('%B %-d, %Y')
        elif sort == 'week':
            normalizer = today.isocalendar()[2]
            start_time = today - datetime.timedelta(days=normalizer - 1)
            end_time = today + datetime.timedelta(days=7 - normalizer)
            date = f"{start_time.strftime('%B %-d')}—{end_time.strftime('%-d, %Y')}"
        elif sort == 'month':
            date = today.strftime('%B %Y')
        elif sort == 'year':
            date = today.strftime('%Y')

        formatted_sort = {
            'day': 'Daily',
            'week': 'Weekly',
            'month': 'Monthly',
            'year': 'Yearly'
        }[sort]

        formatted_category = {
            'points': 'points',
            'gamesFinished': 'races',
            'wpm': 'wpm'
        }[category]

        embed = discord.Embed(
            title=f"{formatted_sort} Competition ({formatted_category})",
            color=discord.Color(MAIN_COLOR),
            description=f"**Universe:** {href_universe(universe)}",
            url=Urls().competition(sort, category, '', universe))
        embed.add_field(name=date, value=value)
        await ctx.send(embed=embed)
        return

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.cooldown(50, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('timebetween'))
    async def timebetween(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        url_param = False
        if len(args) < 2 or len(args) > 3:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    (f"{ctx.invoked_with} [url] [url]` or "
                     f"`{ctx.invoked_with} [user] [race_one] [race_two]")))
            return
        if len(args) == 2:
            try:
                args[0].index('result?') and args[1].index('result?')
                url_param = True
            except ValueError:
                args = check_account(user_id)(args)
        if len(args) == 3:
            player = get_player(user_id, args[0])
            try:
                race_one = int(args[1])
                race_two = int(args[2])
                if race_one <= 0 or race_two <= 1:
                    raise ValueError
                args = (race_one, race_two)
            except ValueError:
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).incorrect_format(
                        f"Refer to `help {ctx.invoked_with}` for correct parameter formats"
                    ))
                return

        urls = []
        if url_param: urls = [url for url in args]
        else:
            urls = [
                Urls().result(player, race_num, universe) for race_num in args
            ]

        responses = await fetch(urls, 'text', timestamp_scraper)
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            player = responses[0]['player']
            difference = abs(responses[1]['timestamp'] -
                             responses[0]['timestamp'])
            universe = responses[0]['universe']
            race_nums = [response['race_number'] for response in responses]
            race_one = min(race_nums)
            race_two = max(race_nums)
        except TypeError:
            try:
                if escape_sequence(player):
                    raise sqlite3.OperationalError
                difference = abs(c.execute(f"SELECT t FROM t_{player} WHERE gn = ?", (race_one,))
                                           .fetchone()[0] -\
                                 c.execute(f"SELECT t FROM t_{player} WHERE gn = ?", (race_two,))
                                           .fetchone()[0])
            except:
                conn.close()
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).missing_information(
                        '`timestamp` was not found in either race'))
                return
        conn.close()

        description = (f"The time between **{player}**'s "
                       f"**{num_to_text(race_one)}** and "
                       f"**{num_to_text(race_two)}** race in the\n"
                       f"{href_universe(universe)} universe was "
                       f"**{seconds_to_text(difference)}**")

        await ctx.send(embed=discord.Embed(color=discord.Color(MAIN_COLOR),
                                           description=description))
        return


def setup(bot):
    bot.add_cog(BasicStats(bot))
