import os
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_TOKEN
from TypeRacerStats.config import DEFAULT_COMMAND_PREFIX
from TypeRacerStats.Core.Common.prefixes import get_prefix
from TypeRacerStats.Core.Common.prefixes import load_prefixes
from TypeRacerStats.Core.Common.prefixes import update_prefixes

os.environ['TZ'] = 'UTC'
bot = commands.Bot(command_prefix = get_prefix, case_insensitive = True)
bot.remove_command('help')

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.change_presence(activity = discord.Game(name = f"{DEFAULT_COMMAND_PREFIX}help | by e6f4e37l#0785 and KeeganT#1689"))
    print('TypeRacerStats ready.')

@bot.event
async def on_guild_join(guild):
    prefixes = load_prefixes()
    prefixes.update({str(guild.id): DEFAULT_COMMAND_PREFIX})
    update_prefixes(prefixes)

@bot.event
async def on_guild_remove(guild):
    prefixes = load_prefixes()
    prefixes.pop(str(guild.id))
    update_prefixes(prefixes)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if ctx.command.name == 'getdata':
            await ctx.send("`getdata` request is currently running, try again later")
        elif ctx.command.name == 'realspeedaverage':
            await ctx.send(f"2≤ `realspeedaverage` requests are running for <@{ctx.message.author.id}>")
    else:
        print(error)

@bot.event
async def on_command_completion(ctx):
    ctx.command.reset_cooldown(ctx)

if __name__ == '__main__':
    for filename in os.listdir('TypeRacerStats/Core'):
        if filename.endswith('.py') and filename != '__init__.py':
            bot.load_extension(f"Core.{filename[:-3]}")

bot.run(BOT_TOKEN)
