import asyncio, random
from aiogram import Router, F
from aiogram.types import Message
from database.db import update_balance, get_user
from utils.formatters import fmt

router = Router()
active_bets = {}

@router.message(F.text.regexp(r'^(\d+)\s+(.+)$'))
async def place_bet(message: Message):
    amount, target = int(message.text.split()[0]), message.text.split()[1].lower()
    bal, _ = await get_user(message.from_user.id, message.from_user.full_name)
    
    if bal < amount: return await message.answer("❌ Мало денег!")
    
    active_bets.setdefault(message.chat.id, {})[message.from_user.id] = {'amount': amount, 'target': target}
    await update_balance(message.from_user.id, -amount)
    await message.answer(f"✅ Ставка {fmt(amount)} на {target} принята! Жми «го»")

@router.message(F.text.lower() == "го")
async def spin(message: Message):
    bets = active_bets.pop(message.chat.id, {})
    if not bets: return await message.answer("Ставок нет!")
    
    res_num = random.randint(0, 36)
    await message.answer(f"🎰 Выпало: {res_num}")
    # Тут добавь логику проверки выигрыша, как в предыдущем шаге
