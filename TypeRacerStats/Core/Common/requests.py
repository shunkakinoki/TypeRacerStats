import asyncio
import json
import aiohttp

async def fetch_url(session, url, type_):
    async with session.get(url) as response:
        print(url)
        if type_ == 'json':
            return json.loads(await response.read())
        else:
            return await response.text()

async def fetch_urls(urls):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            tasks.append(fetch_url(session, url[0], url[1]))
        return await asyncio.gather(*tasks)

async def fetch(urls):
    answer = await fetch_urls(urls)
    return answer
