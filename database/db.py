import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                balance INTEGER DEFAULT 10000,
                last_bonus TEXT,
                shame_mark TEXT
            )
        """)
        await db.commit()

async def get_user(uid, name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, last_bonus FROM users WHERE id = ?", (uid,)) as cursor:
            res = await cursor.fetchone()
            if not res:
                await db.execute("INSERT INTO users (id, name) VALUES (?, ?)", (uid, name))
                await db.commit()
                return (10000, None)
            return res

async def update_balance(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        await db.commit()
