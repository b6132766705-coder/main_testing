from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Это та самая строка, которую ищет main.py
router = Router()

@router.message(F.text == "🛡 Клан")
@router.message(Command("clan"))
async def clan_menu(message: Message):
    await message.answer(
        "🛡 **Меню кланов**\n\n"
        "Здесь ты можешь создать свой клан или вступить в существующий.\n"
        "Команды:\n"
        "• `Создать [название]` — 20 000 Угадаек\n"
        "• `Вступить [название]` — отправить заявку",
        parse_mode="Markdown"
    )

