import asyncio

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from config import BASE_URL, OUTPUT_FILE
from notifications import send_message, send_end_message, send_error_message
from . import workers, core
from .proxy_manager import ProxyManager
from .utils import normalize_url, log

session = AsyncSession(impersonate='safari_ios')


async def collect_categories():
    category_workers = [
        asyncio.create_task(workers.category_worker())
        for _ in range(10)
    ]

    try:
        await core.category_queue.join()
    finally:
        for w in category_workers:
            w.cancel()
        await asyncio.gather(*category_workers, return_exceptions=True)


async def collect_years():
    years_workers = [
        asyncio.create_task(workers.year_worker())
        for _ in range(15)
    ]

    try:
        await core.year_queue.join()
    finally:
        for w in years_workers:
            w.cancel()
        await asyncio.gather(*years_workers, return_exceptions=True)


async def collect_models():
    models_workers = [
        asyncio.create_task(workers.model_worker())
        for _ in range(15)
    ]

    try:
        await core.model_queue.join()
    finally:
        for w in models_workers:
            w.cancel()
        await asyncio.gather(*models_workers, return_exceptions=True)


async def collect_parts():
    parts_workers = [
        asyncio.create_task(workers.parts_worker())
        for _ in range(15)
    ]

    try:
        await core.parts_queue.join()
    finally:
        for w in parts_workers:
            w.cancel()
        await asyncio.gather(*parts_workers, return_exceptions=True)


async def collect_details():
    details_workers = [
        asyncio.create_task(workers.details_worker())
        for _ in range(15)
    ]

    try:
        await core.details_queue.join()
    finally:
        for w in details_workers:
            w.cancel()
        await asyncio.gather(*details_workers, return_exceptions=True)


async def main(args):
    try:
        proxy_manager = ProxyManager(args.proxies)
        core.proxy_manager = proxy_manager
        core.session = session
        await send_message('🚀 Парсинг начат')

        html = await core.fetch_html(BASE_URL)
        soup = BeautifulSoup(html, 'lxml')
        main_div = soup.find(id='content-main')
        for a in main_div.select('div.grid_8 a[href]'):
            href = normalize_url(a.get('href'), BASE_URL)
            await core.enqueue_url(href, core.category_queue, 'category')

        await collect_categories()
        await send_message('Собраны категории')

        await collect_years()
        await send_message('Собраны года')

        await collect_models()
        await send_message('Собраны модели')

        await collect_parts()
        await send_message('Собраны части')

        await collect_details()
        await send_message('Собраны детали')

        await session.close()
        log('Parsing process completed successfully.')
        await send_end_message(OUTPUT_FILE)
    except Exception as ex:
        await send_error_message(ex)