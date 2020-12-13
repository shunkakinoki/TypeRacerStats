import sqlite3
import sys
import time
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import escape_sequence, seconds_to_text
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.texts import load_texts_large
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.urls import Urls

class AdvancedStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(20, 100, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('top') + get_aliases('worst') + ['worst'])
    async def top(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) == 1: args = check_account(user_id)(args)

        if len(args) != 2:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [user] [wpm/points]"))
            return

        player = args[0].lower()
        if escape_sequence(player):
            await ctx.send(content = f"<@{user_id}>",
                            embed = Error(ctx, ctx.message)
                                    .missing_information((f"[**{player}**]({Urls().user(player, 'play')}) "
                                    "doesn't exist")))
            return

        categories = ['wpm', 'points']

        if not args[1] in categories:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format('`category` must be `wpm/points`'))
            return

        if args[1] == 'points':
            category = 'pts'
        else:
            category = 'wpm'

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        try:
            if ctx.invoked_with in ['top'] + get_aliases('top'):
                order_by = 'DESC'
            else:
                order_by = 'ASC'
            user_data = c.execute(f"SELECT * FROM t_{player} ORDER BY {category} {order_by} LIMIT 10")
            user_data = user_data.fetchall()
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        embed = discord.Embed(title = f"{player}'s Top {len(user_data)} Races (Lagged)",
                              color = discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))

        category = {'pts': 'points', 'wpm': 'WPM'}[category]
        texts = load_texts_large()
        for i, race in enumerate(user_data):
            value = f"{texts[str(race[2])]} [:cinema:]({Urls().result(player, race[0], 'play')})"
            if category == 'points':
                name = f"{i + 1}. {race[4]} {category} (Race #{f'{race[0]:,}'})"
            else:
                name = f"{i + 1}. {race[3]} {category} (Race #{f'{race[0]:,}'})"
            embed.add_field(name = name,
                            value = value,
                            inline = False)
        await ctx.send(embed = embed)
        return

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.cooldown(20, 100, commands.BucketType.default)
    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('racedetails'))
    async def racedetails(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

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

        texts_length = load_texts_json()
        races, words_typed, chars_typed, points, retro, time_spent = (0,) * 6
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        try:
            user_data = c.execute(f"SELECT * FROM t_{player}")
            first_race = user_data.fetchone()
            first_point_race = 0
            text_id = str(first_race[2])
            races += 1
            words_typed += texts_length[text_id]['word count']
            chars_typed += texts_length[text_id]['length']
            try:
                time_spent += 12 * texts_length[text_id]['length'] / first_race[3]
            except ZeroDivisionError:
                races -= 1
                pass
            if first_race[4] == 0:
                retro += first_race[3] / 60 * texts_length[text_id]['word count']
            else:
                if not first_point_race:
                    first_point_race = first_race[1]
                points += first_race[4]
            first_race = first_race[1]
            for row in user_data:
                text_id = str(row[2])
                races += 1
                words_typed += texts_length[text_id]['word count']
                chars_typed += texts_length[text_id]['length']
                if row[4] == 0:
                    retro += row[3] / 60 * texts_length[text_id]['word count']
                else:
                    if not first_point_race:
                        first_point_race = row[1]
                    points += row[4]
                try:
                    time_spent += 12 * texts_length[text_id]['length'] / row[3]
                except ZeroDivisionError:
                    races -= 1
                    pass
        except sqlite3.OperationalError:
            conn.close()
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .not_downloaded())
            return
        conn.close()

        today = time.time()
        num_days = (today - first_race) / 86400
        num_point_days = (today - first_point_race) / 86400

        embed = discord.Embed(title = f"Race Details for {player}",
                              color = discord.Color(MAIN_COLOR))
        embed.set_thumbnail(url = Urls().thumbnail(player))
        embed.set_footer(text = ('(Retroactive points represent the total number of points '
                                 'a user would have gained, before points were introduced '
                                 'in 2017)'))
        embed.add_field(name = 'Races',
                        value = (f"**Total Races:** {f'{races:,}'}\n"
                                 f"**Average Daily Races:** {f'{round(races / num_days, 2):,}'}\n"
                                 f"**Total Words Typed:** {f'{words_typed:,}'}\n"
                                 f"**Average Words Per Race:** {f'{round(words_typed / races, 2):,}'}\n"
                                 f"**Total Chars Typed:** {f'{chars_typed:,}'}\n"
                                 f"**Average Chars Per Race: **{f'{round(chars_typed / races, 2):,}'}\n"
                                 f"**Total Time Spent Racing:** {seconds_to_text(time_spent)}\n"
                                 f"**Average Time Per Race:** {seconds_to_text(time_spent / races)}"))
        embed.add_field(name = 'Points',
                        value = (f"**Current Points:** {f'{round(points):,}'}\n"
                                 f"**Average Daily Points:** {f'{round(points / num_point_days, 2):,}'}\n"
                                 f"**Average Points Per Race:** {f'{round((points + retro) / races, 2):,}'}\n"
                                 f"**Retroactive Points:** {f'{round(retro):,}'}\n"
                                 f"**Total Points:** {f'{round(points + retro):,}'}"))
        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(AdvancedStats(bot))
