import datetime
import re
import sys
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.config import TR_WARNING
from TypeRacerStats.config import BOT_ADMIN_IDS
from TypeRacerStats.Core.Common.accounts import account_information
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.urls import Urls

class RealSpeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = get_aliases('realspeed'))
    async def realspeed(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        desslejusted, universe = account['desslejusted'], account['universe']
        race_api_response = None
        replay_url = ''

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) > 2 or len(args) == 0:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters('realspeed [user] [race_num]` or `realspeed [url]'))
            return

        if len(args) == 1:
            try:
                args[0].index('result?')
                replay_url = args[0]
                urls = [[replay_url, 'text']]
            except ValueError:
                try:
                    player = args[0]
                    urls = [[Urls().get_races(player, universe, 1), 'json']]
                    race_api_response = (await fetch(urls))[0][0]
                    last_race = int(race_api_response['gn'])
                    replay_url = Urls().result(args[0], last_race, universe)
                    urls = [[replay_url, 'text']]
                except:
                    await ctx.send(content = f"<@{user_id}>",
                                   embed = Error(ctx, ctx.message)
                                           .missing_information(("User doesn't exist or has no races in the "
                                                                 f"[`{universe}`](https://play.typeracer.com/?universe={universe}) universe")))
                    return

        elif len(args) == 2:
            try:
                replay_url = Urls().result(args[0], int(args[1]), universe)
                urls = [[replay_url, 'text']]
            except ValueError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`race_num` must be a positive integer'))
                return

        try:
            responses = await fetch(urls)
            result = scrape_result(responses)[0]
            if not race_api_response:
                timestamp = result['timestamp']
                player = result['player']
                universe = result['universe']
                race_api_response = await find_registered(player, universe, result['race_number'], timestamp)
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(('`var typingLog` was not found in the requested URL;\n'
                                                         f"Currently linked to [`{universe}`](https://play.typeracer.com/?universe={universe})\n\n")))
            return

        lagged = race_api_response['wpm']
        realspeeds = compute_realspeed(result['typinglog'], lagged, desslejusted, universe)
        race_number = result['race_number']
        start, unlagged, adjusted, ping, desslejusted_wpm = tuple(realspeeds.values())

        title = f"Real Speeds for {player}'s {race_number} Race"

        description = f"**Universe:** [`{universe}`](https://play.typeracer.com/?universe={universe})\n"

        if ping > 0:
            color = MAIN_COLOR
        else:
            color = 0xe0001a
            description += f"{TR_WARNING} This score is reverse lagged {TR_WARNING}"
        embed = discord.Embed(title = title,
                              colour = discord.Colour(color),
                              url = replay_url,
                              description = description)
        embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
        embed.set_footer(text = "Adjusted speed is calculated by removing the start time from the race")
        value = f"\"{result['race_text']}\""

        if len(value) > 1023:
            value = value[0:1020] + "…\""
        embed.add_field(name = f"Quote (Race Text ID: {race_api_response['tid']})",
                        value = value,
                        inline = False)

        real_speeds = (f"**Lagged:** {f'{lagged:,}'} WPM "
                       f"({f'{round(unlagged - lagged, 2):,}'} WPM lag)\n"
                       f"**Unlagged:** {f'{unlagged:,}'} WPM"
                       f" ({f'{round(ping):,}'}ms ping)\n"
                       f"**Adjusted:** {f'{adjusted:,}'} WPM"
                       f" ({f'{start:,}'}ms start)")
        if desslejusted:
            real_speeds += f"\n**Desslejusted:** {f'{desslejusted_wpm:,}'} WPM"
        embed.add_field(name = "Speeds", value = real_speeds, inline = False)

        await ctx.send(embed = embed)
        return

    @commands.command(aliases = get_aliases('realspeedaverage'))
    async def realspeedaverage(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        desslejusted, universe = account['desslejusted'], account['universe']
        race_api_response = None
        replay_url = ''

        if len(args) == 0 or (len(args) == 1 and len(args[0]) < 4):
            args = check_account(user_id)(args)

        if len(args) > 3 or len(args) == 0:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters('realspeedaverage [user] <first_race> <last_race>'))
            return

        try:
            player = args[0]
            urls = [[Urls().get_races(player, universe, 1), 'json']]
            race_api_response = (await fetch(urls))[0][0]
            last_race = int(race_api_response['gn'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(("User doesn't exist or has no races in the "
                                                         f"[`{universe}`](https://play.typeracer.com/?universe={universe})")))
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
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('The number of races must be a positive integer'))
            return
        if race_interval >= 100 and not user_id in BOT_ADMIN_IDS:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .lacking_permissions('You may only request up to 100 races'))
            return
        elif race_interval >= 500:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .lacking_permissions('You may only request up to 500 races'))
            return

        urls = []
        for i in range(first_race, last_race + 1):
            replay_url = Urls().result(args[0], i, universe)
            urls.append([replay_url, 'text'])

        responses = await fetch(urls)
        parsed_responses = scrape_result(responses)

        if len(parsed_responses) == 0:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(('`var typingLog` was not found in any of the races;\n'
                                                         f"Currently linked to [`{universe}`](https://play.typeracer.com/?universe={universe})\n\n")))
            return

        parsed_responses = sorted(parsed_responses,
                                  key = lambda x: int(x['race_number']),
                                  reverse = True)
        race_api_responses = await find_registered(player, universe, first_race,
                                                   parsed_responses[-1]['timestamp'],
                                                   parsed_responses[0]['timestamp'])
        computed_responses = []
        for i in range(0, len(parsed_responses)):
            for j in range(0, len(race_api_responses)):
                parsed_response, race_api_response = parsed_responses[i], race_api_responses[j]
                if parsed_response['race_number'] != race_api_response['gn']:
                    continue
                realspeeds = compute_realspeed(parsed_response['typinglog'],
                                               race_api_response['wpm'],
                                               desslejusted,
                                               universe)
                computed_responses.append({
                    'url': Urls().result(player, parsed_response['race_number'], universe),
                    'race_number': parsed_response['race_number'],
                    'lagged': race_api_response['wpm'],
                    'unlagged': realspeeds['unlagged'],
                    'adjusted': realspeeds['adjusted'],
                    'ping': realspeeds['ping'],
                    'start': realspeeds['start'],
                    'desslejusted': realspeeds['desslejusted']
                })
                break

        lagged_sum, unlagged_sum, adjusted_sum, ping_sum = (0,) * 4
        start_sum, desslejusted_sum, lag_sum, reverse_lag_count = (0,) * 4

        for computed_response in computed_responses:
            lagged_sum += computed_response['lagged']
            unlagged_sum += computed_response['unlagged']
            adjusted_sum += computed_response['adjusted']
            ping_sum += computed_response['ping']
            start_sum += computed_response['start']
            lag_sum += computed_response['unlagged'] - computed_response['lagged']
            if computed_response['ping'] <= 0:
                reverse_lag_count += 1
            if desslejusted:
                desslejusted_sum += computed_response['desslejusted']

        description = f"**Universe:** [`{universe}`](https://play.typeracer.com/?universe={universe})\n\n"
        if reverse_lag_count:
            color = 0xe0001a
            description = (f"{TR_WARNING} This interval contains "
                           f"{reverse_lag_count} lagged score(s) {TR_WARNING}\n")
        else:
            color = MAIN_COLOR

        race_count = len(computed_responses)

        title = f"Real Speed Average for {player} (Races {f'{first_race:,}'} to {f'{last_race:,}'})"
        real_speeds = f"**Lagged Average:** {f'{round(lagged_sum / race_count, 2):,}'} WPM\n"
        delays = (f"**Average Lag:** {f'{round(lag_sum / race_count, 2):,}'} WPM\n"
                  f"**Average Ping:** {f'{round(ping_sum / race_count, 3):,}'}ms\n")
        real_speeds += f"**Unlagged Average:** {f'{round(unlagged_sum / race_count, 2):,}'} WPM\n"
        real_speeds += f"**Adjusted Average:** {f'{round(adjusted_sum / race_count, 3):,}'} WPM\n"
        if desslejusted:
            real_speeds += f"\n**Desslejusted Average:** {f'{round(desslejusted_sum / race_count, 3):,}'} WPM"
        delays += f"**Average Start:** {f'{round(start_sum / race_count, 3):,}'}ms"

        if race_count >= 20:
            if description:
                embed = discord.Embed(title = title,
                                      color = discord.Color(color),
                                      description = description)
            else:
                embed = discord.Embed(title = title,
                                      color = discord.Color(color))
            embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
            embed.set_footer(text = "(Adjusted speed is calculated by removing the start time from the race)")
            embed.add_field(name = "Speed", value = real_speeds, inline = False)
            embed.add_field(name = "Delays", value = delays, inline = False)
            await ctx.send(content = f"<@{user_id}>", embed = embed)
            return
        
        embed = discord.Embed(title = title,
                              color = discord.Colour(color),
                              description = f"{description}**Speed**\n{real_speeds}\n**Delays**\n{delays}")
        for computed_response in computed_responses:
            name = f"""Real Speeds for Race #{f"{computed_response['race_number']:,}"}"""
            if computed_response['ping'] < 0:
                name += f" {TR_WARNING} Reverse Lagged {TR_WARNING}"
            value = (f"""**Lagged Speed:** {f"{round(computed_response['lagged'], 2)}"} WPM """
                     f"""({f"{round(computed_response['unlagged'] - computed_response['lagged'], 2):,}"} WPM lag) """
                     f"""[<:replay:744891748513480816>]({computed_response['url']})\n"""
                     f"""**Unlagged Speed:** {f"{round(computed_response['unlagged'], 2):,}"} WPM """
                     f"""({f"{round(computed_response['ping']):,}"}ms ping)\n"""
                     f"""**Adjusted Speed:** {f"{round(computed_response['adjusted'], 3):,}"} WPM """
                     f"""({f"{round(computed_response['start'], 3):,}"}ms start)""")
            if desslejusted:
                value += f"""\n**Desslejusted Speed:** {f"{round(computed_response['desslejusted'], 3):,}"} WPM"""
            embed.add_field(name = name, value = value, inline = False)

        await ctx.send(embed = embed)
        return

def scrape_result(responses):
    results = []
    escapes = ''.join([chr(char) for char in range(1, 32)])

    for response in responses:
        try:
            soup = BeautifulSoup(response, 'html.parser')
            race_text = soup.select("div[class='fullTextStr']")[0].text.strip()
            player = soup.select("a[class='userProfileTextLink']")[0]["href"][13:]
            typinglog = re.sub(r'\\t\d', 'a',
                            re.search(r'typingLog\s=\s"(.*?)";', response)
                            .group(1).encode().decode('unicode-escape').translate(escapes))

            race_details = soup.select("table[class='raceDetails']")[0].select('tr')
            universe = 'play'
            for detail in race_details:
                cells = detail.select('td')
                category = cells[0].text.strip()
                if category == "Race Number":
                    race_number = int(cells[1].text.strip())
                elif category == "Date":
                    timestamp = int(datetime.datetime.strptime(cells[1].text.strip()[:-6],
                                                            "%a, %d %b %Y %H:%M:%S")
                                                            .strftime("%s"))
                elif category == "Universe":
                    universe = cells[1].text.strip()

            results.append({'player': player,
                            'timestamp': timestamp,
                            'race_number': race_number,
                            'universe': universe,
                            'race_text': race_text,
                            'typinglog': typinglog})
        except:
            pass

    return results

def compute_realspeed(typinglog, lagged, desslejusted, universe):
    times = [int(c) for c in re.findall(r"\d+", typinglog.split("|")[0])][2:]
    if universe == 'lang_ko':
        mult = 24000
    elif universe == 'lang_zh' or universe == 'new_lang_zh-tw' or universe == 'lang_zh-tw' or universe == 'lang_ja':
        mult = 60000
    else:
        mult = 12000

    quote_length, actual_time, start = len(times), sum(times), times[0]
    unlagged = round(mult * quote_length / actual_time, 2)
    ping = mult * quote_length / lagged - actual_time
    adjusted = round(mult * (quote_length - 1) / (actual_time - start), 3)
    if desslejusted:
        desslejusted_wpm = round(mult * quote_length / (actual_time - start), 3)
    else:
        desslejusted_wpm = None

    return {'start': start,
            'unlagged': unlagged,
            'adjusted': adjusted,
            'ping': ping,
            'desslejusted': desslejusted_wpm}

async def find_registered(player, universe, gn, timestamp, *args):
    if not args:
        urls = [[Urls().get_races(player, universe, timestamp - 1, timestamp + 1), 'json']]
        api_response = await fetch(urls)
        for race in api_response[0]:
            if race['gn'] == gn:
                return race
    else:
        urls = [[Urls().get_races(player, universe, timestamp - 1, args[0] + 1), 'json']]
        api_response = await fetch(urls)
        return api_response[0]

def setup(bot):
    bot.add_cog(RealSpeed(bot))
