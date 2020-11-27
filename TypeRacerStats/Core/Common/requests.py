import asyncio
import json
import aiohttp

async def fetch_json(session, url, scraper):
    async with session.get(url) as response:
        response_ = json.loads(await response.read())
        return scraper(response_)

async def fetch_html(session, url, scraper):
    async with session.get(url) as response:
        response_ = await response.text()
        return scraper(response_)

async def fetch_html_read(session, url, scraper):
    async with session.get(url) as response:
        response_ = await response.read()
        return scraper(response_)

async def fetch_jsons(urls, scraper):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_json(session, url, scraper) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_htmls(urls, scraper):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html(session, url, scraper) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_html_reads(urls, scraper):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html_read(session, url, scraper) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch(urls, type_, scraper = lambda x: x):
    if type_ == 'json':
        answer = await fetch_jsons(urls, scraper)
    elif type_ == 'read':
        answer = await fetch_html_reads(urls, scraper)
    else:
        answer = await fetch_htmls(urls, scraper)
    return answer
