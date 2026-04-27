import aiosqlite
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import DB_PATH
from database.db import get_user
from utils.formatters import fmt
from keyboards.reply import get_main_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        f"Привет! Я — <b>Угадайка бот</b>. 🎰\n"
        f"Даю тебе стартовый капитал: {fmt(10000)} Угадаек!\n\n"
        f"Жми «Играть», чтобы испытать удачу!", 
        reply_markup=get_main_kb(message.chat.type),
        parse_mode="HTML"
    )

@router.message(Command("commands", "comands", "help"))
async def cmd_commands(message: Message):
    help_text = (
        "🎮 <b>Все команды «Угадайка бот»:</b>\n\n"
        "<b>💰 Экономика:</b>\n"
        "• /start — Начать игру и получить бонус\n"
        "• <code>👤 Профиль</code> или <code>б</code> — Баланс\n"
        "• <code>🎁 Бонус</code> — Ежедневный подарок\n"
        "• <code>п [сумма]</code> (ответ) — Передать Угадайки\n"
        "• <code>🏆 Рейтинг</code> — Топ богачей\n\n"
        "<b>🎰 Азарт:</b>\n"
        "• <code>[сумма] [ставка]</code> — Ставка (число, к, ч)\n"
        "• <code>го</code> — Запуск рулетки\n"
        "• <code>лог</code> — История игр\n"
        "• <code>дуэль [сумма]</code> — Вызвать на бой\n\n"
        "<b>🛡 Кланы:</b>\n"
        "• <code>клан</code> — Меню клана\n"
        "• <code>Вступить [Название]</code> — Заявка\n\n"
        "<b>📜 Прочее:</b>\n"
        "• /rules — Правила игры\n"
        "• /commands — Этот список"
    )
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("rules"))
async def cmd_rules(message: Message):
    rules_text = (
        "📜 <b>Правила «Угадайка бот»</b>\n\n"
        "1️⃣ <b>Ставки:</b> Принимаются числа от 0 до 36, цвета (к, ч) и чет/нечет.\n"
        "2️⃣ <b>Запуск:</b> Только тот, кто сделал ставку, может прописать «го».\n"
        "3️⃣ <b>Кланы:</b> Создание клана стоит 20 000. Лидер управляет казной.\n"
        "4️⃣ <b>Награда:</b> Приглашай друзей в чат и получай <b>10 000</b> за каждого!\n"
        "5️⃣ <b>Штрафы:</b> Неудачная попытка кражи вешает клеймо клоуна на 3 часа.\n"
        "🛡 Щит — автоматически защищает от ограбления (расходуется при нападении).\n\n"
        "<i>Удачи в игре!</i>"
    )
    await message.answer(rules_text, parse_mode="HTML")

@router.message(F.text == "👤 Профиль")
@router.message(F.text.lower() == "б")
async def show_profile(message: Message):
    uid = message.from_user.id
    await get_user(uid, message.from_user.full_name) 
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, shame_mark FROM users WHERE id = ?", (uid,)) as cursor:
            res = await cursor.fetchone()
    
    balance, shame_str = res
    status = "🟢 Обычный гражданин"
    
    if shame_str:
        shame_time = datetime.fromisoformat(shame_str)
        if datetime.now() < shame_time:
            left = shame_time - datetime.now()
            m = (left.seconds // 60) + 1
            status = f"🤡 Неудачливый воришка (еще {m} мин.)"

    await message.answer(f"👤 **Профиль:** {message.from_user.first_name}\n💰 **Баланс:** {fmt(balance)} Угадаек\n📝 **Статус:** {status}", parse_mode="Markdown")

