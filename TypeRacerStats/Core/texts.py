from TypeRacerStats.Core.Common.utility import predicate
from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.scrapers import scrape_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.file_paths import TEXTS_FILE_PATH_CSV
from TypeRacerStats.config import BOT_ADMIN_IDS, MAIN_COLOR, TR_INFO, TR_GHOST
import csv
import sys
import time
import discord
from discord.ext import commands
import Levenshtein
sys.path.insert(0, '')


class Texts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('search'))
    async def search(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [3≤ words]"))
            return
        elif len(args) < 3 and not user_id in BOT_ADMIN_IDS:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [3≤ words]"))
            return

        orig_query = ' '.join(args)
        query = orig_query.lower()
        embed = discord.Embed(title=f"Results for \"{orig_query}\"",
                              color=discord.Color(MAIN_COLOR))
        embed.set_footer(text='Page 1')

        texts, messages = [], []
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                texts.append([row[0], row[1], row[2]])

        count = 0
        embed_count = 0
        for i, cur in enumerate(texts):
            try:
                start_index = cur[1].lower().index(query)
                query_length = len(query)
                text = cur[1]
                formatted = (f"{text[0:start_index]}**"
                             f"{text[start_index:start_index + query_length]}**"
                             f"{text[start_index + query_length:]}")

                value_1 = f"\"{formatted}\" "
                value_2 = (f"[{TR_INFO}]({Urls().text(cur[0])}) "
                           f"[{TR_GHOST}]({cur[2]})")
                value = value_1 + value_2
                if len(value) > 1024:
                    value_1 = value_1[0:1019 - len(value_2)]
                    value = value_1 + "…\"" + value_2

                embed.add_field(name=f"Race Text ID: {cur[0]}",
                                value=value,
                                inline=False)
                count += 1
                if count == 5:
                    messages.append(embed)
                    embed_count += 1
                    count = 0
                    embed = discord.Embed(title=f"More Results for \"{orig_query}\"",
                                          color=discord.Color(MAIN_COLOR))
                    embed.set_footer(text=f"Page {embed_count + 1}")
            except:
                continue

        if count == 0 and embed_count == 0:
            embed = discord.Embed(title=f"No results found for \"{orig_query}\"",
                                  color=discord.Color(MAIN_COLOR))
            await ctx.send(embed=embed)
            if count == 0:
                return
            return
        messages.append(embed)

        index = 0
        msg = None
        action = ctx.send
        time_ = time.time()

        while time.time() - time_ < 5 and embed_count > 1:
            res = await action(embed=messages[index])
            if res:
                msg = res
            l = index != 0
            r = index != len(messages) - 1
            await msg.add_reaction('◀️')
            await msg.add_reaction('▶️')
            react, user = await self.bot.wait_for('reaction_add', check=predicate(msg, l, r, user_id))
            if react.emoji == '◀️':
                index -= 1
            elif react.emoji == '▶️':
                index += 1
            action = msg.edit

        if embed_count <= 1:
            await ctx.send(embed=messages[0])
        return

    @commands.cooldown(3, 25, commands.BucketType.user)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('levenshtein'))
    async def levenshtein(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 0:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [≤40 chars]"))
            return

        query = ' '.join(args)
        query_length = len(query)
        if query_length > 40 and not user_id in BOT_ADMIN_IDS:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [≤40 chars]"))
            return

        texts = []
        with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                text = row[1]
                if query_length >= len(text):
                    texts.append(
                        [row[0], text, row[2], Levenshtein.distance(query, text), 0])
                else:
                    min_index = 0
                    min_distance = 10000000
                    for i in range(0, len(text) - query_length):
                        cur_distance = Levenshtein.distance(
                            query, text[i:i + query_length])
                        if cur_distance < min_distance:
                            min_distance = cur_distance
                            min_index = i
                        if cur_distance == 0:
                            min_distance = cur_distance
                            min_index = i
                            break
                    texts.append(
                        [row[0], text, row[2], min_distance, min_index])

        if len(texts) > 5:
            levenshtein_sorted = sorted(texts, key=lambda x: x[3])[0:5]
        else:
            levenshtein_sorted = sorted(texts, key=lambda x: x[3])

        embed = discord.Embed(title=("Texts With Smallest Levenshtein Distance "
                                     f"to \"{query}\" (Length = {query_length})"),
                              color=discord.Color(MAIN_COLOR))
        for cur in levenshtein_sorted:
            min_index = cur[4]
            text = cur[1]

            if len(text) < len(query):
                formatted = f"**{text}**"
            else:
                formatted = (f"{text[0:min_index]}**{text[min_index:min_index + query_length]}"
                             f"**{text[min_index + query_length:]}")

            value_1 = f"\"{formatted}\" "
            value_2 = (f"[{TR_INFO}]({Urls().text(cur[0])}) "
                       f"[{TR_GHOST}]({cur[2]})")
            value = value_1 + value_2
            if len(value) > 1024:
                value_1 = value_1[0:1019 - len(value_2)]
                value = value_1 + "…\"" + value_2
            embed.add_field(name=(f"Levenshtein Distance: {cur[3]} ("
                                  f"{round(100 * cur[3] / query_length, 2)}%)\n"
                                  f"Race Text ID: {cur[0]}"),
                            value=value,
                            inline=False)

        await ctx.send(embed=embed)
        return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4) and check_banned_status(ctx))
    @commands.command(aliases=get_aliases('searchid'))
    async def searchid(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) != 1:
            await ctx.send(content=f"<@{user_id}>",
                           embed=Error(ctx, ctx.message)
                           .parameters(f"{ctx.invoked_with} [text_id]"))
            return

        tid = args[0]
        urls = [Urls().text(tid)]
        text = await fetch(urls, 'read', scrape_text)
        if text[0]:
            value_1 = f"\"{text[0]}\""
            value_2 = f" [{TR_INFO}]({urls[0]})"
            value = value_1 + value_2
            if len(value) > 1024:
                value_1 = value_1[0:1019 - len(value_2)]
                value = value_1 + "…\"" + value_2
            embed = discord.Embed(title=f"Search Result for {tid}",
                                  color=discord.Color(MAIN_COLOR))
            embed.add_field(name=f"Race Text ID: {tid}",
                            value=value,
                            inline=False)
            await ctx.send(embed=embed)
            return

        await ctx.send(content=f"<@{user_id}>",
                       embed=Error(ctx, ctx.message)
                       .incorrect_format(f"{tid} is not a valid text ID"))
        return


def setup(bot):
    bot.add_cog(Texts(bot))
