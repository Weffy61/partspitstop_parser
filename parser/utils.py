from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse

from bs4 import BeautifulSoup


def normalize_url(url, base_url):
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        url = urljoin(base_url, url)
        parsed = urlparse(url)

    return urlunparse(('https', parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def log(msg: str):
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"[{current_time}][LOG] {msg}")


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
