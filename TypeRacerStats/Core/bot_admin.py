import csv
import os
import sqlite3
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_OWNER_IDS, BOT_ADMIN_IDS, USERS_KEY
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence

class BotAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['perish', 'unban', 'banned'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_ADMIN_IDS and check_banned_status(ctx))
    async def ban(self, ctx, *args):
        user_id = ctx.message.author.id

        if ctx.invoked_with == 'banned':
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()

            banned_users = c.execute(f"SELECT * FROM {USERS_KEY} WHERE banned = 1").fetchall()
            conn.close()

            description, banned = '', [['ID']]
            for i, user in enumerate(banned_users):
                id_ = user[0]

                if i < 10:
                    description += f"**{i + 1}.** <@{id_}>\n"
                banned.append([id_])

            description = description[:-1]
            embed = discord.Embed(title = 'Banned Users',
                                  color = discord.Color(0),
                                  description = description)

            if len(banned) > 10:
                with open('banned_users.csv', 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(banned)

                file_ = discord.File('banned_users.csv', 'banned_users.csv')

                await ctx.send(file = file_, embed = embed)
                os.remove('banned_users.csv')
                return

            await ctx.send(embed = embed)
            return

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [discord_id]"))
            return

        def perms(id_):
            if id_ in BOT_OWNER_IDS:
                return 2
            if id_ in BOT_ADMIN_IDS:
                return 1
            return 0

        try:
            if len(args[0]) > 18 or escape_sequence(args[0]):
                raise ValueError
            discord_id = int(args[0])
            if perms(discord_id) >= perms(user_id):
                raise commands.CheckFailure
                return
        except ValueError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"<@{args[0]}> is not a valid Discord ID"))
            return

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT * FROM {USERS_KEY} WHERE id = ?", (discord_id,)).fetchall()
            if not user_data:
                toggled_to = True
                c.execute(f"INSERT INTO {USERS_KEY} (id, banned) VALUES(?, ?)", (discord_id, toggled_to,))
            else:
                toggled_to = not user_data[0][1]
                c.execute(f"UPDATE {USERS_KEY} SET banned = ? WHERE id = ?", (toggled_to, discord_id,))
            conn.commit()
            conn.close()
        except sqlite3.OperationalError:
            c.execute(f"CREATE TABLE {USERS_KEY} (id integer PRIMARY KEY, banned BOOLEAN)")
            conn.close()
            return

        setting = 'banned' if toggled_to else 'unbanned'
        await ctx.send(embed = discord.Embed(color = discord.Color(0),
                                             description = (f"<@{discord_id}> has been **{setting}**\n"
                                                            'from using <@742267194443956334>')))
        return

def setup(bot):
    bot.add_cog(BotAdmin(bot))
