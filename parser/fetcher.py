import asyncio
import random

from bs4 import BeautifulSoup
from curl_cffi import AsyncSession

from config import IMPERSONATE_PROFILES
from parser.core import semaphore, proxy_manager
from parser.utils import log


async def fetch_html(
        url: str,
        retries: int = 5,
        delay: float = 2.0,
        global_timeout:
        float = 40.0
) -> str:
    for attempt in range(1, retries + 1):
        async with semaphore:
            session = get_new_session()
            proxy = proxy_manager.get() if proxy_manager else None
            resp = None
            log(f"[{attempt}/{retries}] Fetching: {url} {f'(proxy: {proxy})' if proxy else ''}")
            try:
                resp = await asyncio.wait_for(
                    session.get(url, timeout=30, proxy=proxy),
                    timeout=global_timeout
                )
                html = resp.text
                if resp.status_code == 403 and is_blocked_page(resp.text):
                    log(f"[{attempt}/{retries}] Cloudflare block detected at {url} "
                        f"{f'(proxy: {proxy})' if proxy else ''}")
                    if attempt == retries:
                        return '<BLOCKED>'
                    continue
                if not html.strip():
                    log(f"[{attempt}/{retries}] Empty response from {url} (possibly blocked)")
                    if attempt == retries:
                        return '<EMPTY>'
                    continue
                return resp.text
            except asyncio.TimeoutError:
                log(f'[{attempt}/{retries}] Timeout fetching {url}')
            except Exception as e:
                status = getattr(resp, 'status_code', 0)
                log(f'ERROR fetching {url}: {e} | STATUS CODE {status}')
            finally:
                await session.close()
        if attempt < retries:
            await asyncio.sleep(delay)
        else:
            log(f'GAVE UP: {url}')
            return '<ERROR>'


async def handle_fetch_result(html: str, url: str, queue: asyncio.Queue, worker_name: str) -> bool:
    if html == '<BLOCKED>':
        log(f"[{worker_name}] Blocked by Cloudflare: {url}, retrying")
        await queue.put(url)
        queue.task_done()
        return False
    if html == '<EMPTY>':
        log(f'[{worker_name}] Empty response from {url}, retrying')
        await queue.put(url)
        queue.task_done()
        return False
    if html == '<ERROR>':
        log(f"[{worker_name}] Error fetching {url}")
        queue.task_done()
        return False
    return True


def is_blocked_page(response: str) -> bool:
    soup = BeautifulSoup(response, 'lxml')
    title = soup.title
    if title and 'attention required' in title.text.lower():
        return True
    return False


def get_new_session():
    profile = random.choice(IMPERSONATE_PROFILES)
    return AsyncSession(impersonate=profile)
