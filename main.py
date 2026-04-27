import asyncio # Исправлено: маленькая буква
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperty # Для parse_mode
from aiogram.enums import ParseMode

from config import TOKEN
from database.db import init_db
from handlers import economy, games, clans, admin

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация БД
    await init_db()
    
    # Настройка бота с автоматическим HTML (чтобы не писать везде parse_mode)
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperty(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_routers(
        admin.router,
        economy.router,
        games.router,
        clans.router
    )
    
    # Очищаем очередь обновлений, чтобы бот не отвечал на старые сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Бот запущен и готов к игре!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
