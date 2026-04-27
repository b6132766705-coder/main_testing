import aiosqlite
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_user, update_balance, DB_PATH
from keyboards.reply import get_main_kb
from utils.formatters import fmt

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "🎰 **Добро пожаловать!**\nТвой стартовый баланс: 10 000 Угадаек.",
        reply_markup=get_main_kb(message.chat.type),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    res = await get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"💰 Баланс: **{fmt(res[0])}** Угадаек")

@router.message(F.text == "🎁 Бонус")
async def get_bonus(message: Message):
    # Код бонуса из предыдущих шагов
    pass
