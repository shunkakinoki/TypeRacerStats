import json
import os
import discord
from discord.ext import commands

import sys
sys.path.insert(0, '')
from TypeRacerStats.config import *
from TypeRacerStats.Core.Common.aliases import *
from TypeRacerStats.Core.Common.prefixes import *

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
    prefixes[str(guild.id)] = DEFAULT_COMMAND_PREFIX
    update_prefixes(prefixes)

@bot.event
async def on_guild_remove(guild):
    prefixes = load_prefixes()
    prefixes.pop(str(guild.id))
    update_prefixes(prefixes)

if __name__ == '__main__':
    for filename in os.listdir('TypeRacerStats/Core'):
        if filename.endswith('.py') and filename != '__init__.py':
            bot.load_extension(f"Core.{filename[:-3]}") 

bot.run(BOT_TOKEN)
