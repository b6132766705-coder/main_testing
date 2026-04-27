import aiosqlite
import os
from config import DB_PATH

# --- ФУНКЦИИ ---
async def init_db():
    # Создаем папку для БД, если её нет (нужно для Railway)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                           (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 10000, 
                            last_bonus TEXT, name TEXT, last_active TEXT, 
                            last_steal TEXT, shame_mark TEXT, clan_id INTEGER)''')
        
        # Таблица кланов
        await db.execute('''CREATE TABLE IF NOT EXISTS clans
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            name TEXT UNIQUE, 
                            owner_id INTEGER, 
                            balance INTEGER DEFAULT 0,
                            multiplier REAL DEFAULT 1.0,
                            level INTEGER DEFAULT 1)''')
        
        # Таблица заявок в кланы
        await db.execute('''CREATE TABLE IF NOT EXISTS clan_requests 
                           (user_id INTEGER, clan_id INTEGER, 
                            PRIMARY KEY (user_id, clan_id))''')
        
        # Таблица истории рулетки
        await db.execute('''CREATE TABLE IF NOT EXISTS history (number INTEGER)''')
        
        # Таблица инвентаря
        await db.execute('''CREATE TABLE IF NOT EXISTS inventory 
                           (user_id INTEGER, item_name TEXT, amount INTEGER DEFAULT 1,
                            PRIMARY KEY (user_id, item_name))''')
        
        # Проверка и добавление колонок, если БД уже была создана ранее
        try:
            await db.execute("ALTER TABLE clans ADD COLUMN multiplier REAL DEFAULT 1.0")
            await db.execute("ALTER TABLE clans ADD COLUMN level INTEGER DEFAULT 1")
        except:
            pass
            
        await db.commit()

async def get_user(user_id, name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, last_bonus FROM users WHERE id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            
        if not res:
            await db.execute("INSERT INTO users (id, balance, name) VALUES (?, ?, ?)", (user_id, 10000, name))
            await db.commit()
            return (10000, None)
        else:
            # Обновляем имя пользователя при каждом входе
            await db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            await db.commit()
            return res

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (int(amount), user_id))
        await db.commit()
