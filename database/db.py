import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей (добавили clan_id)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                balance INTEGER DEFAULT 10000,
                last_bonus TEXT,
                shame_mark TEXT,
                clan_id INTEGER
            )
        """)
        # Таблица кланов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                owner_id INTEGER,
                balance INTEGER DEFAULT 0
            )
        """)
        # Таблица заявок в кланы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clan_requests (
                user_id INTEGER,
                clan_id INTEGER,
                PRIMARY KEY (user_id, clan_id)
            )
        """)
        await db.commit()

async def get_user(uid, name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, last_bonus, clan_id FROM users WHERE id = ?", (uid,)) as cursor:
            res = await cursor.fetchone()
            if not res:
                await db.execute("INSERT INTO users (id, name, balance) VALUES (?, ?, 10000)", (uid, name))
                await db.commit()
                return (10000, None, None)
            return res

async def update_balance(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        await db.commit()
