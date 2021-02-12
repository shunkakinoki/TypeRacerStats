from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.requests import fetch
from TypeRacerStats.Core.Common.data import fetch_data
from TypeRacerStats.file_paths import DATABASE_PATH, MAINTAIN_PLAYERS_TXT, TEMPORARY_DATABASE_PATH, TEXTS_FILE_PATH_CSV, TOPTENS_JSON_FILE_PATH, TOPTENS_FILE_PATH, TEXTS_LENGTHS, TEXTS_LARGE
import asyncio
import csv
import json
import re
import sqlite3
import sys
import time
from bs4 import BeautifulSoup
from discord.ext import tasks
sys.path.insert(0, '')


def maintain_text_files():
    texts_lengths = dict()
    texts_large = dict()

    with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            tid = str(row[0])
            texts_lengths.update({
                tid: {
                    'length': len(row[1]),
                    'word count': len(row[1].split(' '))
                }
            })

            texts_large.update({
                tid: f"{row[1][:50]}…"
            })

    with open(TEXTS_LENGTHS, 'w') as jsonfile:
        json.dump(texts_lengths, jsonfile)

    with open(TEXTS_LARGE, 'w') as jsonfile:
        json.dump(texts_large, jsonfile)


@tasks.loop(hours=24)
async def drop_temporary_tables():
    conn = sqlite3.connect(TEMPORARY_DATABASE_PATH)
    c = conn.cursor()
    tables = [i[0]
              for i in c.execute("SELECT name FROM sqlite_master").fetchall()]

    for table in tables:
        c.execute(f"DROP TABLE {table}")


@tasks.loop(hours=24)
async def maintain_players():
    with open(MAINTAIN_PLAYERS_TXT, 'r') as txtfile:
        players = txtfile.read().split('\n')

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    for player in players:
        print(f"Maintaining: {player}")
        last_race = c.execute(
            f"SELECT t FROM t_{player} ORDER BY gn DESC LIMIT 1").fetchone()[0]
        data = await fetch_data(player, 'play', last_race + 0.01, time.time())
        if data:
            c.executemany(
                f"INSERT INTO t_{player} VALUES (?, ?, ?, ?, ?)", data)
            conn.commit()

    conn.close()


@tasks.loop(hours=168)
async def maintain_top_tens():
    tids = []
    with open(TEXTS_FILE_PATH_CSV, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            tids.append(row[0])

    def scraper(response):
        soup = BeautifulSoup(response, 'html.parser')
        top_10 = soup.findAll('a', class_="userProfileTextLink")
        top_10_dict = {}
        for i in range(0, len(top_10)):
            top_10_dict.update({i + 1: top_10[i].text})
        return top_10_dict

    text_top_tens = {}
    urls, partition = [], []
    for i, tid in enumerate(tids):
        partition.append(Urls().tr_text(tid))
        if i % 500 == 0:
            urls.append(partition)
            partition = []

    for partition in urls:
        print(partition[0])
        data = (await fetch(partition, 'text', scraper, lambda x: re.findall('[0-9]+', x)[0]))
        for text in data:
            text_top_tens.update(text)
        await asyncio.sleep(100)

    with open(TOPTENS_JSON_FILE_PATH, 'w') as jsonfile:
        json.dump(text_top_tens, jsonfile)

    with open(TOPTENS_JSON_FILE_PATH, 'r') as jsonfile:
        text_top_tens = json.load(jsonfile)

    player_top_tens = {}
    for value in text_top_tens.values():
        for i in range(1, 11):
            try:
                player = value[str(i)]
                try:
                    current = player_top_tens[player]
                    current.update({i: current[i] + 1})
                except KeyError:
                    temp = {}
                    for j in range(1, 11):
                        if j == i:
                            temp.update({j: 1})
                        else:
                            temp.update({j: 0})
                    player_top_tens.update({player: temp})
            except KeyError:
                pass
    player_top_tens.update({'last updated': time.time()})

    with open(TOPTENS_FILE_PATH, 'w') as jsonfile:
        json.dump(player_top_tens, jsonfile)
