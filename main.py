import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database.db import init_db
from handlers import games, economy, clans # Импортируем твои папки

async def main():
    # Инициализируем базу данных
    await init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры (обработчики)
    dp.include_routers(
        games.router,
        economy.router,
        clans.router
    )

    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
