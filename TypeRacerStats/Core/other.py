import datetime
import json
import random
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import ART_JSON, CLIPS_JSON
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.supporter import get_supporter, check_dm_perms
from TypeRacerStats.Core.Common.urls import Urls

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('unixreference'))
    async def unixreference(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) > 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} <timestamp>"))
            return

        if len(args) == 0:
            embed = discord.Embed(title = "Unix Timestamp Conversions",
                                  color = discord.Color(MAIN_COLOR))
            embed.set_footer(text = "All converted times are in UTC")
            embed.add_field(name = "Times",
                            value = ('1.25e9 - August 11, 2009\n'
                                     '1.30e9 - March 13, 2011\n'
                                     '1.35e9 - October 12, 2012\n'
                                     '1.40e9 - May 13, 2014\n'
                                     '1.45e9 - December 13, 2015\n'
                                     '1.50e9 - July 14, 2017\n'
                                     '1.55e9 - February 12, 2019\n'
                                     '1.60e9 - September 13, 2020\n'
                                     '1.65e9 - April 15, 2022'))
            await ctx.send(embed = embed)
            return

        try:
            time = int(args[0])
            await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                                 description = datetime.datetime.fromtimestamp(time)
                                                               .strftime("%B %d, %Y, %I:%M:%S")))
            return
        except ValueError:
            try:
                scientific_notation_lst = args[0].lower().split('e')
                await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                                     description = datetime.datetime.fromtimestamp(
                                                                   float(scientific_notation_lst[0]) * 10 ** (int(scientific_notation_lst[1])))
                                                                   .strftime("%B %d, %Y, %I:%M:%S")))
                return
            except:
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format('`timestamp` must be an integer or scientific notation (e.g. 1.0365e9)'))
                return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('serverinfo'))
    async def serverinfo(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) != 0:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with}"))
            return

        embed = discord.Embed(title = f"Server Information for {ctx.guild.name}",
                              color = discord.Color(MAIN_COLOR),
                              description = ctx.guild.description)
        embed.set_thumbnail(url = ctx.guild.icon_url)
        embed.add_field(name = 'Stats',
                        value = (f"**Owner:** <@{ctx.guild.owner_id}>\n"
                                 f"**Region:** {ctx.guild.region}\n"
                                 f"**Created At:** {ctx.guild.created_at}\n"
                                 f"**Member Count:** {f'{ctx.guild.member_count:,}'}\n"
                                 f"**Text Channels:** {f'{len(ctx.guild.text_channels):,}'}\n"
                                 f"**Roles:** {f'{len(ctx.guild.roles):,}'}"))
        embed.set_image(url = ctx.guild.banner_url)

        await ctx.send(embed = embed)
        return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('art'))
    async def art(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) > 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} <artist>"))
            return

        with open(ART_JSON, 'r') as jsonfile:
            works = json.load(jsonfile)

        artists = list(works.keys())
        if len(args) == 1:
            artist = args[0].lower()
            if artist == '*':
                await ctx.send(file = discord.File(ART_JSON, f"typeracer_art.json"))
                return
            if artist not in artists:
                artists_ = ''
                for artist_ in artists:
                    artists_ += f"`{artist_}`, "
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format(f"Must provide a valid artist: {artists_[:-2]}"))
                return
            works, trid = works[artist]['art'], works[artist]['trid']
            work = random.choice(works)
        else:
            works_ = []
            for key, value in works.items():
                for art_work in value['art']:
                    works_.append({
                        'artist': key,
                        'trid': value['trid'],
                        'title': art_work['title'],
                        'url': art_work['url']
                    })
            work = random.choice(works_)
            artist, trid = work['artist'], work['trid']

        title = work['title'] if work['title'] else "Untitled"

        embed = discord.Embed(title = title,
                              color = discord.Color(MAIN_COLOR))
        embed.set_author(name = artist,
                         url = Urls().user(trid, 'play'),
                         icon_url = Urls().thumbnail(trid))
        embed.set_image(url = work['url'])

        await ctx.send(embed = embed)
        return

    @commands.check(lambda ctx: check_dm_perms(ctx, 4))
    @commands.command(aliases = get_aliases('clip'))
    async def clip(self, ctx, *args):
        user_id = ctx.message.author.id
        MAIN_COLOR = get_supporter(user_id)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters(f"{ctx.invoked_with} [clip]"))
            return

        with open(CLIPS_JSON, 'r') as jsonfile:
            clips = json.load(jsonfile)

        if len(args) == 1:
            clip = args[0].lower()
            if clip == '*':
                await ctx.send(file = discord.File(CLIPS_JSON, f"clips.json"))
                return
            try:
                clip_url = clips[clip]
            except KeyError:
                calls = list(clips.keys())
                calls_ = ''
                for clip_ in calls:
                    calls_ += f"`{clip_}`, "
                await ctx.send(content = f"<@{user_id}>",
                               embed = Error(ctx, ctx.message)
                                       .incorrect_format(f"Must provide a valid clip: {calls_[:-2]}"))
                return

        await ctx.send(clip_url)
        return

def setup(bot):
    bot.add_cog(Other(bot))
