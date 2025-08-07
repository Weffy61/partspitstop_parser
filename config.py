from datetime import datetime
import os
from environs import Env

env = Env()
env.read_env()

OUTPUT_DIR = env.str('OUTPUT_DIR', './data')
BOT_TOKEN = env.str('BOT_TOKEN')
USER_ID = env.int('USER_ID')
BASE_URL = 'https://www.partspitstop.com'

os.makedirs(OUTPUT_DIR, exist_ok=True)

timestamp = datetime.now().strftime('%d-%m-%Y-%H-%M')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f'results_{timestamp}.jsonl')

IMPERSONATE_PROFILES = [
    'chrome99', 'chrome100', 'chrome101', 'chrome104', 'chrome107', 'chrome110',
    'chrome116', 'chrome119', 'chrome120', 'chrome99_android', 'edge99', 'edge101',
    'safari15_3', 'safari15_5', 'safari17_0', 'safari17_2_ios', 'safari_ios', 'safari',
    'chrome'
]

