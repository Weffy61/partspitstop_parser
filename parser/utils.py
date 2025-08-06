from urllib.parse import urlparse, urljoin, urlunparse


def normalize_url(url, base_url):
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        url = urljoin(base_url, url)
        parsed = urlparse(url)

    return urlunparse(('https', parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def log(msg: str):
    print(f"[LOG] {msg}")
