import discord
from discord.ext import commands

class TypeRacerOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 746460695670816798: #typeracer-stats in TypeRacer main server
            return
        if 't!tg train' in message.content:
            if message.author.id == 476016555981930526: #pasta's Discord ID
                await message.channel.send(content = f"<@{message.author.id}>, this is NOT bot usage.")
            else:
                embed = discord.Embed(title = 'Training Success!',
                                      color = discord.Color(0x4B9F6C),
                                      description = 'Your pet ran around you in circles. It is now resting on your lap!')
                embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/448997775309537280/791689215531679764/pet.png')
                embed.add_field(name = 'Updated Attributes',
                                value = ('<:pet_xp:791713169763991553> Exp: **10 / 10200** (`+10`)\n'
                                         '<:pet_fatigue:791713209371459584> Fatigue: **12 / 504** (`+3`)'))
                embed.set_footer(text = 'Copied from Tatsu#8792 to meme pasta | Wrapped Tatsugotchis are tradable, but not unwrapped ones.')
                await message.channel.send(content = ('>  **Interacting with Pet • [ **'
                                                      f"{message.author.name}#{message.author.discriminator}"
                                                      '** ] • **`1`<a:mail_new_small:791710454946857001>'
                                                      '`2`<a:dice:791710772984021013>'),
                                           embed = embed)

        return

def setup(bot):
    bot.add_cog(TypeRacerOnly(bot))
