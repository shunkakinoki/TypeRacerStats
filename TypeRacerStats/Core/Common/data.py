import time
import sys
sys.path.insert(0, '')
from TypeRacerStats.Core.Common.urls import Urls
from TypeRacerStats.Core.Common.requests import fetch

async def get_registered(player, universe, start, end):
    urls = [Urls().get_races(player, universe, start, end)]

    try:
        api_response = await fetch(urls, 'json')
    except:
        return []

    api_response = api_response[0]
    if len(api_response) < 1000:
        return api_response
    else:
        return api_response + await get_registered(player, universe,
                                                   start, float(api_response[-1]['t']) - 0.01)

async def fetch_data(player, universe, start, end):
    registered_races = await get_registered(player, universe, start, end)
    if not registered_races:
        return None

    parsed_data = []

    for registered_race in registered_races:
        parsed_data.append((
            registered_race['gn'],
            registered_race['t'],
            registered_race['tid'],
            registered_race['wpm'],
            registered_race['pts']
        ))

    return parsed_data[::-1]
