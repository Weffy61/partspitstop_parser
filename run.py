import argparse
import asyncio
from parser.main import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxies', help='Path to proxy list', default=None)
    args = parser.parse_args()

    asyncio.run(main(args))
