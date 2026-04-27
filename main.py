import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database.db import init_db
from handlers import economy, games, clans

async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры из папки handlers
    dp.include_routers(economy.router, games.router)
    
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
