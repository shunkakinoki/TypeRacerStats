import os
import sqlite3
import re
import sys
import time
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR, NUMBERS
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account, account_information
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, href_universe, num_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls

class Graphs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('histogram'))
    async def histogram(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                   "doesn't exist")))
            return
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(f"SELECT wpm FROM t_{player}")
            data = [i[0] for i in player_data.fetchall()]
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        ax = plt.subplots()[1]
        max_, min_ = max(data), min(data)
        if int(max_ - min_) // 10 == 0:
            ax.hist(data, bins = 1)
        else:
            ax.hist(data, bins = int(max_ - min_) // 10)

        ax.set_xlabel('WPM')
        ax.set_ylabel('Frequency')
        plt.grid(True)
        ax.set_title(f"{player}'s WPM Histogram")
        file_name = f"{player} WPM.png"
        plt.savefig(file_name)
        wpm_picture = discord.File(file_name, filename = file_name)
        await ctx.send(file = wpm_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(3, 15, commands.BucketType.user)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('boxplot'))
    async def boxplot(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) < 1 or len(args) > 4:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <user_2>...<user_4>"))
            return

        for player in args:
            if escape_sequence(player):
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                      .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                      "doesn't exist")))
                return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        data = []
        try:
            title_text = ''
            for user in args:
                title_text += f"{user} vs. "
                user_data = c.execute(f"SELECT wpm FROM t_{user}")
                temp = [i[0] for i in user_data]
                data.append(temp)
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()
        title_text = title_text[:-4]
        title_text += 'WPM'

        ax = plt.subplots()[1]
        ax.boxplot(data, showfliers = False)
        ax.set_xticklabels(list(args))
        ax.set_ylabel('WPM')
        ax.set_title(title_text)
        plt.grid(True)
        file_name = f"{title_text}.png"
        plt.savefig(file_name)
        wpm_picture = discord.File(file_name, filename = file_name)

        await ctx.send(file = wpm_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(3, 25, commands.BucketType.user)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('raceline'))
    async def raceline(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) < 1 or len(args) > 10:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <user_2>...<user_10>"))
            return
        today = time.time()

        opt = 0
        if len(args) > 1:
            try:
                args[0].index('.')
                opt = float(args[0])
                if opt <= 1.25 or opt > time.time() / 1_000_000_000:
                    raise ValueError
                args = args[1:]
            except ValueError:
                pass

        for player in args:
            if escape_sequence(player):
                await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
                return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        data_x, data_y = [], []
        try:
            for user in args:
                temp_x, temp_y, first_gn = [], [], 1
                if opt:
                    user_data = c.execute(f"SELECT t, gn FROM t_{user} WHERE t > {opt * 1_000_000_000}")
                    first_t, first_gn = user_data.fetchone()
                    temp_x.append(first_t)
                    temp_y.append(1)
                else:
                    user_data = c.execute(f"SELECT t, gn FROM t_{user}")
                for i in user_data:
                    temp_x.append(i[0])
                    temp_y.append(i[1] - first_gn + 1)
                data_x.append(temp_x)
                data_y.append(temp_y)
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        ax = plt.subplots()[1]
        count = 0
        for i in range(0, len(args)):
            try:
                ax.plot(data_x[i] + [today], data_y[i] + [data_y[i][-1]], label = args[i])
                count += 1
            except IndexError:
                pass

        if not count:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information('No users had races specified time interval'))
            return

        title = 'Races Over Time'
        if opt:
            title += f"\n(Since {opt}e9 UNIX Timestamp)"
        ax.set_title(title)
        ax.set_xlabel('Date (UNIX Timestamp)')
        ax.set_ylabel('Races')
        plt.grid(True)
        plt.tight_layout(rect=[0,0,0.75,1])
        ax.legend(loc = 'upper left', bbox_to_anchor = (1.03, 1), shadow = True, ncol = 1)
        file_name = 'Races Over Time.png'
        plt.savefig(file_name)
        races_over_time_picture = discord.File(file_name, filename = file_name)

        await ctx.send(file = races_over_time_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('improvement'))
    async def improvement(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 1: args = check_account(user_id)(args)

        if len(args) != 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <time/races>"))
            return

        player = args[0].lower()
        if args[1].lower() not in ['time', 'races']:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('Must provide a valid category: `time/races`'))
            return

        if args[1].lower() == 'time':
            q_category = 't'
            category = 'Time'
        else:
            q_category = 'gn'
            category = 'Races'

        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                   "doesn't exist")))
            return

        data_x, data_y = [], []
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(f"SELECT wpm, {q_category} FROM t_{player} ORDER by {q_category}")
            for row in player_data:
                data_x.append(row[1])
                data_y.append(row[0])
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        length = len(data_x)
        if length < 7500:
            sma = length // 15
        else:
            sma = 500
        moving_y = [sum(data_y[0:sma]) / sma]
        moving_y += [sum(data_y[i - sma:i]) / sma for i in range(sma, length)]
        moving_x = [data_x[0]] + data_x[sma:]

        ax = plt.subplots()[1]
        ax.scatter(data_x, data_y, marker = '.', alpha = 0.1, color = '#000000')
        ax.plot(moving_x, moving_y, color = '#FF0000')
        ax.set_title(f"{player}'s WPM Over {category}\n(Moving Average of {sma} Races)")

        if q_category == 't':
            ax.set_xlabel('Date (UNIX Timestamp)')
        else:
            ax.set_xlabel('Race #')

        ax.set_ylabel('WPM')
        plt.grid(True)
        file_name = f"WPM Over {category}.png"
        plt.savefig(file_name)
        races_over_time_picture = discord.File(file_name, filename = file_name)

        await ctx.send(file = races_over_time_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.cooldown(50, 100, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('adjustedgraph') + ['matchgraph'] + get_aliases('matchgraph'))
    async def adjustedgraph(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        ag = ctx.invoked_with in ['adjustedgraph'] + get_aliases('adjustedgraph')
        mg = ctx.invoked_with in ['matchgraph'] + get_aliases('matchgraph')

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) > 2 or len(args) == 0:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [race_num]` or `{ctx.invoked_with} [url]"))
            return

        if len(args) == 1:
            try:
                args[0].index('result?')
                replay_url = args[0]
                urls = [replay_url]
            except ValueError:
                try:
                    player = args[0].lower()
                    urls = [Urls().get_races(player, universe, 1)]
                    race_api_response = await fetch(urls, 'json')
                    last_race = race_api_response[0][0]['gn']
                    race_api_response = race_api_response[0][0]
                    replay_url = Urls().result(args[0], last_race, universe)
                    urls = [replay_url]
                except:
                    await ctx.send(content = f"<@{user_id}>",
                                   embed = Error(ctx, ctx.message)
                                           .missing_information((f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                                                                 "doesn't exist or has no races in the "
                                                                 f"{href_universe(universe)} universe")))
                    return

        elif len(args) == 2:
            try:
                replay_url = Urls().result(args[0], int(args[1]), universe)
                urls = [replay_url]
            except ValueError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`race_num` must be a positive integer'))
                return

        def helper_scraper(soup):
            escapes = ''.join([chr(char) for char in range(1, 32)])
            try:
                typinglog = re.sub('\\t\d', 'a',
                            re.search(r'typingLog\s=\s"(.*?)";', response)
                            .group(1).encode().decode('unicode-escape').translate(escapes)).split('|')
                return [int(c) for c in re.findall(r"\d+", typinglog[0])][2:]
            except:
                return None
        try:
            response = (await fetch(urls, 'text'))[0]
            if not response:
                raise KeyError
            soup = BeautifulSoup(response, 'html.parser')
            times = helper_scraper(soup)

            race_text = soup.select("div[class='fullTextStr']")[0].text.strip()
            player = soup.select("a[class='userProfileTextLink']")[0]["href"][13:]
            race_details = soup.select("table[class='raceDetails']")[0].select('tr')
            universe = 'play'
            opponents = []
            for detail in race_details:
                cells = detail.select('td')
                category = cells[0].text.strip()
                if category == 'Race Number':
                    race_number = int(cells[1].text.strip())
                elif category == 'Universe':
                    universe = cells[1].text.strip()
                elif category == 'Opponents':
                    opponents = [i['href'] for i in cells[1].select('a')]
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(('`var typingLog` was not found in the requested URL;\n'
                                                         f"Currently linked to the {href_universe(universe)} universe\n\n")))
            return

        if universe == 'lang_ko':
            mult = 24000
        elif universe == 'lang_zh' or universe == 'new_lang_zh-tw' or universe == 'lang_zh-tw' or universe == 'lang_ja':
            mult = 60000
        else:
            mult = 12000

        def wpm_helper(times):
            temp, total_time = [], 0
            for i, time_ in enumerate(times):
                total_time += time_
                try:
                    temp.append((i + 1) * mult / total_time)
                except ZeroDivisionError:
                    pass
            return temp

        if ag:
            times.pop(0)
            data_y = wpm_helper(times)
        else:
            unl = wpm_helper(times)
            data = {player: [unl, unl[-1], times[0], replay_url.split('https://data.typeracer.com/pit/')[1]]}
            for opponent in opponents:
                try:
                    urls = ["https://data.typeracer.com/pit/" + opponent]
                    response = (await fetch(urls, 'text'))[0]
                    if not response:
                        raise KeyError
                    soup = BeautifulSoup(response, 'html.parser')
                    times = helper_scraper(soup)
                    unl = wpm_helper(times)
                    data.update({opponent.split('|')[1][3:]: [unl, unl[-1], times[0], opponent]})
                except:
                    pass
            data = {k: v for k, v in sorted(data.items(), key = lambda x: x[1][1], reverse = True)}

        if ag:
            title_1 = f"Adjusted WPM Over {player}'s {num_to_text(race_number)} Race"
            title = f"{title_1}\nUniverse: {universe}"
        else:
            title_1 = f"Unlagged WPM Over {player}'s {num_to_text(race_number)} Race"
            title = f"{title_1}\nUniverse: {universe}"

        description = f"**Quote**\n\"{race_text[0:1008]}\""

        ax = plt.subplots()[1]
        if ag:
            ax.plot([i for i in range(1, len(data_y) + 1)], data_y)
        else:
            value, i = '', 0
            for name, data_y in data.items():
                ax.plot([i for i in range(1, len(data_y[0]) + 1)], data_y[0], label = name)
                value += (f"{NUMBERS[i]} [{name}]({f'https://data.typeracer.com/pit/{data_y[3]}'})"
                          f" - {round(data_y[1], 2)} WPM ({f'{data_y[2]:,}'}ms start)\n")
                i += 1
            print(value)
            plt.tight_layout(rect=[0.02,0.02,0.75,0.92])
            ax.legend(loc = 'upper left', bbox_to_anchor = (1.03, 1), shadow = True, ncol = 1)

        ax.set_title(title)
        ax.set_xlabel('Keystrokes')
        ax.set_ylabel('WPM')
        plt.grid(True)
        file_name = 'WPM Over Race.png'
        plt.savefig(file_name)
        plt.close()

        file_ = discord.File(file_name, filename = 'image.png')
        embed = discord.Embed(title = title_1, color = discord.Color(MAIN_COLOR), description = description, url = replay_url)
        embed.set_image(url = 'attachment://image.png')
        if mg:
            embed.add_field(name = 'Ranks (ranked by unlagged WPM)', value = value[:-1])
        os.remove(file_name)

        await ctx.send(file = file_, embed = embed)
        return

def setup(bot):
    bot.add_cog(Graphs(bot))
