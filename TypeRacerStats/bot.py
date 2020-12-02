import os
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_TOKEN
from TypeRacerStats.config import DEFAULT_COMMAND_PREFIX
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.maintenance import drop_temporary_tables, maintain_players, maintain_top_tens
from TypeRacerStats.Core.Common.prefixes import get_prefix
from TypeRacerStats.Core.Common.prefixes import load_prefixes
from TypeRacerStats.Core.Common.prefixes import update_prefixes

os.environ['TZ'] = 'UTC'
bot = commands.Bot(command_prefix = get_prefix, case_insensitive = True)
bot.remove_command('help')

MAINTAIN = False

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.change_presence(activity = discord.Game(name = f"{DEFAULT_COMMAND_PREFIX}help | by e6f4e37l#0785 and keegan#1689"))
    print('TypeRacerStats ready.')
    if MAINTAIN:
        drop_temporary_tables.start()
        maintain_players.start()
        maintain_top_tens.start()

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
        await ctx.send(content = f"<@{ctx.message.author.id}>",
                       embed = Error(ctx, ctx.message)
                               .cooldown((f"Maximum number of `{ctx.invoked_with}`"
                                          ' request(s) are running\nTry again later')))
    else:
        ctx.command.reset_cooldown(ctx)
        raise error

@bot.event
async def on_command_completion(ctx):
    ctx.command.reset_cooldown(ctx)

if __name__ == '__main__':
    for filename in os.listdir('TypeRacerStats/Core'):
        if filename.endswith('.py') and filename != '__init__.py':
            bot.load_extension(f"Core.{filename[:-3]}")

bot.run(BOT_TOKEN)
