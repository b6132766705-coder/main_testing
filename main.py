import asyncio
import logging
from aiogram import Bot, Dispatcher
# Внимательно: Properties в конце с буквой 's'
from aiogram.client.default import DefaultBotProperties 
from aiogram.enums import ParseMode

from config import TOKEN
from database.db import init_db
from handlers import economy, games, clans, admin

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    
    # Исправлено здесь тоже
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_routers(
        admin.router,
        economy.router,
        games.router,
        clans.router
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
