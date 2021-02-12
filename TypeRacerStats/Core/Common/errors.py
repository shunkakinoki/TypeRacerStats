import discord
from TypeRacerStats.Core.Common.prefixes import get_prefix


class Error:
    def __init__(self, bot, message):
        self.command_prefix = get_prefix(bot, message)

    def parameters(self, message):
        embed = discord.Embed(color=discord.Color(0xff9700))
        embed.add_field(name='Error: Missing/Too Many Parameters',
                        value=f"Must provide `{self.command_prefix}{message}`")
        return embed

    def incorrect_format(self, message):
        embed = discord.Embed(color=discord.Color(0xe0001a))
        embed.add_field(
            name='Error: Incorrect Parameter Type/Format', value=message)
        return embed

    def not_downloaded(self):
        embed = discord.Embed(color=discord.Color(0xf8e41c))
        embed.add_field(name='Error: User Information Not Downloaded',
                        value=f"Must run `{self.command_prefix}getdata [user]` on the user(s)")
        return embed

    def missing_information(self, *args):
        embed = discord.Embed(color=discord.Color(0x838383))
        if len(args) == 0:
            embed.add_field(name='Error: Information Not Found',
                            value="User doesn't exist")
            return embed
        else:
            embed.add_field(name='Error: Information Not Found', value=args[0])
            return embed

    def lacking_permissions(self, message):
        embed = discord.Embed(color=discord.Color(0x7f0dcc))
        embed.add_field(name='Error: Lacking Permissions', value=message)
        return embed

    def cooldown(self, message):
        embed = discord.Embed(color=discord.Color(0x7f0dcc))
        embed.add_field(name='Error: Command Cooldown', value=message)
        return embed
