import csv
import os
import sys
import discord
from discord.ext import commands, tasks
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_ADMIN_IDS, BOT_OWNER_IDS, MAIN_COLOR, NUMBERS, TR_WARNING
from TypeRacerStats.Core.Common.accounts import account_information, check_account, check_banned_status, get_player
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import href_universe, num_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.scrapers import compute_realspeed, find_registered, raw_typinglog_scraper, rs_typinglog_scraper
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.text_id_caching import cache_id
from TypeRacerStats.Core.Common.urls import Urls


class RealSpeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.realspeed_cache = dict()
        self.clear_cache.start()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.cooldown(50, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('realspeed') + ['lastrace'] +
                      get_aliases('lastrace') + ['raw'] + get_aliases('raw'))
    async def realspeed(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        desslejusted, universe = account['desslejusted'], account['universe']
        race_api_response = None
        replay_url = ''

        rs = ctx.invoked_with.lower() in ['realspeed'
                                          ] + get_aliases('realspeed')
        lr = ctx.invoked_with.lower() in ['lastrace'] + get_aliases('lastrace')
        raw = ctx.invoked_with.lower() in ['raw'] + get_aliases('raw')

        if len(args) == 0 or (len(args) == 1 and args[0][0] == '-'):
            args = check_account(user_id)(args)

        if len(args) > 2 or len(args) == 0:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] [race_num]` or `{ctx.invoked_with} [url]"
                ))
            return

        race_num = 0
        if len(args) == 2 and args[1][0] == '-':
            try:
                race_num = int(args[1])
                args = (args[0], )
            except ValueError:
                pass

        players = []
        if len(args) == 1:
            try:
                args[0].index('result?')
                replay_url = args[0]
                urls = [replay_url]
            except ValueError:
                try:
                    player = get_player(user_id, args[0])
                    urls = [Urls().get_races(player, universe, 1)]
                    race_api_response = await fetch(urls, 'json')
                    last_race = race_api_response[0][0]['gn']
                    if race_num < 0:
                        last_race += race_num
                        race_api_response = None
                    else:
                        race_api_response = race_api_response[0][0]
                    replay_url = Urls().result(player, last_race, universe)
                    urls = [replay_url]
                except:
                    await ctx.send(
                        content=f"<@{user_id}>",
                        embed=Error(ctx, ctx.message).missing_information((
                            f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                            "doesn't exist or has no races in the "
                            f"{href_universe(universe)} universe")))
                    return
        elif len(args) == 2:
            try:
                player = get_player(user_id, args[0])
                replay_url = Urls().result(player, int(args[1]), universe)
                urls = [replay_url]
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   '`race_num` must be a positive integer'))
                return
        try:
            if raw:
                responses = await fetch(urls, 'text', raw_typinglog_scraper)
            else:
                if not lr: urls, responses = self.check_cache(urls)
                if urls:
                    responses = await fetch(urls, 'text', rs_typinglog_scraper,
                                            True)
                    self.update_cache(responses)
                    responses = [
                        list(response.values())[0] for response in responses
                    ]
            result = responses[0]
            if not result:
                raise KeyError
            if not race_api_response:
                timestamp = result['timestamp']
                player = result['player']
                universe = result['universe']
                race_api_response = await find_registered(
                    player, universe, result['race_number'], timestamp)
        except:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information((
                    '`var typingLog` was not found in the requested URL;\n'
                    f"Currently linked to the {href_universe(universe)} universe\n\n"
                )))
            return

        lagged = race_api_response['wpm']
        try:
            realspeeds = compute_realspeed(result['length'],
                                           result['duration'], result['start'],
                                           lagged, desslejusted, universe)
        except ZeroDivisionError:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               ('∞ adjusted WPM')))

        race_number, color = result['race_number'], MAIN_COLOR
        title = f"Real Speeds for {player}'s {num_to_text(race_number)} Race"
        description = f"**Universe:** {href_universe(universe)}\n"

        if rs or raw:
            start, unlagged, adjusted, ping, desslejusted_wpm = tuple(
                realspeeds.values())
            if ping <= 0:
                color = 0xe0001a
                description += f"{TR_WARNING} This score is reverse lagged {TR_WARNING}"
            if raw:
                start, unlagged, adjusted, ping, desslejusted_wpm = tuple(
                    realspeeds.values())
                correction, adj_correction, length = result[
                    'correction'], result['adj_correction'], result['duration']
                raw_unlagged = (length * unlagged) / (length - correction)
                raw_adjusted = ((length - start) *
                                adjusted) / (length - start - adj_correction)
        elif lr:
            players.append([player, urls[0]] + list((realspeeds.values())))
            for opponent in result['opponents']:
                urls = ["https://data.typeracer.com/pit/" + opponent]
                opponent_data = await fetch(urls, 'text', rs_typinglog_scraper)
                result_ = opponent_data[0]
                timestamp_ = result_['timestamp']
                player_ = result_['player']
                opponent_api_response = await find_registered(
                    player_, universe, result_['race_number'], timestamp_)
                lagged_ = opponent_api_response['wpm']
                try:
                    realspeeds = compute_realspeed(result_['length'],
                                                   result_['duration'],
                                                   result_['start'], lagged_,
                                                   False, universe)
                    players.append([player_, urls[0]] +
                                   list((realspeeds.values())))
                except ZeroDivisionError:
                    pass

        embed = discord.Embed(title=title,
                              colour=discord.Colour(color),
                              url=replay_url,
                              description=description)
        embed.set_thumbnail(
            url=f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
        embed.set_footer(
            text=
            "Adjusted speed is calculated by removing the start time from the race"
        )
        value = f"\"{result['race_text']}\""

        if len(value) > 1023:
            value = value[0:1020] + "…\""
        embed.add_field(
            name=f"Quote (Race Text ID: {race_api_response['tid']})",
            value=value,
            inline=False)

        cache_id(ctx.message.channel.id, race_api_response['tid'])

        if rs or raw:
            real_speeds = (f"**Lagged:** {f'{lagged:,}'} WPM "
                           f"({f'{round(unlagged - lagged, 2):,}'} WPM lag)\n"
                           f"**Unlagged:** {f'{unlagged:,}'} WPM"
                           f" ({f'{round(ping):,}'}ms ping)\n"
                           f"**Adjusted:** {f'{adjusted:,}'} WPM"
                           f" ({f'{start:,}'}ms start)")
            if desslejusted:
                real_speeds += f"\n**Desslejusted:** {f'{desslejusted_wpm:,}'} WPM"
            if raw:
                real_speeds += (
                    f"\n**Raw Unlagged:** {f'{round(raw_unlagged, 2):,}'} WPM "
                    f"({f'{correction:,}'}ms correction time, {round(100 * correction / length, 2)}%)"
                    f"\n**Raw Adjusted:** {f'{round(raw_adjusted, 3):,}'} WPM")
            embed.add_field(name="Speeds", value=real_speeds, inline=False)
        elif lr:
            value = ''
            players = sorted(players, key=lambda x: x[3], reverse=True)
            for i, player in enumerate(players):
                segment = (f"{NUMBERS[i]} "
                           f"[{player[0]}]({player[1]}) - "
                           f"{player[3]} unlagged WPM / "
                           f"{player[4]} adjusted WPM\n")
                if len(value + segment) > 1024: break
                value += segment
            value = value[:-1]
            embed.add_field(name='Ranks (ranked by unlagged WPM)',
                            value=value,
                            inline=False)

        await ctx.send(embed=embed)
        return

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.cooldown(10, 600, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('realspeedaverage'))
    async def realspeedaverage(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        desslejusted, universe = account['desslejusted'], account['universe']
        race_api_response = None
        replay_url = ''
        redact = not ctx.invoked_with[-1] == '*'
        rawsa = 'raw' in ctx.invoked_with

        if len(args) == 0 or (len(args) == 1 and len(args[0]) < 4):
            args = check_account(user_id)(args)

        if len(args) > 3 or len(args) == 0:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] <first_race> <last_race>"))
            return

        try:
            player = get_player(user_id, args[0])
            urls = [Urls().get_races(player, universe, 1)]
            race_api_response = (await fetch(urls, 'json'))[0][0]
            last_race = int(race_api_response['gn'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                                                         "doesn't exist or has no races in the " \
                                                         f"{href_universe(universe)} universe")))
            return

        invalid = False
        if len(args) == 1:
            if last_race < 10:
                first_race = 1
            else:
                first_race = last_race - 9
        elif len(args) == 2:
            try:
                num = int(args[1])
                first_race = last_race - num + 1
            except ValueError:
                invalid = True
        elif len(args) == 3:
            try:
                first_race, last_race = int(args[1]), int(args[2])
            except ValueError:
                invalid = True
        race_interval = last_race - first_race
        if first_race <= 0 or last_race <= 0 or race_interval <= 0:
            invalid = True
        if invalid:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    'The number of races must be a positive integer'))
            return
        if race_interval >= 10 and not user_id in BOT_ADMIN_IDS:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).lacking_permissions(
                               'You may only request up to 10 races'))
            return
        elif race_interval >= 10 and not user_id in BOT_OWNER_IDS:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).lacking_permissions(
                               'You may only request up to 10 races'))
            return
        elif race_interval >= 500:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).lacking_permissions(
                               'You may only request up to 500 races'))
            return

        urls = []
        for i in range(first_race, last_race + 1):
            replay_url = Urls().result(player, i, universe)
            urls.append(replay_url)

        responses = []
        urls, responses = self.check_cache(urls, True)
        if urls:
            new_responses = await fetch(urls, 'text', raw_typinglog_scraper,
                                        True)
            self.update_cache(new_responses)
            new_responses = [
                list(response.values())[0] for response in new_responses
            ]
            responses += new_responses
        responses = [i for i in responses if i]
        if len(responses) == 0:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information((
                    '`var typingLog` was not found in any of the races;\n'
                    f"Currently linked to the {href_universe(universe)} universe\n\n"
                )))
            return

        responses = sorted(responses,
                           key=lambda x: int(x['race_number']),
                           reverse=True)

        urls = [
            Urls().get_races(player, universe, responses[-1]['timestamp'] - 1,
                             responses[0]['timestamp'] + 1)
        ]
        race_api_responses = (await fetch(urls, 'json'))[0]
        race_api_responses = sorted(race_api_responses,
                                    key=lambda x: x['gn'],
                                    reverse=True)
        computed_responses = []
        j = 0
        lagged_sum, unlagged_sum, adjusted_sum, ping_sum = (0, ) * 4
        start_sum, desslejusted_sum, lag_sum, reverse_lag_count = (0, ) * 4
        raw_unlagged_sum, raw_adjusted_sum, correction_time_sum, correction_percentage_sum = (
            0, ) * 4
        for i in range(0, len(race_api_responses)):
            response, race_api_response = responses[j], race_api_responses[i]
            if response['race_number'] == race_api_response['gn']:
                j += 1
                try:
                    realspeeds = compute_realspeed(response['length'],
                                                   response['duration'],
                                                   response['start'],
                                                   race_api_response['wpm'],
                                                   desslejusted, universe)
                    computed_responses.append({
                        'url':
                        Urls().result(player, response['race_number'],
                                      universe),
                        'race_number':
                        response['race_number'],
                        'lagged':
                        race_api_response['wpm'],
                        'unlagged':
                        realspeeds['unlagged'],
                        'adjusted':
                        realspeeds['adjusted'],
                        'ping':
                        realspeeds['ping'],
                        'start':
                        realspeeds['start'],
                        'desslejusted':
                        realspeeds['desslejusted']
                    })
                    lagged_sum += race_api_response['wpm']
                    unlagged_sum += realspeeds['unlagged']
                    adjusted_sum += realspeeds['adjusted']
                    ping_sum += realspeeds['ping']
                    start_sum += realspeeds['start']
                    lag_sum += realspeeds['unlagged'] - race_api_response['wpm']
                    if realspeeds['ping'] <= 0:
                        reverse_lag_count += 1
                    if desslejusted:
                        desslejusted_sum += realspeeds['desslejusted']
                    if rawsa:
                        correction, adj_correction, length = response[
                            'correction'], response[
                                'adj_correction'], response['duration']
                        raw_unlagged = (length * realspeeds['unlagged']) / (
                            length - correction)
                        raw_adjusted = (
                            (length - realspeeds['start']) *
                            realspeeds['adjusted']) / (
                                length - realspeeds['start'] - adj_correction)
                        computed_responses[-1].update({
                            'raw_unlagged':
                            raw_unlagged,
                            'raw_adjusted':
                            raw_adjusted,
                            'correction_time':
                            correction,
                            'correction_percentage':
                            round(100 * correction / length, 2)
                        })
                        raw_unlagged_sum += raw_unlagged
                        raw_adjusted_sum += raw_adjusted
                        correction_time_sum += correction
                        correction_percentage_sum += 100 * correction / length

                except ZeroDivisionError:
                    continue
            else:
                continue

        description = f"**Universe:** {href_universe(universe)}\n\n"
        if reverse_lag_count:
            color = 0xe0001a
            description += (
                f"{TR_WARNING} This interval contains "
                f"{reverse_lag_count} reverse lagged score(s) {TR_WARNING}\n")
        else:
            color = MAIN_COLOR

        race_count = len(computed_responses)

        title = f"""Real Speed Average for {player} (Races {f"{responses[-1]['race_number']:,}"} to {f"{responses[0]['race_number']:,}"})"""
        real_speeds = f"**Lagged Average:** {f'{round(lagged_sum / race_count, 2):,}'} WPM\n"
        delays = (
            f"**Average Lag:** {f'{round(lag_sum / race_count, 2):,}'} WPM\n"
            f"**Average Ping:** {f'{round(ping_sum / race_count, 3):,}'}ms\n"
            f"**Average Start:** {f'{round(start_sum / race_count, 3):,}'}ms")
        real_speeds += f"**Unlagged Average:** {f'{round(unlagged_sum / race_count, 2):,}'} WPM\n"
        real_speeds += f"**Adjusted Average:** {f'{round(adjusted_sum / race_count, 3):,}'} WPM"
        if desslejusted:
            real_speeds += f"\n**Desslejusted Average:** {f'{round(desslejusted_sum / race_count, 3):,}'} WPM"
        if rawsa:
            real_speeds += f"\n**Raw Unlagged Average:** {f'{round(raw_unlagged_sum / race_count, 3):,}'} WPM"
            real_speeds += f"\n**Raw Adjusted Average:** {f'{round(raw_adjusted_sum / race_count, 3):,}'} WPM"
            delays += f"\n**Correction Time:** {f'{round(correction_time_sum / race_count):,}'}ms"
            delays += f" ({round(correction_percentage_sum  / race_count, 2)}%)"

        if race_count >= 20 or redact:
            delays = f"\n{delays}"
            if not redact:
                csv_data = [list(computed_responses[0].keys())[1:]]
                csv_data += [
                    list(computed_response.values())[1:]
                    for computed_response in computed_responses
                ]
                filename = f"{player}_real_speed_average_{responses[-1]['race_number']}_to_{responses[0]['race_number']}.csv"
                with open(filename, 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(csv_data)
                file_ = discord.File(filename, filename)
            if description:
                embed = discord.Embed(title=title,
                                      color=discord.Color(color),
                                      description=description)
            else:
                embed = discord.Embed(title=title, color=discord.Color(color))
            embed.set_thumbnail(
                url=f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
            embed.set_footer(
                text=
                "(Adjusted speed is calculated by removing the start time from the race)"
            )
            embed.add_field(name="Speed", value=real_speeds, inline=False)
            embed.add_field(name="Delays", value=delays, inline=False)
            if not redact:
                await ctx.send(file=file_,
                               content=f"<@{user_id}>",
                               embed=embed)
                os.remove(filename)
            else:
                await ctx.send(content=f"<@{user_id}>", embed=embed)
            return

        embed = discord.Embed(
            title=title,
            color=discord.Colour(color),
            description=
            f"{description}**Speed**\n{real_speeds}\n**Delays**\n{delays}")
        for computed_response in computed_responses:
            name = f"""Real Speeds for Race #{f"{computed_response['race_number']:,}"}"""
            if computed_response['ping'] < 0:
                name += f" {TR_WARNING} Reverse Lagged {TR_WARNING}"
            value = (
                f"""**Lagged Speed:** {f"{round(computed_response['lagged'], 2)}"} WPM """
                f"""({f"{round(computed_response['unlagged'] - computed_response['lagged'], 2):,}"} WPM lag) """
                f"""[:cinema:]({computed_response['url']})\n"""
                f"""**Unlagged Speed:** {f"{round(computed_response['unlagged'], 2):,}"} WPM """
                f"""({f"{round(computed_response['ping']):,}"}ms ping)\n"""
                f"""**Adjusted Speed:** {f"{round(computed_response['adjusted'], 3):,}"} WPM """
                f"""({f"{round(computed_response['start'], 3):,}"}ms start)""")
            if desslejusted:
                value += f"""\n**Desslejusted Speed:** {f"{round(computed_response['desslejusted'], 3):,}"} WPM"""
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)
        return

    def update_cache(self, responses):
        for response in responses:
            if response:
                self.realspeed_cache.update(response)

    def check_cache(self, urls, *raw):
        results = []
        uncached_urls = []

        for url in urls:
            try:
                if raw and raw[0]:
                    self.realspeed_cache[url]['correction']
                results.append(self.realspeed_cache[url])
            except KeyError:
                uncached_urls.append(url)

        return uncached_urls, results

    @tasks.loop(hours=48)
    async def clear_cache(self):
        self.realspeed_cache = dict()


def setup(bot):
    bot.add_cog(RealSpeed(bot))
