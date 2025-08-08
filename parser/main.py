import asyncio
from asyncio import Queue

from bs4 import BeautifulSoup

from config import BASE_URL, OUTPUT_FILE, CATEGORY_WORKER_COUNT, YEAR_WORKER_COUNT, MODEL_WORKER_COUNT, \
    PARTS_WORKER_COUNT, DETAILS_WORKER_COUNT
from notifications import send_message, send_end_message, send_error_message
from . import workers, core
from .fetcher import fetch_html
from .proxy_manager import ProxyManager
from .utils import normalize_url, log


async def collect(worker_func, queue: Queue, workers_count: int):
    tasks = [asyncio.create_task(worker_func()) for _ in range(workers_count)]
    try:
        await queue.join()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def main(args):
    try:
        proxy_manager = ProxyManager(args.proxies)
        core.proxy_manager = proxy_manager
        await send_message('🚀 Парсинг начат')

        html = await fetch_html(BASE_URL)
        soup = BeautifulSoup(html, 'lxml')
        main_div = soup.find(id='content-main')
        for a in main_div.select('div.grid_8 a[href]'):
            href = normalize_url(a.get('href'), BASE_URL)
            await core.enqueue_url(href, core.category_queue, 'category')

        await collect(workers.category_worker, core.category_queue, CATEGORY_WORKER_COUNT)
        await send_message('Собраны категории')

        await collect(workers.year_worker, core.year_queue, YEAR_WORKER_COUNT)
        await send_message('Собраны года')

        await collect(workers.model_worker, core.model_queue, MODEL_WORKER_COUNT)
        await send_message('Собраны модели')

        await collect(workers.parts_worker, core.parts_queue, PARTS_WORKER_COUNT)
        await send_message('Собраны части')

        await collect(workers.details_worker, core.details_queue, DETAILS_WORKER_COUNT)
        await send_message('Собраны детали')

        log('Parsing process completed successfully.')
        await send_end_message(OUTPUT_FILE)
    except Exception as ex:
        await send_error_message(ex)
