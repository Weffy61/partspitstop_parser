import asyncio

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

import core
import workers
from config import BASE_URL, OUTPUT_FILE
from notifications import send_start_message, send_end_message
from proxy_manager import ProxyManager
from utils import normalize_url, log

session = AsyncSession(impersonate='safari_ios')


async def main(args):
    proxy_manager = ProxyManager(args.proxies)
    await send_start_message()

    html = await core.fetch_html(BASE_URL)
    soup = BeautifulSoup(html, 'lxml')
    main_div = soup.find(id='content-main')
    for a in main_div.select('div.grid_8 a[href]'):
        href = normalize_url(a.get('href'), BASE_URL)
        await core.enqueue_url(href, core.category_queue, 'category')

    workers_list = [
        asyncio.create_task(workers.category_worker()),
        asyncio.create_task(workers.year_worker()),
        asyncio.create_task(workers.model_worker()),
        asyncio.create_task(workers.parts_worker()),
        *[asyncio.create_task(workers.details_worker()) for _ in range(50)]
    ]

    await core.category_queue.join()
    await core.year_queue.join()
    await core.model_queue.join()
    await core.parts_queue.join()
    await core.details_queue.join()

    await session.close()
    for w in workers_list:
        w.cancel()

    log('Parsing process completed successfully.')
    await send_end_message(OUTPUT_FILE)
