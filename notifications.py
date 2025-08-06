from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from config import BOT_TOKEN, USER_ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def send_message(message: str):
    await bot.send_message(USER_ID, message)


async def send_end_message(filepath: str):
    try:
        file = FSInputFile(filepath)
        await bot.send_document(USER_ID, file, caption="✅ Парсинг окончен")
    except Exception as e:
        await bot.send_message(USER_ID, f"⚠️ Ошибка при отправке файла: {e}")


async def send_error_message(error: Exception):
    try:
        await bot.send_message(USER_ID, f"❌ Ошибка:\n{str(error)}")
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке сообщения об ошибке: {e}")