import asyncio
import json

import aiofiles

from config import OUTPUT_FILE

seen_skus = set()
sku_lock = asyncio.Lock()


async def save_part(part: dict) -> None:
    async with sku_lock:
        if part['sku'] in seen_skus:
            return
        seen_skus.add(part['sku'])

    async with aiofiles.open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        await f.write(json.dumps(part, ensure_ascii=False) + "\n")
        await f.flush()

