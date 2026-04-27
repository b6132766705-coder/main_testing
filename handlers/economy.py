import aiosqlite
from datetime import datetime, timedelta
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_user, update_balance, DB_PATH
from utils.formatters import fmt
from keyboards.reply import get_main_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "🎰 Добро пожаловать в Угадайку!", 
        # Было:
        reply_markup=get_main_kb(message.chat.type)

        parse_mode="HTML"
    )


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    bal, _ = await get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"👤 **{message.from_user.first_name}**\n💰 Баланс: **{fmt(bal)}**")

@router.message(F.text == "🎁 Бонус")
async def get_bonus(message: Message):
    _, last_b = await get_user(message.from_user.id, message.from_user.full_name)
    now = datetime.now()
    
    if last_b and now - datetime.fromisoformat(last_b) < timedelta(hours=24):
        return await message.answer("⏳ Бонус можно брать раз в 24 часа!")

    amount = random.randint(500, 2000)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE id = ?", 
                         (amount, now.isoformat(), message.from_user.id))
        await db.commit()
    await message.answer(f"🎁 Вы получили **{fmt(amount)}**!")
