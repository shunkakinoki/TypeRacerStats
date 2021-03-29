import datetime
import os
import sqlite3
import re
import sys
import time
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR, NUMBERS
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account, account_information, check_banned_status
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, graph_color, href_universe, num_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms, get_graph_colors
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.utility import reduce_list


class Graphs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('histogram'))
    async def histogram(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(f"SELECT wpm FROM t_{player}")
            data = [i[0] for i in player_data.fetchall()]
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        ax = plt.subplots()[1]
        max_, min_ = max(data), min(data)

        if int(max_ - min_) // 10 == 0:
            patches = ax.hist(data, bins=1)[2]
        else:
            patches = ax.hist(data, bins=int(max_ - min_) // 10)[2]

        ax.set_xlabel('WPM')
        ax.set_ylabel('Frequency')
        plt.grid(True)
        ax.set_title(f"{player}'s WPM Histogram")
        file_name = f"{player} WPM.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False, patches)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        wpm_picture = discord.File(file_name, filename=file_name)
        await ctx.send(file=wpm_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(3, 15, commands.BucketType.user)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('boxplot'))
    async def boxplot(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) < 1 or len(args) > 4:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] <user_2>...<user_4>"))
            return

        for player in args:
            if escape_sequence(player):
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).missing_information(
                        (f"[**{player}**]({Urls().user(player, 'play')}) "
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
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()
        title_text = title_text[:-4]
        title_text += 'WPM'

        ax = plt.subplots()[1]
        ax.boxplot(data, showfliers=False)
        ax.set_xticklabels(list(args))
        ax.set_ylabel('WPM')
        ax.set_title(title_text)
        plt.grid(True)
        file_name = f"{title_text}.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, True)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        wpm_picture = discord.File(file_name, filename=file_name)

        await ctx.send(file=wpm_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(3, 25, commands.BucketType.user)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('raceline') + ['pointline'] +
                      get_aliases('pointline'))
    async def raceline(self, ctx, *args):
        user_id = ctx.message.author.id

        rl = ctx.invoked_with.lower() in ['raceline'] + get_aliases('raceline')
        pl = ctx.invoked_with.lower() in ['pointline'
                                          ] + get_aliases('pointline')

        units = 'Races' if rl else 'Points'
        retroactive = ctx.invoked_with[-1] == '*' and pl

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) < 1 or len(args) > 10:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).parameters(
                    f"{ctx.invoked_with} [user] <user_2>...<user_10>"))
            return
        today = time.time()

        start, end = 0, 0
        if len(args) > 1:
            try:
                args[0].index('-')
                start = (
                    datetime.datetime.strptime(args[0], "%Y-%m-%d").date() -
                    datetime.date(1970, 1, 1)).total_seconds()
                if start <= 1_250_000_000 or start > time.time():
                    raise ValueError
                args = args[1:]
            except ValueError:
                pass
        if len(args) > 1:
            try:
                args[-1].index('-')
                end = (
                    datetime.datetime.strptime(args[-1], "%Y-%m-%d").date() -
                    datetime.date(1970, 1, 1)).total_seconds()
                if end <= 1_250_000_000 or end > time.time():
                    raise ValueError
                args = args[:-1]
            except ValueError:
                pass

        for player in args:
            if escape_sequence(player):
                await ctx.send(
                    content=f"<@{user_id}>",
                    embed=Error(ctx, ctx.message).missing_information(
                        (f"[**{player}**]({Urls().user(player, 'play')}) "
                         "doesn't exist")))
                return

        def calculate_pts(tid, wpm):
            try:
                return text_data[str(tid)]['word count'] * wpm / 60
            except ValueError:
                return 0
            except KeyError:
                return 0

        text_data = load_texts_json()
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        data_x, data_y = [], []
        try:
            for user in args:
                temp_x, temp_y, first_gn, cur_pts = [], [], 1, 0
                if start:
                    if not end:
                        user_data = c.execute(
                            f"SELECT t, gn, pts, wpm, tid FROM t_{user} WHERE t > ?",
                            (start, ))
                    else:
                        user_data = c.execute(
                            f"SELECT t, gn, pts, wpm, tid FROM t_{user} WHERE t > ? AND t < ?",
                            (start, end))
                    try:
                        first_t, first_gn, first_pts, first_wpm, first_tid = user_data.fetchone(
                        )
                    except TypeError:
                        continue
                    temp_x.append(datetime.datetime.fromtimestamp(first_t))
                    if rl:
                        temp_y.append(1)
                    elif pl:
                        if retroactive and not first_pts:
                            first_pts = calculate_pts(first_tid, first_wpm)
                        temp_y.append(first_pts)
                else:
                    if rl or retroactive:
                        if end:
                            user_data = c.execute(
                                f"SELECT t, gn, pts, wpm, tid FROM t_{user} WHERE t < ?",
                                (end, ))
                        else:
                            user_data = c.execute(
                                f"SELECT t, gn, pts, wpm, tid FROM t_{user}")
                    elif pl:
                        if end:
                            user_data = c.execute(
                                f"SELECT t, gn, pts, wpm, tid FROM t_{user} WHERE t > ? AND t < ?",
                                (1_501_113_600, end))
                        else:
                            user_data = c.execute(
                                f"SELECT t, gn, pts, wpm, tid FROM t_{user} WHERE t > ?",
                                (1_501_113_600, ))
                for i in user_data:
                    temp_x.append(datetime.datetime.fromtimestamp(i[0]))
                    if rl:
                        temp_y.append(i[1] - first_gn + 1)
                    elif pl:
                        pts = i[2]
                        if retroactive and not pts:
                            pts = calculate_pts(i[4], i[3])
                        cur_pts += pts
                        temp_y.append(cur_pts)
                data_x.append(temp_x)
                data_y.append(temp_y)
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        ax = plt.subplots()[1]
        count = 0
        for i in range(0, len(args)):
            try:
                temp_x = reduce_list(data_x[i])
                temp_y = reduce_list(data_y[i])
                if len(temp_x) < 2:
                    raise IndexError
                added_x, added_y = [], []
                if start:
                    added_x = [datetime.datetime.fromtimestamp(start)]
                    added_y = [0]
                added_x += temp_x
                added_y += temp_y
                if not end:
                    added_x += [datetime.datetime.fromtimestamp(today)]
                    added_y += [temp_y[-1]]
                ax.plot(added_x, added_y, label=args[i])
                count += 1
            except IndexError:
                pass

        if not count:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).missing_information(
                               'No users had races specified time interval'))
            return

        title = f"{args[0].lower()}'s " if len(args) == 1 else ''
        if retroactive: units = f"Retroactive {units}"
        title += f"{units} Over Time"
        segment = ''
        if start:
            segment = f"""\n(Since {datetime.datetime.fromtimestamp(start)
                                   .strftime("%B %-d, %Y")})"""
        if end:
            segment = f"""\n(Until {datetime.datetime.fromtimestamp(end)
                                   .strftime("%B %-d, %Y")})"""
        if start and end:
            segment = (f"""\n(From {datetime.datetime.fromtimestamp(start)
                                   .strftime("%B %-d, %Y")} to """
                       f"""{datetime.datetime.fromtimestamp(end)
                            .strftime("%B %-d, %Y")})""")
        title += segment

        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_xticks(ax.get_xticks()[::2])
        formatter = mdates.DateFormatter("%b. %-d, '%y")
        ax.xaxis.set_major_formatter(formatter)

        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(self.large_num_formatter))
        ax.set_ylabel(units)
        plt.grid(True)

        if len(data_y) > 1:
            plt.tight_layout(rect=[0, 0, 0.75, 1])
            ax.legend(loc='upper left',
                      bbox_to_anchor=(1.03, 1),
                      shadow=True,
                      ncol=1)
        file_name = f"{units} Over Time.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        over_time_picture = discord.File(file_name, filename=file_name)

        await ctx.send(file=over_time_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('improvement'))
    async def improvement(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) == 1: args += ('races', )

        if len(args) != 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <time/races>"))
            return

        player = args[0].lower()
        if args[1].lower() not in ['time', 'races']:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               'Must provide a valid category: `time/races`'))
            return

        if args[1].lower() == 'time':
            q_category = 't'
            category = 'Time'
        else:
            q_category = 'gn'
            category = 'Races'

        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        data_x, data_y, max_point = [], [], 0
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(
                f"SELECT wpm, {q_category} FROM t_{player} ORDER by {q_category}"
            )
            for row in player_data:
                if q_category == 't':
                    data_x.append(datetime.datetime.fromtimestamp(row[1]))
                else:
                    data_x.append(row[1])
                row_wpm = row[0]
                max_point = max(max_point, row_wpm)
                data_y.append(row_wpm)
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        length = len(data_x)
        if length < 15:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    f"`{ctx.invoked_with}` requires 15≤ races to generate a graph"
                ))
            return

        elif length < 7500:
            sma = length // 15
        else:
            sma = 500
        moving_y = [sum(data_y[0:sma]) / sma]
        moving_y += [sum(data_y[i - sma:i]) / sma for i in range(sma, length)]
        moving_x = [data_x[0]] + data_x[sma:]
        moving_y = reduce_list(moving_y)
        moving_x = reduce_list(moving_x)

        max_line = max(moving_y)

        ax = plt.subplots()[1]
        ax.scatter(data_x, data_y, marker='.', alpha=0.1, color='#000000')
        ax.plot(moving_x, moving_y, color='#FF0000')
        ax.set_title(
            f"{player}'s WPM Over {category}\n(Moving Average of {sma} Races)")

        if q_category == 't':
            ax.set_xlabel('Date')
            ax.set_xticks(ax.get_xticks()[::2])
            formatter = mdates.DateFormatter("%b. %-d '%y")
            ax.xaxis.set_major_formatter(formatter)
        else:
            ax.xaxis.set_major_formatter(
                ticker.FuncFormatter(self.large_num_formatter))
            ax.set_xlabel('Race #')

        if max_point > 2 * max_line: ax.set_ylim(0, 2 * max_line)
        ax.set_ylabel('WPM')
        plt.grid(True)
        file_name = f"WPM Over {category}.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        races_over_time_picture = discord.File(file_name, filename=file_name)

        await ctx.send(file=races_over_time_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.cooldown(50, 100, commands.BucketType.default)
    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('adjustedgraph') + ['matchgraph'] +
                      get_aliases('matchgraph'))
    async def adjustedgraph(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)
        account = account_information(user_id)
        universe = account['universe']

        ag = ctx.invoked_with.lower() in ['adjustedgraph'
                                          ] + get_aliases('adjustedgraph')
        mg = ctx.invoked_with.lower() in ['matchgraph'
                                          ] + get_aliases('matchgraph')

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
                    if race_num < 0: last_race += race_num
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
                player = args[0].lower()
                replay_url = Urls().result(player, int(args[1]), universe)
                urls = [replay_url]
            except ValueError:
                await ctx.send(content=f"<@{user_id}>",
                               embed=Error(ctx, ctx.message).incorrect_format(
                                   '`race_num` must be a positive integer'))
                return

        def helper_scraper(soup):
            escapes = ''.join([chr(char) for char in range(1, 32)])
            try:
                typinglog = re.sub(
                    '\\t\d', 'a',
                    re.search(
                        r'typingLog\s=\s"(.*?)";',
                        response).group(1).encode().decode(
                            'unicode-escape').translate(escapes)).split('|')
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
            player = soup.select(
                "a[class='userProfileTextLink']")[0]["href"][13:]
            race_details = soup.select("table[class='raceDetails']")[0].select(
                'tr')
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
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information((
                    '`var typingLog` was not found in the requested URL;\n'
                    f"Currently linked to the {href_universe(universe)} universe\n\n"
                )))
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
            data = {
                player: [
                    unl, unl[-1], times[0],
                    replay_url.split('https://data.typeracer.com/pit/')[1]
                ]
            }
            for opponent in opponents:
                try:
                    urls = ["https://data.typeracer.com/pit/" + opponent]
                    response = (await fetch(urls, 'text'))[0]
                    if not response:
                        raise KeyError
                    soup = BeautifulSoup(response, 'html.parser')
                    times = helper_scraper(soup)
                    unl = wpm_helper(times)
                    data.update({
                        opponent.split('|')[1][3:]:
                        [unl, unl[-1], times[0], opponent]
                    })
                except:
                    pass
            data = {
                k: v
                for k, v in sorted(
                    data.items(), key=lambda x: x[1][1], reverse=True)
            }

        if ag:
            title_1 = f"Adjusted WPM Over {player}'s {num_to_text(race_number)} Race"
            title = f"{title_1}\nUniverse: {universe}"
        else:
            title_1 = f"Unlagged WPM Over {player}'s {num_to_text(race_number)} Race"
            title = f"{title_1}\nUniverse: {universe}"

        description = f"**Quote**\n\"{race_text[0:1008]}\""

        text_length = len(race_text) > 9

        ax = plt.subplots()[1]
        if ag:
            if text_length:
                starts = data_y[0:9]
                remaining = data_y[9:]
            ax.plot([i for i in range(1, len(data_y) + 1)], data_y)
        else:
            value, i, starts, remaining = '', 0, [], []
            for name, data_y in data.items():
                wpm_ = data_y[0]
                if text_length:
                    starts += wpm_[0:9]
                    remaining += wpm_[9:]
                ax.plot([i for i in range(1, len(wpm_) + 1)], wpm_, label=name)
                segment = (
                    f"{NUMBERS[i]} [{name}]({f'https://data.typeracer.com/pit/{data_y[3]}'})"
                    f" - {round(data_y[1], 2)} WPM ({f'{data_y[2]:,}'}ms start)\n"
                )
                if len(value + segment) <= 1024:
                    value += segment
                i += 1
            if len(data) > 1:
                plt.tight_layout(rect=[0.02, 0.02, 0.75, 0.92])
                ax.legend(loc='upper left',
                          bbox_to_anchor=(1.03, 1),
                          shadow=True,
                          ncol=1)

        ax.set_title(title)
        ax.set_xlabel('Keystrokes')
        ax.set_ylabel('WPM')
        plt.grid(True)
        file_name = 'WPM Over Race.png'

        embed = discord.Embed(title=title_1,
                              color=discord.Color(MAIN_COLOR),
                              description=description,
                              url=replay_url)
        if text_length:
            max_starts, max_remaining = max(starts), max(remaining)
            messed_up_scaled = max_starts > max_remaining
            if messed_up_scaled:
                if ctx.invoked_with[-1] != '*':
                    ax.set_ylim(0, 1.05 * max_remaining)
                    embed.set_footer(
                        text=
                        f"The `y`-axis has been scaled; run `{ctx.invoked_with}*` to see the entire graph"
                    )

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        plt.close()

        file_ = discord.File(file_name, filename='image.png')
        embed.set_image(url='attachment://image.png')
        if mg:
            embed.add_field(name='Ranks (ranked by unlagged WPM)',
                            value=value[:-1])
        os.remove(file_name)

        await ctx.send(file=file_, embed=embed)
        return

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('pbgraph'))
    async def pbgraph(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) <= 1: args = check_account(user_id)(args)

        if len(args) == 1: args += ('races', )

        if len(args) != 2:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).parameters(
                               f"{ctx.invoked_with} [user] <time/races>"))
            return

        player = args[0].lower()
        if args[1].lower() not in ['time', 'races']:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).incorrect_format(
                               'Must provide a valid category: `time/races`'))
            return

        if args[1].lower() == 'time':
            q_category = 't'
            category = 'Time'
        else:
            q_category = 'gn'
            category = 'Races'

        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        data_x, data_y = [], []
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(
                f"SELECT {q_category}, wpm FROM t_{player}")
            temp_x, temp_y = player_data.fetchone()
            if q_category == 't':
                data_x.append(datetime.datetime.fromtimestamp(temp_x))
            else:
                data_x.append(temp_x)
            data_y.append(temp_y)
            for row in player_data:
                if data_y[-1] > row[1]: continue
                if q_category == 't':
                    data_x.append(datetime.datetime.fromtimestamp(row[0]))
                else:
                    data_x.append(row[0])
                data_y.append(row[1])
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        data_x = reduce_list(data_x)
        data_y = reduce_list(data_y)

        ax = plt.subplots()[1]
        ax.plot(data_x, data_y)
        ax.set_title(f"{player}'s PBs Over {category}")

        if q_category == 't':
            ax.set_xlabel('Date')
            ax.set_xticks(ax.get_xticks()[::2])
            formatter = mdates.DateFormatter("%b. %-d '%y")
            ax.xaxis.set_major_formatter(formatter)
        else:
            ax.set_xlabel('Race #')

        ax.set_ylabel('WPM')
        plt.grid(True)
        file_name = f"PBs Over {category}.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False)
        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        races_over_time_picture = discord.File(file_name, filename=file_name)

        await ctx.send(file=races_over_time_picture)
        os.remove(file_name)
        plt.close()
        return

    def large_num_formatter(self, x, pos):
        if x >= 1_000_000:
            return f"{round(x / 1_000_000, 1)}M"
        elif x >= 1_000:
            return f"{round(x / 1_000, 1)}K"
        else:
            return x

    @commands.check(
        lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('compare'))
    async def compare(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 1: args = check_account(user_id)(args)

        if len(args) != 2:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx, ctx.message).parameters(f"{ctx.invoked_with} [user_1] [user_2]"))
            return

        player = args[0].lower()
        player_ = args[1].lower()
        if escape_sequence(player):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player}**]({Urls().user(player, 'play')}) "
                     "doesn't exist")))
            return

        if escape_sequence(player_):
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    (f"[**{player_}**]({Urls().user(player_, 'play')}) "
                     "doesn't exist")))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            player_data = c.execute(
                f"SELECT tid, MAX(wpm) FROM t_{player} GROUP BY tid ORDER BY wpm"
            ).fetchall()
            player_data_ = c.execute(
                f"SELECT tid, MAX(wpm) FROM t_{player_} GROUP BY tid ORDER BY wpm"
            ).fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message).not_downloaded())
            return
        conn.close()

        player_dict = dict()
        for text in player_data:
            player_dict.update({
                text[0]: text[1]
            })

        first_player, second_player = [], []
        for text in player_data_:
            if player_dict.get(text[0], -1) > 0:
                difference = text[1] - player_dict[text[0]]
                if difference == 0: pass
                elif difference < 0:
                    first_player.append(-1 * difference)
                else:
                    second_player.append(difference)

        if len(first_player) + len(second_player) == 0:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                                 .missing_information(f"**{player}** and **{player_}** have no texts in common"))
            return

        fig, (ax, ax_) = plt.subplots(1, 2, sharey=True)
        if first_player:
            first_max = max(first_player)
        else:
            first_max = 0
        if second_player:
            second_max = max(second_player)
        else:
            second_max = 0

        if int(first_max) // 10 == 0:
            patches = ax.hist(first_player, bins=1, orientation='horizontal')[2]
        else:
            patches = ax.hist(first_player, bins=int(first_max) // 10, orientation='horizontal')[2]
        if int(second_max) // 10 == 0:
            patches_ = ax_.hist(second_player, bins=1, orientation='horizontal')[2]
        else:
            patches_ = ax_.hist(second_player, bins=int(second_max) // 10, orientation='horizontal')[2]

        ax.yaxis.tick_left()
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_ylabel('Difference (WPM)')
        ax.grid()
        ax.set_title(player)

        ax_.grid()
        ax_.set_title(player_)

        max_xlim = max(ax.get_xlim()[1], ax_.get_xlim()[1])
        ax.set_xlim(0, max_xlim)
        ax.set_xlim(ax.get_xlim()[::-1])
        ax_.set_xlim(0, max_xlim)

        title = f"{player} vs. {player_} Text Bests Comparison"
        plt.subplots_adjust(wspace=0, hspace=0)
        file_name = f"{player}_{player_}_text_bests_comparison.png"

        graph_colors = get_graph_colors(user_id)
        graph_color(ax, graph_colors, False, patches)
        graph_color(ax_, graph_colors, False, patches)

        to_rgba = lambda x: (x // 65536 / 255,
                         ((x % 65536) // 256) / 255, x % 256 / 255)

        if graph_colors['text']:
            fig.suptitle(title, color=to_rgba(graph_colors['text']))
            fig.text(0.5, 0.025, 'Frequency (Texts)', ha='center', color=to_rgba(graph_colors['text']))
        else:
            fig.suptitle(title)
            fig.text(0.5, 0.025, 'Frequency (Texts)', ha='center')

        plt.savefig(file_name, facecolor=ax.figure.get_facecolor())
        plt.close()

        embed = discord.Embed(title=title, color=MAIN_COLOR)
        file_ = discord.File(file_name, filename=file_name)
        embed.set_image(url=f"attachment://{file_name}")
        embed.add_field(name=player,
                        value=f"**{f'{len(first_player):,}'}** texts (+**{f'{round(sum(first_player), 2):,}'}** WPM)")
        embed.add_field(name=player_,
                        value=f"**{f'{len(second_player):,}'}** texts (+**{f'{round(sum(second_player), 2):,}'}** WPM)")
        await ctx.send(file=file_, embed=embed)
        os.remove(file_name)
        return


def setup(bot):
    bot.add_cog(Graphs(bot))
