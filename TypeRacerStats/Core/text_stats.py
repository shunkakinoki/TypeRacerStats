import csv
import random
import sqlite3
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR, TR_INFO, TR_GHOST
from TypeRacerStats.file_paths import DATABASE_PATH, TEXTS_FILE_PATH_CSV
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.urls import Urls

class TextStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(10, 50, commands.BucketType.default)
    @commands.command(aliases = get_aliases('personalbest'))
    async def personalbest(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0:
            args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [text_id]"))
            return

        player = args[0]
        if len(args) == 2:
            text_id = int(args[1])
        else:
            try:
                urls = [Urls().get_races(player, 'play', 1)]
                text_id = int((await fetch(urls, 'json'))[0][0]['tid'])
            except:
                await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information())
                return

        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if int(row[0]) == text_id:
                    text = row[1]
                    break
                else:
                    continue

        try:
            if len(text) > 1024:
                text = f"\"{text[0:1020]}…\""
            else:
                text = f"\"{text}\""
        except NameError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(f"{text_id} is not a valid text ID"))
            return

        count, sum_, best, best_gn, worst_gn = (0,) * 5
        worst = 100000
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT gn, wpm FROM t_{player} WHERE tid = {text_id}")
            for row in user_data:
                count += 1
                sum_ += row[1]
                if row[1] > best:
                    best_gn, best = row
                if row[1] < worst:
                    worst_gn, worst = row
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        if not count:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(f"**{player}** has not completed the text yet"))
            return

        embed = discord.Embed(title = f"Quote #{text_id} Statistics for {player}",
                              color = discord.Color(MAIN_COLOR),
                              url = Urls().text(text_id))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.add_field(name = 'Quote', value = text, inline = False)
        embed.add_field(name = 'Speeds',
                        value = (f"**Times:** {f'{count:,}'}\n"
                                 f"**Average:** {f'{round(sum_ / count, 2):,}'}\n"
                                 f"**Fastest:** {f'{best:,}'} WPM "
                                 f"(Race #{f'{best_gn}'}) [:cinema:]"
                                 f"({Urls().result(player, 'play', best_gn)})\n"
                                 f"**Slowest:** {f'{worst:,}'} WPM "
                                 f"(Race #{f'{worst_gn}'}) [:cinema:]"
                                 f"({Urls().result(player, 'play', worst_gn)})\n"))

        await ctx.send(embed = embed)
        return

    @commands.cooldown(10, 30, commands.BucketType.default)
    @commands.command(aliases = get_aliases('unraced'))
    async def unraced(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0 or (len(args) == 1 and len(args[0]) < 4):
            args = check_account(user_id)(args)

        if len(args) == 0 or len(args) > 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] <length>"))
            return
        player = args[0]

        if len(args) == 2:
            try:
                length = int(args[1])
                if length < 1 or length > 999:
                    raise ValueError
            except ValueError:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`length` must be a positive integer less than 999'))
                return
        else:
            length = 0

        all_tids, user_tids, texts_data = set(), set(), dict()
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                all_tids.add(int(row[0]))
                texts_data.update(
                    {
                        int(row[0]): {
                            'text': row[1],
                            'ghost': row[2]
                        }
                    }
                )

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            user_data = c.execute(f"SELECT DISTINCT tid FROM t_{player}")
            for row in user_data:
                user_tids.add(row[0])
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        unraced_tids = list(all_tids - user_tids)
        if length:
            unraced_tids = list(filter(lambda x: len(texts_data[x]['text']) < length, unraced_tids))
        if len(unraced_tids) == 0:
            description = f"{player} has completed all texts"
            if length:
                description += f" under length {length}"
            description += '!'
            await ctx.send(embed = discord.Embed(title = 'Nothing to Choose From',
                                                 color = discord.Color(754944),
                                                 description = description))
            return

        title = 'Random Unraced Texts'
        if length:
            title += f" Under Length {length}"
        title += f" for {player} ({f'{len(unraced_tids):,}'} left)"

        embed = discord.Embed(title = title, color = discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))

        try:
            for i in range(0, 5):
                random_tid = random.choice(unraced_tids)
                value_1 = f"\"{texts_data[random_tid]['text']}\""
                value_2 = (f"[{TR_INFO}]({Urls().text(random_tid)}) "
                           f"[{TR_GHOST}]({texts_data[random_tid]['ghost']})")
                value = value_1 + value_2
                if len(value) > 1024:
                    value_1 = value_1[0:1019 - len(value_2)]
                    value = f"{value_1}…\" {value_2}"

                embed.add_field(name = f"{i + 1}. Race Text ID: {random_tid}",
                                value = value,
                                inline = False)
                unraced_tids.remove(random_tid)
        except:
            pass

        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(TextStats(bot))
