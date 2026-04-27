import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from database.db import init_db
from handlers import common

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Создаем таблицы в БД, если их нет
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Регистрируем наши роутеры
    dp.include_router(common.router)
    
    print("🚀 Бот успешно запущен!")
    await dp.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
