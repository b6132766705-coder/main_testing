import aiosqlite
from config import DB_PATH

async def get_db():
    return await aiosqlite.connect(DB_PATH)

async def init_db():
    async with await get_db() as db:
        # Сюда перенеси все свои CREATE TABLE из старого кода
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 10000,
                clan_id INTEGER
            )
        """)
        # ... и остальные таблицы
        await db.commit()
