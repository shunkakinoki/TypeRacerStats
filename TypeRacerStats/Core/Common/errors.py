import discord
from TypeRacerStats.Core.Common.prefixes import get_prefix

class Error:
    def __init__(self, bot):
        self.command_prefix = get_prefix(bot, bot.id)

    def parameters(self, message):
        embed = discord.Embed(color = discord.Color(0xff9700))
        embed.add_field(name = "Error: Missing/Too Many Parameters", value = message)
        return embed

    def error_two(self, message):
        embed = discord.Embed(color = discord.Color(0xe0001a))
        embed.add_field(name = "Error: Incorrect Parameter Type/Format", value = message)
        return embed

    def error_three(self):
        embed = discord.Embed(color = discord.Color(0xf8e41c))
        embed.add_field(name = "Error: User Information Not Downloaded",
                        value = "Must run `!getdata [user]` on the user(s)")
        return embed

    def error_four(self, *args):
        embed = discord.Embed(color = discord.Color(0x838383))
        if len(args) == 0:
            embed.add_field(name = "Error: Information Not Found", value = "User doesn't exist")
            return embed
        else:
            embed.add_field(name = "Error: Information Not Found", value = args[0])
            return embed

    def error_five(self, message):
        embed = discord.Embed(color = discord.Color(0x7f0dcc))
        embed.add_field(name = "Error: Lacking Permissions", value = message)
        return embed
