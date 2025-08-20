import asyncio


proxy_manager = None

visited_lock = asyncio.Lock()

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

semaphore = asyncio.Semaphore(5)


async def enqueue_url(url: str, queue: asyncio.Queue, stage: str) -> None:
    async with visited_lock:
        if url in visited[stage]:
            return
        visited[stage].add(url)
    await queue.put(url)
