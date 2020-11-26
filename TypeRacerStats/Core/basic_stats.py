import time
import sys
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.Core.Common.accounts import account_information
from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import href_universe
from TypeRacerStats.Core.Common.formatting import seconds_to_text
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.urls import Urls

class BasicStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.command(aliases = get_aliases('stats'))
    async def stats(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters('stats [user]'))
            return

        player = args[0].lower()
        urls = [Urls().get_user(player, universe)]
        try:
            user_api = await fetch(urls, 'json')
            user_api = user_api[0]
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                   "doesn't exist")))
            return

        if user_api['country']:
            country = f":flag_{user_api['country']}: "
        else:
            country = ''
        if user_api['name']:
            name = user_api['name']
        else:
            name = ''
        if user_api['lastName']:
            name += f" {user_api['lastName']}"
        if user_api['premium']:
            premium = 'Premium'
        else:
            premium = 'Basic'
        try:
            banned = user_api['tstats']['disqualified']
            if banned == 'false' or not banned:
                banned = ''
            else:
                banned = '\n**Status: **Banned'
        except KeyError:
            banned = ''
        
        urls = [[Urls().trd_user(player, universe), 'json']]
        try:
            trd_user_api = await fetch(urls, 'json')
            trd_user_api = trd_user_api[0]
            textbests = round(float(trd_user_api['account']['wpm_textbests']), 2)
            textsraced =  trd_user_api['account']['texts_raced']
            extra_stats = (f"**Text Bests: **{textbests} WPM\n"
                           f"**Texts Typed: **{textsraced}\n")
        except:
            textbests, textsraced, extra_stats = ('', ) * 3
        
        urls = [Urls().user(player, universe)]
        try:
            response = await fetch(urls, 'text')
            response = response[0]
            soup = BeautifulSoup(response, 'lxml')
            rows = soup.select("table[class='profileDetailsTable']")[0].select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2: continue
                if cells[0].text.strip() == "Racing Since":
                    date_joined = cells[1].text.strip()
            rows = soup.select("table[class='personalInfoTable']")[0].select('tr')
            medal_count = 0
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2: continue
                if cells[0].text.strip() == "Awards":
                    medal_count = len(cells[1].select('a'))
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                                         "doesn't exist")))
            return
        
        if banned:
            color = 0xe0001a
        else:
            color = MAIN_COLOR
        embed = discord.Embed(title = f"{country}{player}",
                              colour = discord.Colour(color),
                              description = f"**Universe:** {href_universe(universe)}",
                              url = urls[0])
        embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
        embed.add_field(name = "General",
                        value = (f"**Name:** {name}\n"
                                 f"**Joined: **{date_joined}\n"
                                 f"**Membership: **{premium}{banned}"),
                        inline = False)
        embed.add_field(name = "Stats",
                        value = (f"""**Races: **{f"{user_api['tstats']['cg']:,}"}\n"""
                                 f"""**Races Won: **{f"{user_api['tstats']['gamesWon']:,}"}\n"""
                                 f"""**Points: **{f"{round(user_api['tstats']['points']):,}"}\n"""
                                 f"""**Full Average: **{round(user_api['tstats']['wpm'], 2)} WPM\n"""
                                 f"""**Fastest Race: **{round(user_api['tstats']['bestGameWpm'], 2)} WPM\n"""
                                 f"""**Captcha Speed: **{round(user_api['tstats']['certWpm'], 2)} WPM\n"""
                                 f"""{extra_stats}**Medals: **{f'{medal_count:,}'}\n"""),
                        inline = False)
        await ctx.send(embed = embed)
        await fetch([Urls().trd_import(player)], 'text')
        return
    
    @commands.command(aliases = get_aliases('lastonline'))
    async def lastonline(self, ctx, *args):
        user_id = ctx.message.author.id
        account = account_information(user_id)
        universe = account['universe']

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters('lastonline [user]'))
        player = args[0].lower()
        try:
            urls = [Urls().get_races(player, universe, 1)]
            response = await fetch(urls, 'json', lambda x: x[0]['t'])
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**](https://data.typeracer.com/pit/race_history?user={player}&universe={universe}) "
                                                         "doesn't exist or has no races in the "
                                                         f"{href_universe(universe)} universe")))
        
        time_difference = time.time() - response[0]
        await ctx.send(embed = discord.Embed(colour = discord.Colour(MAIN_COLOR),
                       description = f"**{player}** last played {seconds_to_text(time_difference)}\nago on the {href_universe(universe)} universe"))
        return

    @commands.cooldown(4, 12, commands.BucketType.user)
    @commands.cooldown(50, 150, commands.BucketType.default)
    @commands.command(aliases = get_aliases('medals'))
    async def medals(self, ctx, *args):
        user_id = ctx.message.author.id

        if len(args) == 0: args = check_account(user_id)(args)

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .parameters('medals [user]'))
        player = args[0].lower()
        try:
            urls = [Urls().user(player, 'play')]
            response = await fetch(urls, 'text')
            soup = BeautifulSoup(response[0], 'lxml')
            rows = soup.select("table[class='personalInfoTable']")[0].select('tr')
        except:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information((f"[**{player}**]({urls[0]}) "
                                                         "doesn't exist")))
            return

        medals = []
        for row in rows:
            cells = row.select('td')
            if len(cells) < 2: continue
            if cells[0].text.strip() == "Awards":
                medals = cells[1].select('img')

        breakdown = {
            "g": {1: 0, 2: 0, 3: 0},
            "d": {1: 0, 2: 0, 3: 0},
            "w": {1: 0, 2: 0, 3: 0},
            "m": {1: 0, 2: 0, 3: 0},
            "y": {1: 0, 2: 0, 3: 0}
        }
        for medal in medals:
            title = medal['title']
            breakdown["g"][int(title[0])] += 1
            breakdown[title[17]][int(title[0])] += 1
        
        general = list(breakdown['g'].values())
        daily = list(breakdown['d'].values())
        weekly = list(breakdown['w'].values())
        monthly = list(breakdown['m'].values())
        yearly = list(breakdown['y'].values())
        if not sum(general):
            embed = discord.Embed(title = f"Medal Stats for {player}",
                                  colour = discord.Colour(MAIN_COLOR),
                                  description = "It's empty here.")
            embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
            await ctx.send(embed = embed)
            return

        embed = discord.Embed(title = f"Medals Stats for {player}",
                              colour=discord.Colour(MAIN_COLOR))
        embed.set_thumbnail(url = f"https://data.typeracer.com/misc/pic?uid=tr:{player}")
        helper_constructor = lambda count: (f"**Total: **{sum(count)}\n"
                                            f":first_place: x {count[0]}\n"
                                            f":second_place: x {count[1]}\n"
                                            f":third_place: x {count[2]}")
        embed.add_field(name = "General",
                        value = helper_constructor(general),
                        inline = False)
        if(sum(daily)):
            embed.add_field(name = "Daily",
                            value = helper_constructor(daily),
                            inline = True)
        if(sum(weekly)):
            embed.add_field(name = "Weekly",
                            value = helper_constructor(daily),
                            inline = True)
        if(sum(monthly)):
            embed.add_field(name = "Monthly",
                            value = helper_constructor(daily),
                            inline = True)
        if(sum(yearly)):
            embed.add_field(name = "Yearly",
                            value = helper_constructor(daily),
                            inline = True)
        await ctx.send(embed = embed)
        return

def setup(bot):
    bot.add_cog(BasicStats(bot))
