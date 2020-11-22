import json
import os
import discord
from discord.ext import commands
from TypeRacerStats.config import *
from TypeRacerStats.Core.Common.prefixes import *
from TypeRacerStats.Core.Common.aliases import *

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(os.path.dirname(__file__) + '/../src/commands.json', 'r') as jsonfile:
            self.commands = json.load(jsonfile)
        
        self.all_commands = []
        for type_ in self.commands.values():
            self.all_commands += type_
    
    def create_embeds(self, bot, message):
        COMMAND_PREFIX = get_prefix(bot, message)

        self.normalized_commands, self.command_embeds = {}, {}
        for command in self.all_commands:
            name = command['name']
            for alias in command['aliases']:
                self.normalized_commands.update({alias: name})
            self.normalized_commands.update({name: name})
            self.command_embeds.update({name: embed_constructor(command, COMMAND_PREFIX)})

        self.main_embed = discord.Embed(title = 'Help Page',
                                        color = discord.Color(HELP_BLACK),
                                        description = (f"**Run `{COMMAND_PREFIX}help [command]` to learn more**\n"
                                                        "`[ ]` represent required paramaters\n"
                                                        "`< >` represent optional parameters"))
        self.main_embed.set_thumbnail(url = HELP_IMG)
        self.main_embed.add_field(name = 'Info Commands',
                                  value = value_formatter(self.commands['info'], COMMAND_PREFIX),
                                  inline = False)
        self.main_embed.add_field(name = 'Configuration Commands',
                                  value = value_formatter(self.commands['configuration'], COMMAND_PREFIX),
                                  inline = False)
        self.main_embed.add_field(name = 'Basic Commands',
                                  value = value_formatter(self.commands['basic'], COMMAND_PREFIX),
                                  inline = False)
        self.main_embed.add_field(name = f"Advanced Commands (all require `{COMMAND_PREFIX}getdata`)",
                                  value = value_formatter(self.commands['advanced'], COMMAND_PREFIX),
                                  inline = False)
        self.main_embed.add_field(name = 'Other Commands',
                                  value = value_formatter(self.commands['other'], COMMAND_PREFIX),
                                  inline = False)
        self.main_embed.set_footer(text = f"Run {COMMAND_PREFIX}help [command] to learn more")
    
    def create_info_embed(self, bot, message):
        COMMAND_PREFIX = get_prefix(bot, message)

        with open(os.path.dirname(__file__) + '/../info.txt', 'r') as txtfile:
            self.info_ = txtfile.read().split('\n\n')
            self.info_ = self.info_[0].split('\n') + self.info_[1:]
            self.info_ = [i.replace('\\n', '\n').replace('{PFX}', COMMAND_PREFIX) for i in self.info_]
        
        self.info_embed = discord.Embed(title = self.info_[0],
                                        color = discord.Color(int(self.info_[1])),
                                        description = self.info_[2])
        self.info_embed.set_thumbnail(url = self.info_[3])
        for i in range(4, len(self.info_) - 1):
            paragraph = self.info_[i].split(':::')
            print(paragraph)
            self.info_embed.add_field(name = paragraph[0], value = paragraph[1], inline = False)
        self.info_embed.set_footer(text = self.info_[-1])

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

def value_formatter(command_list, COMMAND_PREFIX):
    value = ''
    for command in command_list:
        value += f"`{COMMAND_PREFIX}{command['name']} {command['usage']['general']}`\n"
    return value[:-1]

def embed_constructor(command, COMMAND_PREFIX):
    call = f"{COMMAND_PREFIX}{command['name']}"
    if command['name'] == 'verify' or command['name'] == 'premium':
        embed = discord.Embed(title = f"Help for `{COMMAND_PREFIX}premium` and `{COMMAND_PREFIX}verify`",
                              color = discord.Color(HELP_BLACK),
                              description = (f"`{COMMAND_PREFIX}premium [user]` and"
                                             f" `{COMMAND_PREFIX}verify [verification_code]` - "
                                             f"{command['description']}"))
        embed.add_field(name = "Steps", value = (f"1. Run `{COMMAND_PREFIX}premium [user]`\n"
                                                  "2. Check TypeRacer inbox for a message\n"
                                                 f"3. Run `{COMMAND_PREFIX}verify [verification code]`"))
        return embed

    embed = discord.Embed(
        title = f"Help for `{call}` {SPEED_INDICATORS[command['speed']]}",
        color = discord.Colour(HELP_BLACK),
        description = f"`{call} {command['usage']['general']}` - {command['description']}"
    )

    embed.set_thumbnail(url = HELP_IMG)

    if command['usage']['general']:
        embed.add_field(
            name = 'Usage',
            value = f"`{call} {command['usage']['example']}`",
            inline = False
        )
    
    if command['usage']['alt_example']:
        value = ''
        for example in command['usage']['alt_example']:
            value += f"{example['notes']}: `{call} {example['usage']}`\n"
        embed.add_field(
            name = 'Alternative Usage',
            value = value[:-1],
            inline = False
        )
    
    if command['aliases']:
        value = ''
        for alias in command['aliases']:
            value += f"`{alias}`, "
        embed.add_field(
            name = 'Aliases',
            value = value[:-2],
            inline = False
        )

    if command['linked']:
        embed.set_footer(text = 'Command can be used without user parameter if Discord account is linked')

    return embed

def setup(bot):
    bot.add_cog(Help(bot))
