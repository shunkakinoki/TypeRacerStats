import asyncio
import csv
import os
from PIL import Image, ImageDraw, ImageFont
import random
import sqlite3
import sys
import time
import discord
from discord.ext import commands, tasks
sys.path.insert(0, '')
from TypeRacerStats.config import CHRISTMAS_KEY, NUMBERS, BOT_OWNER_IDS
from TypeRacerStats.file_paths import DATABASE_PATH
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.Core.Common.requests import fetch

class Christmas_2020(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_request.start()
        self.font = ImageFont.truetype('Arial.ttf', size = 48)
        self.words = ['filler']

    def cog_load(self):
        self.send_request.start()

    def cog_unload(self):
        self.send_request.cancel()

    @tasks.loop(seconds = 120) #seconds = 180
    async def send_request(self):
        random_duration = random.randint(0, 30) #random.randint(0, 120)
        await asyncio.sleep(random_duration)

        embed = discord.Embed(title = '<:santavalikor:793468488714944562> Santa Says: I need some toys!',
                              color = discord.Color(0x9700),
                              description = '**Quickly, type the toys for Santa!**')

        embed.set_footer(text = 'Santa will only accept toys crafted with 100% accuracy!')

        file_name = 'christmas_2020.png'
        img = Image.new('RGB', (1000, 1000), color = (47, 49, 54))
        draw = ImageDraw.Draw(img)

        gifts = [random.choice(self.words) for _ in range(random.randint(5, 20))] #random.randint(3, 10)
        text = ' '.join(gifts)

        cur_text, cur_width, total_height = '', 0, 0
        for word in text.split(' '):
            word_ = f"{word} "
            width, height = self.font.getsize(word_)
            cur_width += width
            if cur_width > 980:
                draw.text((10, total_height), cur_text, font = self.font, fill = (215, 216, 217))
                cur_text = word_
                cur_width = width
                total_height += height
            else:
                cur_text += word_
        draw.text((10, total_height), cur_text, font = self.font, fill = (215, 216, 217))
        total_height += height

        img = img.crop((0, 0, 1000, total_height + height * 0.5))
        img.save(file_name, 'png')

        file_ = discord.File(file_name, filename = file_name)

        embed.set_image(url = f"attachment://{file_name}")

        christmas_channel = self.bot.get_channel(793478667056578621) #christmas-bot-usage channel ID

        request_message = await christmas_channel.send(file = file_, embed = embed)
        start = time.time()
        os.remove(file_name)

        try:
            msg = await self.bot.wait_for('message', check = check(text), timeout = len(text))
            user_id = msg.author.id
            time_taken = time.time() - start
            time_remaining = len(text) - time_taken
            points = round(time_remaining * len(text) / 100) + 1

            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            try:
                c.execute(f"INSERT INTO {CHRISTMAS_KEY} (id, name, cookies, gifts) VALUES (?, ?, ?, ?)",
                            (user_id,
                            f"{msg.author.name}#{msg.author.discriminator}",
                            points,
                            len(gifts)))
                conn.commit()
                conn.close()
            except sqlite3.OperationalError:
                c.execute(f"CREATE TABLE {CHRISTMAS_KEY} (id integer, name, cookies, gifts)")
                conn.close()

            embed = discord.Embed(title = f"<:santavalikor:793468488714944562> Thank you @{msg.author.name}!",
                                  color = discord.Color(0x9700),
                                  description = (f"You made **{len(gifts)}** gifts in **{round(time_taken, 3)}**\n"
                                                 f"seconds for **{f'{points:,}'}** :cookie:!"))
            embed.set_image(url = 'https://cdn.discordapp.com/emojis/793468488869740544.png?v=1')
            await request_message.edit(content = f"<@{user_id}>",
                                       embed = embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(title = 'Time ran out :(', color = discord.Color(0xFF0000))
            embed.set_image(url = 'https://cdn.discordapp.com/emojis/793509718185607199.png?v=1')
            await request_message.edit(embed = embed)

    @commands.check(lambda ctx: check_banned_status(ctx))
    @commands.command(aliases = ['clb', 'christmaslb'])
    async def christmasleaderboard(self, ctx):
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        user_data = c.execute(f"""SELECT name, SUM(cookies), SUM(gifts)
                                  FROM {CHRISTMAS_KEY}
                                  GROUP BY id
                                  ORDER BY SUM(cookies) DESC""").fetchall()
        conn.close()

        description = ''
        for i, user in enumerate(user_data[:10]):
            description += f"{NUMBERS[i]} {user[0]} - {f'{user[1]:,}'} :cookie:\n"
        description = description[:-1]

        embed = discord.Embed(title = ':star2: Santa\'s Best Elves :star2:',
                              color = discord.Color(0xFF0000),
                              description = description)

        adjectives = ['made', 'crafted', 'fabricated', 'manifested']
        embed.set_footer(text = (f"{f'{len(user_data):,}'} elves {random.choice(adjectives)} "
                                 f"{f'{sum([i[2] for i in user_data]):,}'} gifts and\n"
                                 f"accumulated {f'{sum([i[1] for i in user_data]):,}'} cookies so far!"))

        if ctx.message.author.id in BOT_OWNER_IDS:
            christmas_lb_data = [['name', 'cookies', 'gifts']]
            for user in user_data:
                christmas_lb_data.append(list(user))

            with open('christmas_2020.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(christmas_lb_data)

            file_ = discord.File('christmas_2020.csv', 'christmas_2020.csv')

            await ctx.send(file = file_, embed = embed)
            os.remove('christmas_2020.csv')
            return

        await ctx.send(embed = embed)

    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and check_banned_status(ctx))
    @commands.command(aliases = ['uw'])
    async def updatewords(self, ctx):
        words = ((await fetch(['https://pastebin.com/raw/ynB6UtBP'], 'text'))[0].split('\n'))
        words_filtered = [word.strip() for word in words if word]
        self.words = words_filtered

        await ctx.send(embed = discord.Embed(title = 'Christmas 2020 Word List Updated',
                                             color = discord.Color(0)))

def check(text):
    def inner_check(message):
        if message.content == text:
            return True
        else:
            return False
    return inner_check

def setup(bot):
    bot.add_cog(Christmas_2020(bot))
