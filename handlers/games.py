from aiogram import Router, F
from aiogram.types import Message
from database.db import get_db

router = Router()

@router.message(F.text.lower() == "го")
async def spin_roulette(message: Message):
    # Твоя логика из старого файла, но через роутер
    await message.answer("🎰 Крутим рулетку...")

@router.message(F.text.lower() == "лог")
async def show_history(message: Message):
    await message.answer("📜 Последние игры: ...")
