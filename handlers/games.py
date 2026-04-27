import asyncio, random
from aiogram import Router, F
from aiogram.types import Message
from database.db import update_balance, get_user
from utils.formatters import fmt

router = Router()
active_bets = {}

# --- МИНИ-ИГРА: УГАДАЙ ЧИСЛО ---
@dp.message(F.text == "🎮 Играть")
async def start_guess(message: Message, state: FSMContext):
    num = random.randint(1, 10)
    await state.set_state(GameStates.guessing)
    await state.update_data(target=num, attempts=3)
    await message.answer("Я загадал число от 1 до 10. У тебя 3 попытки! Пиши число:")

@dp.message(GameStates.guessing)
async def process_guess(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("Игра отменена.", reply_markup=get_main_kb(message.chat.type))

    if not message.text.isdigit(): 
        return await message.answer("Пожалуйста, введи только цифры! (Или напиши «Отмена»)")
    
    # ... дальше идет твой старый код проверки попыток ...
        
    guess = int(message.text)
    data = await state.get_data()
    target = data['target']
    attempts = data['attempts'] - 1

    if guess == target:
        await update_balance(message.from_user.id, 50)
        await message.answer(f"🎉 Угадал! +{fmt(50)} Угадаек.", reply_markup=get_main_kb(message.chat.type))
        await state.clear()
    elif attempts > 0:
        hint = "Больше!" if target > guess else "Меньше!"
        await state.update_data(attempts=attempts)
        await message.answer(f"Неверно. {hint} Осталось попыток: {attempts}")
    else:
        await message.answer(f"Попытки кончились! Это было {target}.", reply_markup=get_main_kb(message.chat.type))
        await state.clear()
