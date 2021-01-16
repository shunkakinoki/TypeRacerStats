import os
import sqlite3
import sys
import discord
from discord.ext import commands
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_TOKEN, DEFAULT_COMMAND_PREFIX, MAINTAIN, TABLE_KEY
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.maintenance import drop_temporary_tables, maintain_players, maintain_top_tens, maintain_text_files
from TypeRacerStats.Core.Common.prefixes import get_prefix, load_prefixes, update_prefixes

os.environ['TZ'] = 'UTC'
bot = commands.Bot(command_prefix = get_prefix, case_insensitive = True)
bot.remove_command('help')

@bot.event
async def on_ready():
    global eugene

    await bot.wait_until_ready()
    await bot.change_presence(activity = discord.Game(name = f"{DEFAULT_COMMAND_PREFIX}help | by e6f4e37l#0785 and keegan#1689"))
    print('TypeRacerStats ready.')

    eugene = await bot.fetch_user(697048255254495312) #Eugene's Discord ID
    await eugene.send(embed = discord.Embed(color = discord.Color(0), title = f"TypeRacerStats Ready."))

    maintain_text_files()

    if MAINTAIN:
        drop_temporary_tables.start()
        maintain_players.start()
        maintain_top_tens.start()

@bot.event
async def on_guild_join(guild):
    guilds = bot.guilds
    server_count = len(guilds)
    people_count = 0
    for guild in guilds:
        try:
            people_count += guild.member_count
        except AttributeError:
            pass
    await eugene.send(embed = discord.Embed(color = discord.Color(0),
                                            title = f"Joined \"{guild.name}\"",
                                            description = f"Serving {f'{people_count:,}'} people in {f'{server_count:,}'} servers"))

    prefixes = load_prefixes()
    prefixes.update({str(guild.id): DEFAULT_COMMAND_PREFIX})
    update_prefixes(prefixes)

@bot.event
async def on_guild_remove(guild):
    guilds = bot.guilds
    server_count = len(guilds)
    people_count = 0
    for guild in guilds:
        try:
            people_count += guild.member_count
        except AttributeError:
            pass
    await eugene.send(embed = discord.Embed(color = discord.Color(0),
                                            title = f"Left \"{guild.name}\"",
                                            description = f"Serving {f'{people_count:,}'} people in {f'{server_count:,}'} servers"))

    prefixes = load_prefixes()
    prefixes.pop(str(guild.id))
    update_prefixes(prefixes)

@bot.event
async def on_command(ctx):
    user_id = ctx.message.author.id
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    try:
        user_data = c.execute(f"SELECT * FROM {TABLE_KEY} WHERE id = ? LIMIT 1", (user_id,)).fetchall()
        if not user_data:
            embed = discord.Embed(title = 'Hello!',
                                  color = discord.Color(0),
                                  description = ("You can get started by using the command `-help`\n\n"
                                                 "To register your TypeRacer account to the bot, you\n"
                                                 "can use `-link [typeracer_username]`; after linking,\n"
                                                 "you don't have to type your username every time."))

            await ctx.send(content = f"<@{user_id}>", embed = embed)
    except sqlite3.OperationalError:
        c.execute(f"CREATE TABLE {TABLE_KEY} (id integer, name, command)")

    c.execute(f"INSERT INTO {TABLE_KEY} (id, name, command) VALUES (?, ?, ?)",
              (user_id,
              f"{ctx.message.author.name}#{ctx.message.author.discriminator}",
              ctx.invoked_with.lower()))
    conn.commit()
    conn.close()
    return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(content = f"<@{ctx.message.author.id}>",
                       embed = Error(ctx, ctx.message)
                               .cooldown((f"Maximum number of `{ctx.invoked_with}`"
                                          ' request(s) are running\nTry again later')))
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(content = f"<@{ctx.message.author.id}>",
                       embed = Error(ctx, ctx.message)
                               .lacking_permissions('You lack the perms for that command'))
        return
    else:
        ctx.command.reset_cooldown(ctx)
        raise error

@bot.event
async def on_command_completion(ctx):
    ctx.command.reset_cooldown(ctx)

if __name__ == '__main__':
    for filename in os.listdir('TypeRacerStats/Core'):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'christmas_2020.py':
            bot.load_extension(f"Core.{filename[:-3]}")

bot.run(BOT_TOKEN)
