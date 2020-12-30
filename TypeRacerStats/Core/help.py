import csv
import json
import os
import time
import discord
from discord.ext import commands
from TypeRacerStats.config import BOT_OWNER_IDS, HELP_BLACK, HELP_IMG, SPEED_INDICATORS
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.Core.Common.aliases import get_aliases
from TypeRacerStats.Core.Common.prefixes import get_prefix

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.normalized_commands = {}
        self.command_embeds = {}
        self.main_embed = None
        self.info_embed = None
        self.invite_embed = None
        self.donate_embed = None
        self.perks_embed = None
        with open(os.path.dirname(__file__) + '/../src/commands.json', 'r') as jsonfile:
            self.bot_commands = json.load(jsonfile)

    def create_embeds(self, bot, message):
        command_prefix = get_prefix(bot, message)

        for command in [command for category in self.bot_commands.values() for command in category]:
            name = command['name']
            for alias in command['aliases']:
                self.normalized_commands.update({alias: name})
            self.normalized_commands.update({name: name})
            self.command_embeds.update({name: embed_constructor(command, command_prefix)})

        self.main_embed = discord.Embed(title = 'Help Page',
                                        color = discord.Color(HELP_BLACK),
                                        description = ('[`Invite`](https://www.google.com/) - '
                                                       '[`top.gg`](https://top.gg/bot/742267194443956334) - '
                                                       '[`GitHub`](https://github.com/e6f4e37l/TypeRacerStats) - '
                                                       '[`PayPal`](https://www.paypal.me/e3e2)\n\n'
                                                       f"**Run `{command_prefix}help [command]` to learn more**\n"
                                                       "`[ ]` represent required paramaters\n"
                                                       "`< >` represent optional parameters"))
        self.main_embed.set_thumbnail(url = HELP_IMG)
        self.main_embed.add_field(name = 'Info Commands',
                                  value = value_formatter(self.bot_commands['info'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Configuration Commands',
                                  value = value_formatter(self.bot_commands['configuration'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Basic Commands',
                                  value = value_formatter(self.bot_commands['basic'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = f"Advanced Commands (all require `{command_prefix}getdata`)",
                                  value = value_formatter(self.bot_commands['advanced'], command_prefix),
                                  inline = False)
        self.main_embed.add_field(name = 'Other Commands',
                                  value = value_formatter(self.bot_commands['other'], command_prefix),
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
            self.info_embed.add_field(name = paragraph[0], value = paragraph[1], inline = False)
        self.info_embed.set_footer(text = info[-1])

    def create_invite_embed(self):
        guilds = self.bot.guilds
        server_count = len(guilds)
        people_count = sum([i.member_count for i in guilds])

        self.invite_embed = discord.Embed(title = "TypeRacerStats Invite Link",
                                          color = HELP_BLACK,
                                          description = '[**Invite Link**](https://discord.com/oauth2/authorize?client_id=742267194443956334&permissions=378944&scope=bot)')
        self.invite_embed.add_field(name = 'Stats',
                                    value = f"Serving {f'{people_count:,}'} people in {f'{server_count:,}'} servers")

    def create_donate_embed(self):
        description = '[**Star on GitHub ⭐**](https://github.com/e6f4e37l/TypeRacerStats)\n'
        description += '[**Vote for TypeRacerStats on `top.gg` 🗳️**](https://top.gg/bot/742267194443956334)\n'
        description += '[**Support on PayPal ❤️**](https://www.paypal.me/e3e2)'

        self.donate_embed = discord.Embed(title = "TypeRacerStats Donation/Support",
                                          color = HELP_BLACK,
                                          description = description)
        self.donate_embed.add_field(name = 'Perks (USD)',
                                    value = ('**Tier 1: $0.01 - $5.99**\n'
                                             'Name listed on `info` command and access to `echo` command\n\n'
                                             '**Tier 2: $6.00 - $11.99**\n'
                                             'Set custom embed color with `setcolor`\n\n'
                                             '**Tier 3: $12.00 - $17.99**\n'
                                             'Custom command added to the bot and set custom colors for graphs with `setgraphcolor`\n\n'
                                             '**Tier 4: $18.00+**\n'
                                             'Access to commands via bot DM'))
        self.donate_embed.set_footer(text = 'One month of hosting costs 6 USD')

    def create_perks_embed(self, bot, message):
        command_prefix = get_prefix(bot, message)

        value = value_formatter(self.bot_commands['supporter'], command_prefix)

        self.perks_embed = discord.Embed(title = "Supporter Commands",
                                          color = HELP_BLACK,
                                          description = 'These commands only work for those that have supported the project. Refer to the `support` command for more information.')
        self.perks_embed.set_thumbnail(url = HELP_IMG)
        self.perks_embed.add_field(name = 'Commands',
                                    value = value)

    @commands.check(lambda ctx: check_banned_status(ctx))
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

    @commands.command(aliases = get_aliases('info'))
    async def info(self, ctx, *args):
        self.create_info_embed(ctx, ctx.message)

        if len(args) != 0: return
        await ctx.send(embed = self.info_embed)

    @commands.check(lambda ctx: check_banned_status(ctx))
    @commands.command(aliases = get_aliases('invite'))
    async def invite(self, ctx, *args):
        self.create_invite_embed()

        if len(args) != 0: return
        await ctx.send(embed = self.invite_embed)

    @commands.command(aliases = get_aliases('support'))
    async def support(self, ctx, *args):
        self.create_donate_embed()

        if len(args) != 0: return
        await ctx.send(embed = self.donate_embed)

    @commands.check(lambda ctx: check_banned_status(ctx))
    @commands.command(aliases = get_aliases('perks'))
    async def perks(self, ctx, *args):
        self.create_perks_embed(ctx, ctx.message)

        if len(args) != 0: return
        await ctx.send(embed = self.perks_embed)

    @commands.command(aliases = ['servers'])
    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and not ctx.guild and check_banned_status(ctx))
    async def listservers(self, ctx):
        guilds = sorted(self.bot.guilds, key = lambda x: x.member_count, reverse = True)
        guilds_data = [['Name', "Member Count", 'Guild ID']]
        people_count, server_count = 0, 0
        for guild in guilds:
            guilds_data.append([guild.name, guild.member_count, guild.id])
            people_count += guild.member_count
            server_count += 1

        with open('servers.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(guilds_data)

        embed = discord.Embed(title = 'List of Servers TypeRacerStats is in',
                              color = discord.Color(0),
                              description = f"Serving {f'{people_count:,}'} people in {f'{server_count:,}'} servers")
        for i, guild in enumerate(guilds[0:20]):
            embed.add_field(name = guild.name,
                            value = (f"{i + 1}. {f'{guild.member_count:,}'} members "
                                     f"({round(100 * guild.member_count / people_count, 2)}%)"),
                            inline = False)

        await ctx.send(embed = embed,
                       file = discord.File('servers.csv', f"server_list_{time.time()}.csv"))
        os.remove('servers.csv')
        return

def value_formatter(command_list, command_prefix):
    value = ''
    for command in command_list:
        value += f"`{command['name']}`, "
    return value[:-2]

def embed_constructor(command, command_prefix):
    call = f"{command_prefix}{command['name']}"

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
