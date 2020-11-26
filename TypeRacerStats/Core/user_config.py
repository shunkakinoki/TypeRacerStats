import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import UNIVERSES_FILE_PATH
from TypeRacerStats.Core.Common.accounts import load_accounts
from TypeRacerStats.Core.Common.accounts import update_accounts
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.formatting import href_universe
from TypeRacerStats.Core.Common.prefixes import get_prefix
from TypeRacerStats.Core.Common.prefixes import load_prefixes
from TypeRacerStats.Core.Common.prefixes import update_prefixes
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.urls import Urls

class UserConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 1, commands.BucketType.default)
    @commands.command(aliases = get_aliases('changeprefix'))
    @commands.check(lambda ctx: ctx.message.author.guild_permissions.administrator)
    async def changeprefix(self, ctx, prefix):
        prefixes = load_prefixes()
        prefixes[str(ctx.guild.id)] = prefix
        update_prefixes(prefixes)
        await ctx.send(f"updated prefix to {prefix}")

    @commands.cooldown(1, 3, commands.BucketType.default)
    @commands.command(aliases = get_aliases('register'))
    async def register(self, ctx, *args):
        user_id = str(ctx.message.author.id)
        invalid = False

        if len(args) != 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message).parameters(f"{ctx.invoked_with} [typeracer_username]"))
            return
        player = args[0].lower()
        urls = [Urls().get_user(player, 'play')]
        if len(player) > 31:
            invalid = True
        try:
            test_response = await fetch(urls, 'json')
        except:
            invalid = True
        if invalid:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information('`typeracer_username` must be a TypeRacer username'))
            return
        accounts = load_accounts()

        try:
            accounts[user_id]['main'] = player
        except KeyError:
            accounts.update({
                user_id: {
                    'main': player,
                    'alts': [],
                    'desslejusted': False,
                    'speed': 'lag',
                    'universe': 'play'
                }
            })

        update_accounts(accounts)

        await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                             description = (f"<@{user_id}> has been linked to [**{player}**]"
                                                            f"(https://data.typeracer.com/pit/profile?user={player})")))

    @commands.cooldown(1, 1, commands.BucketType.default)
    @commands.command(aliases = get_aliases('setuniverse'))
    async def setuniverse(self, ctx, *args):
        user_id = str(ctx.message.author.id)
        invalid = False

        if len(args) > 1:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message).parameters(f"{ctx.invoked_with} [universe]"))
            return
        
        if len(args) == 0:
            args = ('play',)
        universe = args[0].lower()
        if len(universe) > 50:
            invalid = True
        else:
            with open(UNIVERSES_FILE_PATH, 'r') as txtfile:
                universes = txtfile.read().split('\n')
            if not universe in universes:
                invalid = True
        if invalid:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .incorrect_format(('`universe` must be a [TypeRacer universe]'
                                                      '(http://typeracerdata.com/universes)')))
            return

        accounts = load_accounts()

        try:
            accounts[user_id]['universe'] = universe
        except KeyError:
            await ctx.send(content = f"<@{user_id}>",
                           embed = Error(ctx, ctx.message)
                                   .missing_information(('Discord account must be linked to TypeRacer account with '
                                                         f"`{get_prefix(ctx, ctx.message)}register [typeracer_username]`")))
            return

        update_accounts(accounts)

        await ctx.send(embed = discord.Embed(color = discord.Color(MAIN_COLOR),
                                             description = (f"<@{user_id}> has been linked to the {href_universe(universe)} universe")))

def setup(bot):
    bot.add_cog(UserConfig(bot))
