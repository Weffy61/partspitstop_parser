import asyncio
import random

import aiofiles
import json

from bs4 import BeautifulSoup
from curl_cffi import AsyncSession

from config import OUTPUT_FILE, IMPERSONATE_PROFILES
from .utils import log

seen_skus = set()
sku_lock = asyncio.Lock()
visited_lock = asyncio.Lock()

proxy_manager = None
session = None

visited = {
    'category': set(),
    'year': set(),
    'model': set(),
    'parts': set(),
    'details': set(),
}

category_queue = asyncio.Queue()
year_queue = asyncio.Queue()
model_queue = asyncio.Queue()
parts_queue = asyncio.Queue()
details_queue = asyncio.Queue()

semaphore = asyncio.Semaphore(60)


async def save_part(part: dict) -> None:
    async with sku_lock:
        if part['sku'] in seen_skus:
            return
        seen_skus.add(part['sku'])

    async with aiofiles.open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        await f.write(json.dumps(part, ensure_ascii=False) + "\n")
        await f.flush()


async def fetch_html(
        url: str,
        retries: int = 5,
        delay: float = 2.0,
        global_timeout:
        float = 40.0
) -> str:
    global session
    for attempt in range(1, retries + 1):
        async with semaphore:
            try:
                proxy = proxy_manager.get() if proxy_manager else None
                log(f"[{attempt}/{retries}] Fetching: {url} {f'(proxy: {proxy})' if proxy else ''}")
                resp = await asyncio.wait_for(
                    session.get(url, timeout=30, proxy=proxy),
                    timeout=global_timeout
                )
                if resp.status_code == 403 and is_blocked_page(resp.text):
                    log(f"[{attempt}/{retries}] Cloudflare block detected at {url}")
                    await session.close()
                    session = get_new_session()
                    if attempt == retries:
                        return '<BLOCKED>'
                    continue
                return resp.text
            except asyncio.TimeoutError:
                log(f'[{attempt}/{retries}] Timeout fetching {url}')
            except Exception as e:
                log(f'ERROR fetching {url}: {e} | STATUS CODE {resp.status_code}')
                await session.close()
                session = get_new_session()
        if attempt < retries:
            await asyncio.sleep(delay)
        else:
            log(f'GAVE UP: {url}')
            return ''


async def enqueue_url(url: str, queue: asyncio.Queue, stage: str) -> None:
    async with visited_lock:
        if url in visited[stage]:
            return
        visited[stage].add(url)
    await queue.put(url)


def is_year_select_page(soup: BeautifulSoup) -> bool:
    return any([
        soup.select_one("#partsselectlist"),
        soup.select_one("#fitmentselectlistx"),
        soup.select_one("#fitmentselectlist")
    ])


def get_fitment_select_element(soup: BeautifulSoup) -> str:
    for selector in ['#partsselectlist', '#fitmentselectlistx', '#fitmentselectlist']:
        if soup.select_one(selector):
            return selector.replace('#', '')


def is_blocked_page(response: str) -> bool:
    soup = BeautifulSoup(response, 'lxml')
    title = soup.title
    if title and 'attention required' in title.text.lower():
        return True
    return False


def get_new_session():
    profile = random.choice(IMPERSONATE_PROFILES)
    log(f'[!] Switching session with new impersonate: {profile}')
    return AsyncSession(impersonate=profile)
