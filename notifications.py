from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from config import BOT_TOKEN, USER_ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def send_start_message():
    await bot.send_message(USER_ID, "🚀 Парсинг начат")


async def send_end_message(filepath: str):
    try:
        file = FSInputFile(filepath)
        await bot.send_document(USER_ID, file, caption="✅ Парсинг окончен")
    except Exception as e:
        await bot.send_message(USER_ID, f"⚠️ Ошибка при отправке файла: {e}")
