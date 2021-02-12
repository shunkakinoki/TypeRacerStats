import datetime
import re
import sys
from bs4 import BeautifulSoup
sys.path.insert(0, '')
from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.requests import fetch


def compute_realspeed(quote_length, actual_time, start, lagged, desslejusted,
                      universe):
    if universe == 'lang_ko':
        mult = 24000
    elif universe == 'lang_zh' or universe == 'new_lang_zh-tw' or universe == 'lang_zh-tw' or universe == 'lang_ja':
        mult = 60000
    else:
        mult = 12000

    unlagged = round(mult * quote_length / actual_time, 2)
    ping = mult * quote_length / lagged - actual_time
    adjusted = round(mult * (quote_length - 1) / (actual_time - start), 3)
    if desslejusted:
        desslejusted_wpm = round(mult * quote_length / (actual_time - start),
                                 3)
    else:
        desslejusted_wpm = None

    return {
        'start': start,
        'unlagged': unlagged,
        'adjusted': adjusted,
        'ping': ping,
        'desslejusted': desslejusted_wpm
    }


async def find_registered(player, universe, gn, timestamp):
    urls = [Urls().get_races(player, universe, timestamp - 1, timestamp + 1)]
    api_response = await fetch(urls, 'json')
    for race in api_response[0]:
        if race['gn'] == gn:
            return race


def rs_typinglog_scraper(response):
    escapes = ''.join([chr(char) for char in range(1, 32)])

    try:
        soup = BeautifulSoup(response, 'html.parser')
        typinglog = re.sub(
            '\\t\d', 'a',
            re.search(r'typingLog\s=\s"(.*?)";',
                      response).group(1).encode().decode(
                          'unicode-escape').translate(escapes)).split('|')
        times = [int(c) for c in re.findall(r"\d+", typinglog[0])][2:]

        race_text = soup.select("div[class='fullTextStr']")[0].text.strip()
        player = soup.select("a[class='userProfileTextLink']")[0]["href"][13:]
        race_details = soup.select("table[class='raceDetails']")[0].select(
            'tr')
        universe = 'play'
        opponents = []
        for detail in race_details:
            cells = detail.select('td')
            category = cells[0].text.strip()
            if category == 'Race Number':
                race_number = int(cells[1].text.strip())
            elif category == 'Date':
                timestamp = int(
                    datetime.datetime.strptime(
                        cells[1].text.strip()[:-6],
                        "%a, %d %b %Y %H:%M:%S").strftime("%s"))
            elif category == 'Universe':
                universe = cells[1].text.strip()
            elif category == 'Opponents':
                opponents = [i['href'] for i in cells[1].select('a')]

        return {
            'player': player,
            'timestamp': timestamp,
            'race_number': race_number,
            'universe': universe,
            'race_text': race_text,
            'start': times[0],
            'duration': sum(times),
            'length': len(times),
            'opponents': opponents
        }
    except:
        return None


def raw_typinglog_scraper(response):
    escapes = ''.join([chr(char) for char in range(1, 32)])

    try:
        soup = BeautifulSoup(response, 'html.parser')
        typinglog = re.sub(
            '\\t\d', 'a',
            re.search(r'typingLog\s=\s"(.*?)";',
                      response).group(1).encode().decode(
                          'unicode-escape').translate(escapes)).split('|')
        times = [int(c) for c in re.findall(r"\d+", typinglog[0])][2:]

        race_text = soup.select("div[class='fullTextStr']")[0].text.strip()
        player = soup.select("a[class='userProfileTextLink']")[0]["href"][13:]
        race_details = soup.select("table[class='raceDetails']")[0].select(
            'tr')
        universe = 'play'
        opponents = []
        for detail in race_details:
            cells = detail.select('td')
            category = cells[0].text.strip()
            if category == 'Race Number':
                race_number = int(cells[1].text.strip())
            elif category == 'Date':
                timestamp = int(
                    datetime.datetime.strptime(
                        cells[1].text.strip()[:-6],
                        "%a, %d %b %Y %H:%M:%S").strftime("%s"))
            elif category == 'Universe':
                universe = cells[1].text.strip()
            elif category == 'Opponents':
                opponents = [i['href'] for i in cells[1].select('a')]

        try:
            actions = re.findall("\d+,(?:\d+[\+\-$].?)+,", typinglog[1])
            raw_actions, raw = [], []
            for action in actions:
                if action[-3] == "+":
                    raw_actions.append(action)
                else:
                    for _ in range(0, len(re.findall("\d+-.?", action))):
                        raw_actions.pop()
            for raw_action in raw_actions:
                raw.append(int(raw_action.split(',')[0]))
        except:
            raw = times

        return {
            'player': player,
            'timestamp': timestamp,
            'race_number': race_number,
            'universe': universe,
            'race_text': race_text,
            'start': times[0],
            'duration': sum(times),
            'length': len(times),
            'opponents': opponents,
            'correction': sum(times) - sum(raw),
            'adj_correction': sum(times[1:]) - sum(raw[1:])
        }
    except:
        return None


def timestamp_scraper(response):
    try:
        soup = BeautifulSoup(response, 'html.parser')
        player = soup.select("a[class='userProfileTextLink']")[0]["href"][13:]
        race_details = soup.select("table[class='raceDetails']")[0].select(
            'tr')
        universe = 'play'
        for detail in race_details:
            cells = detail.select('td')
            category = cells[0].text.strip()
            if category == 'Race Number':
                race_number = int(cells[1].text.strip())
            elif category == 'Date':
                timestamp = int(
                    datetime.datetime.strptime(
                        cells[1].text.strip()[:-6],
                        "%a, %d %b %Y %H:%M:%S").strftime("%s"))
            elif category == 'Universe':
                universe = cells[1].text.strip()

        return {
            'player': player,
            'timestamp': timestamp,
            'race_number': race_number,
            'universe': universe
        }
    except:
        return None


def scrape_text(response):
    try:
        soup = BeautifulSoup(response, 'html.parser')
        return soup.select('p')[0].text.strip()
    except IndexError:
        return None
