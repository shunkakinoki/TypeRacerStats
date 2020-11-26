import sys
import time
import discord
from discord.ext import commands
import sqlite3
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_ADMIN_IDS
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
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
            user_data = c.execute(f"SELECT * FROM {player} ORDER BY gn DESC LIMIT 1")
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
                c.execute(f"CREATE TABLE {player} (gn, t, tid, wpm, pts)")
        if races_remaining > 5000 and not user_id in BOT_ADMIN_IDS:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .lacking_permissions(('Data request exceeds 5,000 races. '
                                                         'Have a bot admin run the command.')))
            return
        
        start_ = time.time()
        await ctx.send(embed = discord.Embed(title = 'Data Request',
                                             color = discord.Color(MAIN_COLOR),
                                             description = ('Request successful\n'
                                                            f"Estimated download time: {seconds_to_text(0.00441911 * races_remaining + 0.75)}")))

        try:
            data = await fetch_data(player, 'play', last_race_timestamp)
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

def setup(bot):
    bot.add_cog(GetData(bot))
