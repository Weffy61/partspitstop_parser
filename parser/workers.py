from bs4 import BeautifulSoup

from parser.core import save_part, details_queue, fetch_html, category_queue, enqueue_url, year_queue, model_queue, \
    get_fitment_select_element, is_year_select_page, parts_queue
from parser.utils import normalize_url, log


async def category_worker() -> None:
    while True:
        url = await category_queue.get()
        try:
            html = await fetch_html(url)
            if not html:
                log(f'[category_worker] Empty HTML from {url}')
                category_queue.task_done()
                continue

            soup = BeautifulSoup(html, 'lxml')

            if is_year_select_page(soup):
                await enqueue_url(url, year_queue, 'year')
            else:
                main_div = soup.find(id='content-main')
                if main_div:
                    for a in main_div.select('div.grid_8 a[href]'):
                        href = normalize_url(a.get('href'), url)
                        await enqueue_url(href, category_queue, 'category')
        except Exception as ex:
            log(f'Uncaught error in category_worker for {url}: {ex}')
        category_queue.task_done()


async def year_worker() -> None:
    while True:
        url = await year_queue.get()
        try:
            html = await fetch_html(url)
            if not html:
                log(f"[year_worker] Empty HTML from {url}")
                year_queue.task_done()
                continue
            soup = BeautifulSoup(html, 'lxml')
            selector = get_fitment_select_element(soup)
            if not selector:
                year_queue.task_done()
                continue
            year_grid = soup.find(id=selector)
            for a in year_grid.select('div.widget.rounded li a[href]'):
                href = normalize_url(a.get('href'), url)
                await enqueue_url(href, model_queue, 'model')
        except Exception as ex:
            log(f'Uncaught error in year_worker for {url}: {ex}')
        year_queue.task_done()


async def model_worker() -> None:
    while True:
        url = await model_queue.get()
        try:
            html = await fetch_html(url)
            if not html:
                log(f"[model_worker] Empty HTML from {url}")
                model_queue.task_done()
                continue
            soup = BeautifulSoup(html, 'lxml')
            selector = get_fitment_select_element(soup)
            if not selector:
                model_queue.task_done()
                continue
            parts_grid = soup.find(id=selector)
            for a in parts_grid.select('ul.columnlist li a[href]'):
                href = normalize_url(a.get('href'), url)
                await enqueue_url(href, parts_queue, 'parts')
        except Exception as ex:
            log(f'Uncaught error in model_worker for {url}: {ex}')
        model_queue.task_done()


async def parts_worker() -> None:
    while True:
        url = await parts_queue.get()
        try:
            html = await fetch_html(url)
            if not html:
                log(f"[parts_worker] Empty HTML from {url}")
                parts_queue.task_done()
                continue
            soup = BeautifulSoup(html, 'lxml')
            elements = soup.select('#partassemthumblist div.wrap')
            if not elements:
                elements = soup.select('#previewcontainer div.preview')
            for el in elements:
                a = el.select_one('a[href]')
                if a:
                    href = normalize_url(a.get('href'), url)
                    await enqueue_url(href, details_queue, 'details')
        except Exception as ex:
            log(f'Uncaught error in parts_worker for {url}: {ex}')
        parts_queue.task_done()


async def details_worker() -> None:
    while True:
        url = await details_queue.get()
        try:
            html = await fetch_html(url)
            if not html:
                log(f"[details_worker] Empty HTML from {url}")
                details_queue.task_done()
                continue
            soup = BeautifulSoup(html, 'lxml')
            detail_block = soup.select('#partlist .partlistrow form')
            if detail_block:
                for detail in detail_block:
                    brand = detail.get('data-brand')
                    title = detail.get('data-name')
                    sku = detail.get('data-sku')
                    price = detail.get('data-retail')
                    if 'SEE PART DETAILS' in title:
                        price = '0'
                    part = {
                        'brand': brand,
                        'title': title,
                        'sku': sku,
                        'price': price
                    }
                    await save_part(part)
            else:
                name_block = soup.select_one('.productdetail')
                brand = name_block.select_one('p.brand').text.strip()

                detail = soup.select_one('#divItemList')
                title = detail.select_one('p.name').text.strip()
                sku = detail.select_one('p.sku span').text.strip()
                price = detail.select_one('meta[itemprop="price"]').get('content', '0')
                if 'SEE PART DETAILS' in title:
                    price = '0'
                part = {
                    'brand': brand,
                    'title': title,
                    'sku': sku,
                    'price': price
                }
                await save_part(part)
        except AttributeError:
            log(f'CloudFlare error, running task again')
            await details_queue.put(url)
        except Exception as ex:
            log(f'Uncaught error in details_worker for {url}: {ex}')
        details_queue.task_done()
