import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database.db import init_db
from handlers import economy, games, clans, admin # Импортируем твои файлы

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем все роутеры
    dp.include_routers(
        admin.router,
        economy.router,
        games.router,
        clans.router
    )
    
    print("🚀 Бот запущен и готов к игре!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
