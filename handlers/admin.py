import logging
import aiosqlite
from aiogram import Router, F
from aiogram.types import Message

from config import DB_PATH, ADMIN_ID # Убедись, что ADMIN_ID есть в config.py
from database.db import update_balance
from utils.formatters import fmt

router = Router()

# --- АДМИН-ЧИТ: ОБНУЛЕНИЕ ТАЙМЕРОВ ---
@router.message(lambda m: m.text and m.text.lower().startswith("обнулить"))
async def admin_reset(message: Message):
    if message.from_user.id != ADMIN_ID:
        return 

    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""UPDATE users SET 
                           last_steal = NULL, 
                           shame_mark = NULL, 
                           last_bonus = NULL 
                           WHERE id = ?""", (target_user.id,))
            await db.commit()
        
        await message.answer(f"🪄 **Магия!** Таймеры для {target_user.first_name} сброшены.", parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка при обнулении: {e}")
        await message.answer("❌ Произошла ошибка в базе данных.")

# --- АДМИН-КОМАНДЫ: ВЫДАЧА ПРЕДМЕТОВ ---
@router.message(F.reply_to_message, F.text.lower().startswith("+предмет"), lambda m: m.from_user.id == ADMIN_ID)
async def admin_give_item(message: Message):
    parts = message.text.split()
    try:
        item_name = parts[1]
        amount = int(parts[2]) if len(parts) > 2 else 1
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO inventory (user_id, item_name, amount) 
                VALUES (?, ?, ?) 
                ON CONFLICT(user_id, item_name) DO UPDATE SET amount = amount + ?
            """, (target_id, item_name, amount, amount))
            await db.commit()
        
        await message.answer(f"🪄 Админ выдал <b>{target_name}</b> предмет: <b>{item_name}</b> ({amount} шт.)", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка. Пример: <code>+предмет Клевер 5</code>", parse_mode="HTML")

# --- АДМИН-КОМАНДЫ: БАЛАНС ---
@router.message(F.reply_to_message, lambda m: m.from_user.id == ADMIN_ID)
async def admin_balance_change(message: Message):
    # Если текст начинается с + или - и это не выдача предмета
    if message.text.startswith(("+", "-")) and "предмет" not in message.text.lower():
        try:
            val = int(message.text.replace(" ", ""))
            await update_balance(message.reply_to_message.from_user.id, val)
            await message.answer(f"👑 Баланс игрока изменен на {fmt(val)}")
        except: 
            pass
