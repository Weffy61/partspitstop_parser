import random


class ProxyManager:
    def __init__(self, proxy_file: str):
        self.proxies = []
        if proxy_file:
            with open(proxy_file, "r") as f:
                self.proxies = [line.strip() for line in f if line.strip()]

    def get(self):
        return random.choice(self.proxies) if self.proxies else None
