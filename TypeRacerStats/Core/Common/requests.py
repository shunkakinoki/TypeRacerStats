import asyncio
import json
import aiohttp


async def fetch_json(session, url, scraper, store_url):
    async with session.get(url) as response:
        response_ = json.loads(await response.read())
        if store_url:
            return {url: scraper(response_)}
        return scraper(response_)


async def fetch_html(session, url, scraper, store_url):
    async with session.get(url) as response:
        response_ = await response.text()
        if store_url:
            return {url: scraper(response_)}
        return scraper(response_)


async def fetch_html_read(session, url, scraper, store_url):
    async with session.get(url) as response:
        response_ = await response.read()
        if store_url:
            return {url: scraper(response_)}
        return scraper(response_)


async def fetch_jsons(urls, scraper, store_url):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_json(session, url, scraper, store_url) for url in urls]
        return await asyncio.gather(*tasks)


async def fetch_htmls(urls, scraper, store_url):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html(session, url, scraper, store_url) for url in urls]
        return await asyncio.gather(*tasks)


async def fetch_html_reads(urls, scraper, store_url):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_html_read(session, url, scraper, store_url) for url in urls
        ]
        return await asyncio.gather(*tasks)


async def fetch(urls, type_, scraper=lambda x: x, store_url=False):
    if type_ == 'json':
        answer = await fetch_jsons(urls, scraper, store_url)
    elif type_ == 'read':
        answer = await fetch_html_reads(urls, scraper, store_url)
    else:
        answer = await fetch_htmls(urls, scraper, store_url)
    return answer
