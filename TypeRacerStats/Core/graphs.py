import os
import sqlite3
import sys
import time
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
sys.path.insert(0, '')
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence
from TypeRacerStats.Core.Common.urls import Urls

class Graphs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        ax.set_title(f"{player}'s WPM Histogram'")
        file_name = f"{player} WPM.png"
        plt.savefig(file_name)
        wpm_picture = discord.File(file_name, filename = file_name)
        await ctx.send(file = wpm_picture)
        os.remove(file_name)
        plt.close()
        return

    @commands.cooldown(3, 15, commands.BucketType.user)
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
                temp = [i[0] for i in user_data.fetchall()]
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
                user_data = c.execute(f"SELECT t, gn FROM t_{user}")
                temp_x, temp_y = [], []
                for i in user_data.fetchall():
                    temp_x.append(i[0])
                    temp_y.append(i[1])
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
        ax.plot(data_x[0] + [today], data_y[0] + [data_y[0][-1]], label = args[0])
        for i in range(1, len(args)):
            ax.plot(data_x[i] + [today], data_y[i] + [data_y[i][-1]], label = args[i])
        ax.set_title('Races Over Time')
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
        today = time.time()

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
        if length < 5000:
            sma = length // 10
        else:
            sma = 500
        fragment = length % sma
        moving_y = [sum(data_y[i:i + sma]) / sma for i in range(0, length - fragment - sma)]
        moving_x = data_x[:-fragment - sma] + [data_x[-1]]
        if fragment:
            moving_y += [sum(data_y[-fragment:]) / fragment]
        else:
            moving_y += [sum(data_y[-sma:]) / sma]

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

def setup(bot):
    bot.add_cog(Graphs(bot))