import asyncio
import datetime
import json
import re
import sqlite3
import sys
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
sys.path.insert(0, '')
from TypeRacerStats.config import BOT_OWNER_IDS, BLANK_FLAG, HELP_IMG, TR_INFO
from TypeRacerStats.file_paths import DATABASE_PATH, TYPERACER_RECORDS_JSON, COUNTRY_CODES
from TypeRacerStats.Core.Common.accounts import check_banned_status
from TypeRacerStats.Core.Common.formatting import escape_sequence, seconds_to_text
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.Core.Common.errors import Error
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.scrapers import rs_typinglog_scraper
from TypeRacerStats.Core.Common.texts import load_texts_json
from TypeRacerStats.Core.Common.urls import Urls


class TypeRacerOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.medals = [':first_place:', ':second_place:', ':third_place:']
        self.records_information = dict()
        self.accounts = dict()
        self.countries = dict()
        self.last_updated = ''
        self.races_alltime = dict()
        self.points_alltime = dict()
        self.awards_alltime = dict()
        self.country_tally = dict()
        self.user_tally = dict()

        self.update_init_variables()
        self.update_records.start()

    def cog_load(self):
        self.update_records.start()

    def cog_unload(self):
        self.update_records.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return

        if message.guild.id != 175964903033667585:  #TypeRacer Discord guild ID
            return

        message_content_lower = message.content.lower()

        if 't!tg train' in message_content_lower:
            if message.channel.id != 746460695670816798:  #typeracer-stats in TypeRacer main server
                return
            if message.author.id == 476016555981930526:  #pasta's Discord ID
                await message.channel.send(
                    content=f"<@{message.author.id}>, this is NOT bot usage.")
                return
            else:
                embed = discord.Embed(
                    title='Training Success!',
                    color=discord.Color(0x4B9F6C),
                    description=
                    'Your pet ran around you in circles. It is now resting on your lap!'
                )
                embed.set_thumbnail(
                    url=
                    'https://cdn.discordapp.com/attachments/448997775309537280/791689215531679764/pet.png'
                )
                embed.add_field(
                    name='Updated Attributes',
                    value=
                    ('<:pet_xp:791713169763991553> Exp: **10 / 10200** (`+10`)\n'
                     '<:pet_fatigue:791713209371459584> Fatigue: **12 / 504** (`+3`)'
                     ))
                embed.set_footer(
                    text=
                    'Copied from Tatsu#8792 to meme pasta | Wrapped Tatsugotchis are tradable, but not unwrapped ones.'
                )
                await message.channel.send(content=(
                    '>  **Interacting with Pet • [ **'
                    f"{message.author.name}#{message.author.discriminator}"
                    '** ] • **`1`<a:mail_new_small:791710454946857001>'
                    '`2`<a:dice:791710772984021013>'),
                                           embed=embed)
                return

        words_set = set(re.findall('[a-z0-9]+', message_content_lower))

        if not ({'how', 'dark', 'mode'} - words_set):
            embed = discord.Embed(
                title='FAQ: How do I get dark mode on TypeRacer?',
                color=discord.Color(0),
                description=
                ('_By: Keegan_\n\n'
                 'With the Chrome extension "[Stylus]'
                 '(https://chrome.google.com/webstore/detail/stylus/clngdbkpkpeebahjckkjfobafhncgmne?hl=en)," '
                 'any theme can be applied to any website. '
                 'If you know the basics of `css`, you can create your own theme. '
                 'If you do not, you can browse [themes created by the community]'
                 '(https://userstyles.org/styles/browse/typeracer). '
                 'The most popular ones for TypeRacer are '
                 '[TypeRacer modern dark]'
                 '(https://userstyles.org/styles/140579/typeracer-modern-dark) '
                 'and [TypeRacer modern dark by Hysteria]'
                 '(https://userstyles.org/styles/164591/typeracer-modern-dark-by-hysteria).'
                 ))

            await message.channel.send(content=f"<@{message.author.id}>",
                                       embed=embed)
            return

        if not ({'show', 'unlagged'} -
                words_set) or not ({'show', 'adjusted'} - words_set):
            embed = discord.Embed(
                title='FAQ: How do I get unlagged/adjusted WPM to show?',
                color=discord.Color(0),
                description=
                ('_By: Poem_\n\n'
                 'To install, ```'
                 'Get Tampermonkey from the Chrome Web store. '
                 'Click on one of the GitHub links below to access the code, '
                 'then `ctrl + a` and `ctrl + c` copy everything. '
                 'Click on the Tampermonkey icon in Chrome at the top right corner, '
                 'then "Dashboard," then "⊞" to create a new script. '
                 'Finally, replace the contents of that new script with the code, '
                 'and press file > save. You\'re set!```'))
            embed.add_field(
                name=
                'Adjusted Speed (including on Race End pages), Text Difficulty',
                value=
                ('[__`Script`__]'
                 '(https://github.com/PoemOnTyperacer/tampermonkey/raw/master/adjusted_speed.user.js) - '
                 'Thanks to **ph0t0shop#6788** for help implementing various changes such as cross-browser support!\n'
                 '[Information on the "difficulty" in this script.]'
                 '(http://bit.ly/typeracertextdifficulty)\n\n'
                 '_Warning 1: this script **replaces** the previous \'adjusted speed calculator\' script—'
                 'Make sure to delete the old version._'),
                inline=False)
            embed.add_field(
                name='Unlagged Scores and Top 10s in an Off-Window',
                value=
                ('[__`Script`__]'
                 '(https://github.com/PoemOnTyperacer/tampermonkey/raw/master/unlagged_scores.user.js)'
                 ),
                inline=False)
            embed.add_field(
                name='Exact Last 10 Average',
                value=
                ('[__`Script`__]'
                 '(https://raw.githubusercontent.com/PoemOnTyperacer/tampermonkey/master/better-info-box.js)'
                 ),
                inline=False)
            embed.add_field(
                name='Awards Organizer',
                value=
                ('[__`Script`__]'
                 '(https://raw.githubusercontent.com/PoemOnTyperacer/tampermonkey/master/d_tr-a.js)'
                 ),
                inline=False)

            await message.channel.send(content=f"<@{message.author.id}>",
                                       embed=embed)
            return

        if not ({'what', 'are', 'points'} - words_set):
            embed = discord.Embed(
                title='FAQ: What are points?',
                color=discord.Color(0),
                description=
                ('Points are an arbitrary measure of a user\'s speed and amount played. '
                 'You receive these simply by playing the game: '
                 'After each race, you will receive `(words per second) • (number of words)` points. '
                 'There is no functionality to points other than to serve as a statistic/measure.'
                 ))

            await message.channel.send(content=f"<@{message.author.id}>",
                                       embed=embed)
            return

        if not ({'how', 'type', 'fast'} -
                words_set) or not ({'how', 'type', 'faster'} - words_set):
            embed = discord.Embed(
                title='FAQ: How do I type faster?',
                color=discord.Color(0),
                description=('_By: Izzy_\n\n'
                             'Type the words faster in the right order.'))

            await message.channel.send(content=f"<@{message.author.id}>",
                                       embed=embed)
            return

        return

    #e6f4e37l's Discord ID / TypeRacer Discord guild ID
    @commands.check(lambda ctx: ctx.message.author.id == 697048255254495312 and
                    ctx.message.guild.id == 175964903033667585)
    @commands.command()
    async def eugeneroles(self, ctx):
        role_ids = [
            450016581292916761,  #Premium
            492709794877145109,  #Partner
            676030226874236948,  #Sheet Master
            658349038403452939  #Updates
        ]

        get_role = lambda id_: discord.utils.get(ctx.message.guild.roles,
                                                 id=id_)
        roles = map(get_role, role_ids)
        for role in roles:
            try:
                await ctx.message.author.add_roles(role)
            except:
                pass
        return

    @commands.check(lambda ctx: ctx.message.author.id in BOT_OWNER_IDS and
                    check_banned_status(ctx))
    @commands.cooldown(5, 7200, commands.BucketType.default)
    @commands.command(aliases=['keegant', 'tr_records'])
    async def keegan(self, ctx, *args):
        user_id = ctx.message.author.id

        actions = {'setup': self.records_setup, 'update': self.records_update}

        if len(args) > 1:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(
                    ctx,
                    ctx.message).parameters(f"{ctx.invoked_with} <action>"))
            return

        if len(args) == 0:
            file_ = discord.File(
                TYPERACER_RECORDS_JSON,
                filename=f"typeracer_records_{self.last_updated.lower()}.json")
            await ctx.send(file=file_)
            return

        action = args[0].lower()
        try:
            action = actions[action]
        except KeyError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    f"Must provide a valid action: `{'`, `'.join(actions.keys())}`"
                ))
            return

        await action(ctx)
        return

    async def records_setup(self, ctx):
        self.update_init_variables()
        embeds = await self.construct_embeds()
        for name, embed in embeds.items():
            message = await ctx.send(embed=embed)
            if name == 'faq':
                self.records_information['information'].update(
                    {'message_id': message.id})
            else:
                self.records_information['all_records'][name].update(
                    {'message_id': message.id})
            self.records_information.update({'channel_id': message.channel.id})
            await asyncio.sleep(1)

        with open(TYPERACER_RECORDS_JSON, 'w') as jsonfile:
            json.dump(self.records_information, jsonfile, indent=4)

    async def records_update(self, ctx):
        user_id = ctx.message.author.id

        try:
            updated_file_raw = ctx.message.attachments[0]
        except IndexError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    'Please upload a file and comment the command call'))
            return

        try:
            updated_file = json.loads(await updated_file_raw.read())
        except json.JSONDecodeError:
            await ctx.send(
                content=f"<@{user_id}>",
                embed=Error(ctx, ctx.message).incorrect_format(
                    'The uploaded file is not a properly formatted JSON file'))
            return

        with open(TYPERACER_RECORDS_JSON, 'w') as jsonfile:
            json.dump(updated_file, jsonfile, indent=4)

        try:
            await self.edit_record_messages()
        except NotImplementedError:
            await ctx.send(
                content=f"<@{ctx.message.author.id}>",
                embed=Error(ctx, ctx.message).missing_information(
                    f"Must set-up the records with `{ctx.invoked_with} setup` first"
                ))
            return

        await ctx.send(embed=discord.Embed(title='Records Updated',
                                           color=discord.Color(0)))
        return

    @tasks.loop(hours=24)
    async def update_records(self):
        await self.edit_record_messages()

    async def edit_record_messages(self):
        try:
            self.update_init_variables()

            channel = await self.bot.fetch_channel(
                self.records_information['channel_id'])
            embeds = await self.construct_embeds()
            for name, embed in embeds.items():
                if name == 'faq':
                    message_id = self.records_information['information'][
                        'message_id']
                else:
                    message_id = self.records_information['all_records'][name][
                        'message_id']
                message = await channel.fetch_message(message_id)
                await asyncio.sleep(1)
                await message.edit(embed=embed)
                await asyncio.sleep(1)
        except:
            raise NotImplementedError
        return

    def update_init_variables(self):
        with open(TYPERACER_RECORDS_JSON, 'r') as jsonfile:
            self.records_information = json.load(jsonfile)

        for main, sub_accounts in self.records_information['accounts'].items():
            for sub_account in sub_accounts:
                self.accounts.update({sub_account: main})
            self.accounts.update({main: main})

        self.countries = self.records_information['countries']
        self.last_updated = datetime.datetime.utcnow().strftime(
            '%B %-d, %Y, %X %p')
        self.races_alltime = self.records_information['all_records']['races'][
            'all_time']
        self.points_alltime = self.records_information['all_records'][
            'points']['all_time']
        self.awards_alltime = self.records_information['all_records'][
            'awards']['all_time']

    async def construct_embeds(self):
        self.last_updated = datetime.datetime.utcnow().strftime(
            '%B %-d, %Y, %X %p')
        self.country_tally = dict()
        self.user_tally = dict()

        faq_thumbnail = HELP_IMG
        speed_thumbnail, speed_color = 'https://i.imgur.com/bXAjl4C.png', 0x001359
        three_hundred_thumbnail, three_hundred_color = 'https://i.imgur.com/i8kXn3K.png', 0x1B038C
        races_thumbnail, races_color = 'https://i.imgur.com/DspJLUH.png', 0x14328C
        points_thumbnail, points_color = 'https://i.imgur.com/Xm0VNQV.png', 0x0B4A9E
        speedruns_thumbnail, speedruns_color = 'https://i.imgur.com/lPdQvvQ.png', 0x0E61D1
        awards_thumbnail, awards_color = 'https://i.imgur.com/W9NEYb2.png', 0x0790E8
        records_held_thumbnail, records_held_color = 'https://i.imgur.com/3gJNZRO.png', 0x00BFFF
        last_updated_color = 0x00EEFF

        faq_information = self.records_information['information']
        faq_embed = discord.Embed(**faq_information)
        for field in faq_information['fields']:
            faq_embed.add_field(**field)
        faq_embed.set_thumbnail(url=faq_thumbnail)
        faq_embed.set_footer(**faq_information['footer'])

        all_records_information = self.records_information['all_records']

        speed_information = all_records_information['speed']['records']
        speed_embed = discord.Embed(title='Speed Records',
                                    color=discord.Color(speed_color))
        for speed_record in speed_information:
            speed_embed.add_field(
                **self.record_field_constructor(speed_record, ' WPM'))
        speed_embed.set_thumbnail(url=speed_thumbnail)

        three_hundred_information = all_records_information['300_wpm_club'][
            'records']
        description, members_list = '', []

        for member, url in three_hundred_information.items():
            result = (await fetch([url], 'text', rs_typinglog_scraper))[0]
            wpm = round(
                12000 * (result['length'] - 1) /
                (result['duration'] - result['start']), 3)
            date = datetime.datetime.fromtimestamp(
                result['timestamp']).strftime('%-m/%-d/%y')
            members_list.append([member, wpm, url, date])

        members_list = sorted(members_list, key=lambda x: x[1], reverse=True)

        for i, member in enumerate(members_list):
            if i < 3: rank = self.medals[i]
            else: rank = f"{i + 1}."
            if member[1] >= 400: wpm = f"**{member[1]}**"
            else: wpm = member[1]
            description += f"{rank} {self.get_flag(member[0])} {member[0]} - "
            description += f"[{wpm} WPM]({member[2]}) - {member[3]}\n"

        description = description[:-1]
        three_hundred_embed = discord.Embed(
            title='300 WPM Club',
            color=discord.Color(three_hundred_color),
            description=description)
        three_hundred_embed.set_thumbnail(url=three_hundred_thumbnail)
        three_hundred_embed.set_footer(
            text='All speeds measured according to adjusted metric')

        all_time_leaders = [
            user for category in self.races_alltime.values()
            for user in category
        ]
        all_time_leaders += [
            user for category in self.points_alltime.values()
            for user in category
        ]
        all_time_leaders += [
            user for category in self.awards_alltime.values()
            for user in category
        ]
        all_time_leaders = set(all_time_leaders)
        all_time_data = dict()

        url_constructor = Urls()
        right_now = datetime.datetime.utcnow().timestamp()
        texts_data = load_texts_json()
        with open(COUNTRY_CODES, 'r') as jsonfile:
            country_codes = json.load(jsonfile)
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        for user in all_time_leaders:
            medals = {1: 0, 2: 0, 3: 0}
            try:
                response = (await fetch([url_constructor.user(user, 'play')],
                                        'text'))[0]
                soup = BeautifulSoup(response, 'html.parser')

                rows = soup.select(
                    "table[class='personalInfoTable']")[0].select('tr')

                medal_html_objects = None
                for row in rows:
                    cells = row.select('td')
                    if len(cells) < 2: continue
                    if cells[0].text.strip() == 'Awards':
                        medal_html_objects = cells[1].select('a')
                        break

                if medal_html_objects:
                    for medal in medal_html_objects:
                        medals[int(medal.select('img')[0]['title'][0])] += 1

                if escape_sequence(user):
                    raise FileNotFoundError
                urls = [Urls().get_races(user, 'play', 1)]

                user_data = c.execute(
                    f"SELECT * FROM t_{user} ORDER BY t DESC LIMIT 1")
                last_race_timestamp = user_data.fetchone()[1]

                data = await fetch_data(user, 'play',
                                        last_race_timestamp + 0.01, right_now)
                if data:
                    c.executemany(
                        f"INSERT INTO t_{user} VALUES (?, ?, ?, ?, ?)", data)
                conn.commit()
                data = c.execute(f"SELECT * FROM t_{user}")

                races, chars_typed, points, total_points, seconds_played = (
                    0, ) * 5
                for race in data:
                    races += 1
                    race_text_id = str(race[2])
                    text_length = texts_data[race_text_id]['length']
                    chars_typed += text_length
                    points += race[4]
                    total_points += race[4] if race[4] else texts_data[
                        race_text_id]['word count'] * race[3] / 60
                    try:
                        seconds_played += 12 * text_length / race[3]
                    except ZeroDivisionError:
                        seconds_played += 0

                first_race_timestamp = c.execute(
                    f"SELECT * FROM t_{user} ORDER BY t ASC LIMIT 1").fetchone(
                    )[1]
                time_difference = right_now - first_race_timestamp
                points_time_difference = min(right_now - 1_501_113_600,
                                             time_difference)

                all_time_data.update({
                    user: {
                        'races': races,
                        'races_daily_average': 86400 * races / time_difference,
                        'chars_typed': chars_typed,
                        'points': points,
                        'points_daily_average':
                        86400 * points / points_time_difference,
                        'total_points': total_points,
                        'medals': medals,
                        'seconds_played': seconds_played,
                        'seconds_played_daily_average':
                        86400 * seconds_played / time_difference,
                        'time_difference': time_difference,
                        'points_time_difference': points_time_difference
                    }
                })
            except:
                continue

        conn.close()

        def helper_formatter(tally_dict, name_formatter, results_formatter,
                             *args):
            rankings = dict()
            args = args[0]
            for key, value in tally_dict.items():
                try:
                    rankings[value].append(key)
                except KeyError:
                    rankings[value] = [key]

            rankings = [[k, v] for k, v in sorted(
                rankings.items(), key=lambda x: x[0], reverse=True)][0:3]
            value = ''
            for i, ranking in enumerate(rankings):
                if i == 0 and args[0]:
                    for user in ranking[1]:
                        self.tally(user)

                if len(args) == 1:
                    optional = ''
                else:
                    try:
                        optional = args[1][ranking[1][0]]
                    except KeyError:
                        optional = ''

                ranking[1] = [name_formatter(j) for j in ranking[1]]
                value += f"{self.medals[i]} {' / '.join(ranking[1])} - {results_formatter(ranking[0])}{optional}\n"
            return value

        races_information = all_records_information['races']['records']
        races_embed = discord.Embed(title='Race Records',
                                    color=discord.Color(races_color))
        races_embed.set_thumbnail(url=races_thumbnail)

        helper_sorter = lambda param: {
            k: v[param]
            for k, v in all_time_data.items()
        }
        helper_flag = lambda x: f"{self.get_flag(x)} {x}"
        helper_round = lambda x: f'{round(x):,}'

        races_daily_average_dict = dict()
        points_daily_average_dict = dict()
        chars_typed_metadata_dict = dict()
        medal_breakdown_dict = dict()
        for key, value in all_time_data.items():
            days = round(value['time_difference'] / 86400)
            days_ = round(value['points_time_difference'] / 86400)
            medal_breakdown = value['medals']

            races_daily_average_dict.update({
                key:
                f""" ({f"{round(value['races'], 2):,}"} races over {f"{days:,}"} days)"""
            })

            points_daily_average_dict.update({
                key:
                f""" ({f"{round(value['points']):,}"} points over {f"{days_:,}"} days)"""
            })

            chars_typed_metadata_dict.update({
                key:
                f""" ({f"{round(value['chars_typed'] / value['races'], 2):,}"} average chars over {f"{value['races']:,}"} races)"""
            })

            medal_breakdown_dict.update({
                key:
                f""" (:first_place: {f"{medal_breakdown[1]:,}"} :second_place: {f"{medal_breakdown[2]:,}"} :third_place: {f"{medal_breakdown[3]:,}"})"""
            })

        races_embed.add_field(name='All-Time Leaders',
                              value=helper_formatter(helper_sorter('races'),
                                                     helper_flag, helper_round,
                                                     (True, )),
                              inline=False)
        races_embed.add_field(name='Highest Average Daily Races',
                              value=helper_formatter(
                                  helper_sorter('races_daily_average'),
                                  helper_flag, helper_round,
                                  (True, races_daily_average_dict)),
                              inline=False)
        races_embed.add_field(name='Most Characters Typed',
                              value=helper_formatter(
                                  helper_sorter('chars_typed'), helper_flag,
                                  helper_round,
                                  (True, chars_typed_metadata_dict)),
                              inline=False)
        races_embed.add_field(name='Most Time Spent Racing',
                              value=helper_formatter(
                                  helper_sorter('seconds_played'), helper_flag,
                                  seconds_to_text, (True, )),
                              inline=False)
        races_embed.add_field(
            name='Highest Average Daily Time Spent Racing',
            value=helper_formatter(
                helper_sorter('seconds_played_daily_average'), helper_flag,
                seconds_to_text, (True, )),
            inline=False)

        for races_record in races_information:
            races_embed.add_field(
                **self.record_field_constructor(races_record, ''))

        points_information = all_records_information['points']['records']
        points_embed = discord.Embed(title='Point Records',
                                     color=discord.Color(points_color))
        points_embed.set_thumbnail(url=points_thumbnail)

        points_embed.add_field(name='All-Time Leaders',
                               value=helper_formatter(helper_sorter('points'),
                                                      helper_flag,
                                                      helper_round, (True, )),
                               inline=False)
        points_embed.add_field(name='Highest Average Daily Points',
                               value=helper_formatter(
                                   helper_sorter('points_daily_average'),
                                   helper_flag, helper_round,
                                   (True, points_daily_average_dict)),
                               inline=False)
        points_embed.add_field(
            name='All-Time Total Points (Includes Retroactive Points)',
            value=helper_formatter(helper_sorter('total_points'), helper_flag,
                                   helper_round, (True, )),
            inline=False)
        points_embed.set_footer(
            text=
            'Retroactive points represent the total number of points a user would have gained, before points were introduced in 2017'
        )

        for points_record in points_information:
            points_embed.add_field(
                **self.record_field_constructor(points_record, ''))

        speedruns_information = all_records_information['speedruns']['records']
        speedruns_embed = discord.Embed(title='Speedrun Records',
                                        color=discord.Color(speedruns_color))
        speedruns_embed.set_thumbnail(url=speedruns_thumbnail)

        for speedruns_record in speedruns_information:
            speedruns_embed.add_field(
                **self.record_field_constructor(speedruns_record, ''))

        awards_embed = discord.Embed(title='Awards Records',
                                     color=discord.Color(awards_color))
        awards_embed.set_thumbnail(url=awards_thumbnail)

        medal_tally = {
            k: sum(v['medals'].values())
            for k, v in all_time_data.items()
        }

        awards_embed.add_field(
            name='All-Time Leaders',
            value=helper_formatter(medal_tally, helper_flag, helper_round,
                                   (True, medal_breakdown_dict)),
            inline=False)

        records_held_embed = discord.Embed(
            title='Records Held', color=discord.Color(records_held_color))
        records_held_embed.set_thumbnail(url=records_held_thumbnail)

        top_countries_list = [[k, v] for k, v in self.country_tally.items()]
        records_held_embed.add_field(name = 'Top Countries',
                                     value = helper_formatter(self.country_tally,\
                                                              lambda x: f"{x} {country_codes[re.findall(':flag.+:', x)[0][5:-1].strip('_').upper()]}",
                                                              helper_round,
                                                              (False,)),
                                     inline = False)
        records_held_embed.add_field(name='Top Users',
                                     value=helper_formatter(
                                         self.user_tally, helper_flag,
                                         helper_round, (False, )),
                                     inline=False)

        last_updated_embed = discord.Embed(
            color=discord.Color(last_updated_color),
            description=f"Last updated **{self.last_updated} UTC**")

        return {
            'faq': faq_embed,
            'speed': speed_embed,
            '300_wpm_club': three_hundred_embed,
            'races': races_embed,
            'points': points_embed,
            'speedruns': speedruns_embed,
            'awards': awards_embed,
            'records_held': records_held_embed,
            'last_updated': last_updated_embed
        }

    def record_field_constructor(self, record_information, unit):
        user = record_information['user']
        if 'Race' in record_information['title'].split(' '): emote = ':cinema:'
        else: emote = TR_INFO
        try:
            formatted_record = f"{record_information['record']:,}"
        except ValueError:
            formatted_record = record_information['record']
        value = (f"{self.get_flag(user)} {user} - "
                 f"{formatted_record}{unit} - "
                 f"{record_information['date']} "
                 f"[{emote}]({record_information['url']})")

        self.tally(user)

        return {
            'name': record_information['title'],
            'value': value,
            'inline': False
        }

    def get_flag(self, user):
        user = self.normalize_user(user)

        try:
            flag = f":flag_{self.countries[user]}:"
        except KeyError:
            flag = BLANK_FLAG

        return flag

    def tally(self, user):
        user = self.normalize_user(user)

        try:
            self.user_tally[user] += 1
        except KeyError:
            self.user_tally[user] = 1

        country = self.get_flag(user)
        try:
            self.country_tally[country] += 1
        except KeyError:
            self.country_tally[country] = 1

    def normalize_user(self, user):
        try:
            return self.accounts[user]
        except KeyError:
            return user


def setup(bot):
    bot.add_cog(TypeRacerOnly(bot))
