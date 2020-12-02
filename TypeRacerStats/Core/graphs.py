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
                                   .parameters(f"{ctx.invoked_with} [user] <user_2>...<user_4>"))
            return

        player = args[0]
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

def setup(bot):
    bot.add_cog(Graphs(bot))
