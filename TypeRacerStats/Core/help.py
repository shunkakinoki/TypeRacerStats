import json
import os
import discord
from discord.ext import commands
from TypeRacerStats.config import HELP_BLACK
from TypeRacerStats.config import HELP_IMG
from TypeRacerStats.config import SPEED_INDICATORS
from TypeRacerStats.Core.Common.prefixes import get_prefix
from TypeRacerStats.Core.Common.aliases import get_aliases

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.normalized_commands = {}
        self.command_embeds = {}
        self.main_embed = None
        self.info_embed = None

    def create_embeds(self, bot, message):
        command_prefix = get_prefix(bot, message)

        with open(os.path.dirname(__file__) + '/../src/commands.json', 'r') as jsonfile:
            bot_commands = json.load(jsonfile)

        for command in list(bot_commands.values()):
            name = command['name']
            for alias in command['aliases']:
                self.normalized_commands.update({alias: name})
            self.normalized_commands.update({name: name})
            self.command_embeds.update({name: embed_constructor(command, command_prefix)})

        self.main_embed = discord.Embed(title = 'Help Page',
                                        color = discord.Color(HELP_BLACK),
                                        description = (f"**Run `{command_prefix}help [command]` to learn more**\n"
                                                        "`[ ]` represent required paramaters\n"
                                                        "`< >` represent optional parameters"))
        self.main_embed.set_thumbnail(url = HELP_IMG)
        self.main_embed.add_field(name = 'Info Commands',
                                  value = value_formatter(bot_commands['info'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Configuration Commands',
                                  value = value_formatter(bot_commands['configuration'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Basic Commands',
                                  value = value_formatter(bot_commands['basic'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = f"Advanced Commands (all require `{command_prefix}getdata`)",
                                  value = value_formatter(bot_commands['advanced'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Other Commands',
                                  value = value_formatter(bot_commands['other'], command_prefix),
                                  inline = False)
        self.main_embed.set_footer(text = f"Run {command_prefix}help [command] to learn more")

    def create_info_embed(self, bot, message):
        command_prefix = get_prefix(bot, message)

        with open(os.path.dirname(__file__) + '/../info.txt', 'r') as txtfile:
            info = txtfile.read().split('\n\n')
            info = info[0].split('\n') + info[1:]
            info = [i.replace('\\n', '\n').replace('{PFX}', command_prefix) for i in info]

        self.info_embed = discord.Embed(title = info[0],
                                        color = discord.Color(int(info[1])),
                                        description = info[2])
        self.info_embed.set_thumbnail(url = info[3])

        for i in range(4, len(info) - 1):
            paragraph = info[i].split(':::')
            print(paragraph)
            self.info_embed.add_field(name = paragraph[0], value = paragraph[1], inline = False)
        self.info_embed.set_footer(text = info[-1])

    @commands.command(aliases = get_aliases('help'))
    async def help(self, ctx, *args):
        self.create_embeds(ctx, ctx.message)

        if args:
            try:
                await ctx.send(embed = self.command_embeds[self.normalized_commands[''.join(args).lower()]])
                return
            except KeyError:
                await ctx.send(content = f"<@{ctx.message.author.id}> **Command not found. Refer to the commands below:**",
                               embed = self.main_embed)
                return
        await ctx.send(embed = self.main_embed)
        return

    @commands.command(aliases = get_aliases('info'))
    async def info(self, ctx, *args):
        self.create_info_embed(ctx, ctx.message)

        if len(args) != 0: return
        await ctx.send(embed = self.info_embed)

def value_formatter(command_list, command_prefix):
    value = ''

    for command in command_list:
        value += f"`{command_prefix}{command['name']} {command['usage']['general']}`\n"
    return value[:-1]

def embed_constructor(command, command_prefix):
    call = f"{command_prefix}{command['name']}"

    if command['name'] == 'verify' or command['name'] == 'premium':
        embed = discord.Embed(title = f"Help for `{command_prefix}premium` and `{command_prefix}verify`",
                              color = discord.Color(HELP_BLACK),
                              description = (f"`{command_prefix}premium [user]` and"
                                             f" `{command_prefix}verify [verification_code]` - "
                                             f"{command['description']}"))
        embed.add_field(name = "Steps", value = (f"1. Run `{command_prefix}premium [user]`\n"
                                                  "2. Check TypeRacer inbox for a message\n"
                                                 f"3. Run `{command_prefix}verify [verification code]`"))
        return embed

    embed = discord.Embed(title = f"Help for `{call}` {SPEED_INDICATORS[command['speed']]}",
                          color = discord.Colour(HELP_BLACK),
                          description = f"`{call} {command['usage']['general']}` - {command['description']}")
    embed.set_thumbnail(url = HELP_IMG)

    if command['usage']['general']:
        embed.add_field(name = 'Usage',
                        value = f"`{call} {command['usage']['example']}`",
                        inline = False)

    if command['usage']['alt_example']:
        value = ''
        for example in command['usage']['alt_example']:
            value += f"{example['notes']}: `{call} {example['usage']}`\n"
        embed.add_field(name = 'Alternative Usage',
                        value = value[:-1],
                        inline = False)

    if command['aliases']:
        value = ''
        for alias in command['aliases']:
            value += f"`{alias}`, "
        embed.add_field(name = 'Aliases',
                        value = value[:-2],
                        inline = False)

    if command['linked']:
        embed.set_footer(text = 'Command can be used without user parameter if Discord account is linked')

    return embed

def setup(bot):
    bot.add_cog(Help(bot))
