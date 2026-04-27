import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database.db import init_db
from handlers import economy, games, clans

async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(economy.router)
    dp.include_router(games.router)
    dp.include_router(clans.router)

    
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
