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

# --- КОМАНДЫ ---

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


# --- СПИСОК КОМАНД ---
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
        "• <code>дуэль [сумма]</code> — Вызвать на бой\n"
        
        "<b>🛡 Кланы:</b>\n"
        "• <code>клан</code> — Меню клана\n"
        "• <code>Вступить [Название]</code> — Заявка\n\n"
        
        "<b>📜 Прочее:</b>\n"
        "• /rules — Правила игры\n"
        "• /commands — Этот список"
    )
    await message.answer(help_text, parse_mode="HTML")

# --- ПРАВИЛА ---
@router.message(Command("rules"))
async def cmd_rules(message: Message):
    rules_text = (
        "📜 <b>Правила «Угадайка бот»</b>\n\n"
        "1️⃣ <b>Ставки:</b> Принимаются числа от 0 до 36, цвета (к, ч) и чет/нечет.\n"
        "2️⃣ <b>Запуск:</b> Только тот, кто сделал ставку, может прописать «го».\n"
        "3️⃣ <b>Кланы:</b> Создание клана стоит 20 000. Лидер управляет казной.\n"
        "4️⃣ <b>Награда:</b> Приглашай друзей в чат и получай <b>10 000</b> за каждого!\n"
        "5️⃣ <b>Штрафы:</b> Неудачная попытка кражи вешает клеймо клоуна на 3 часа.\n\n"
        # В блоке правил добавь строчку:
        "🛡 Щит — автоматически защищает от ограбления (расходуется при нападении)."

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

@router.message(F.text.lower().startswith("п "), F.reply_to_message)
async def transfer(message: Message):
    try:
        amount = int(message.text.split()[1])
        sender_id = message.from_user.id
        receiver = message.reply_to_message.from_user
        if amount <= 0 or sender_id == receiver.id: return
        
        res = await get_user(sender_id, message.from_user.full_name)
        bal = res[0]
        
        if bal < amount: return await message.answer("❌ Недостаточно Угадаек!")
        
        await update_balance(sender_id, -amount)
        await update_balance(receiver.id, amount)
        await message.answer(f"✅ Переведено {fmt(amount)} Угадаек для {receiver.first_name}")
    except: pass

@router.message(F.text == "🎁 Бонус")
async def get_bonus(message: Message):
    res = await get_user(message.from_user.id, message.from_user.full_name)
    balance, last_bonus_str = res
    now = datetime.now()
    
    if last_bonus_str:
        last_b = datetime.fromisoformat(last_bonus_str)
        if now - last_b < timedelta(hours=24):
            left = timedelta(hours=24) - (now - last_b)
            h, rem = divmod(left.seconds, 3600)
            m, _ = divmod(rem, 60)
            return await message.answer(f"⏳ Бонус уже получен!\nВозвращайся через **{h} ч. {m} мин.**")

    bonus_amount = random.randint(100, 5000)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE id = ?", 
                    (bonus_amount, now.isoformat(), message.from_user.id))
        await db.commit()
        
    await message.answer(f"🎁 Ты получил бонус: **{fmt(bonus_amount)}** Угадаек!")

# --- ЕДИНЫЙ РЕЙТИНГ (Кнопка + Команда) ---
@router.message(F.text == "🏆 Рейтинг")
@router.message(Command("top"))
async def show_rating(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, balance, id FROM users ORDER BY balance DESC LIMIT 10") as cursor:
            top_users = await cursor.fetchall()
    
    if not top_users:
        return await message.answer("🏆 Список богачей пока пуст!")

    text = "🏆 <b>ТОП-10 МИЛЛИОНЕРОВ:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (name, bal, uid) in enumerate(top_users):
        place = medals[i] if i < 3 else f"<b>{i+1}.</b>"
        display_name = name if name else "Игрок"
        # Ссылка на профиль игрока
        text += f"{place} <a href='tg://user?id={uid}'>{display_name}</a> — <b>{fmt(bal)}</b>\n"
    
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "📊 Ставки")
async def show_my_bets(message: Message):
    cid = message.chat.id
    uid = message.from_user.id
    if cid not in pending_bets or not any(b['user_id'] == uid for b in pending_bets[cid]):
        return await message.answer("У тебя нет активных ставок.")
    
    my_bets = [b for b in pending_bets[cid] if b['user_id'] == uid]
    text = "📝 Твои текущие ставки:\n"
    for b in my_bets:
        for t in b['targets']:
            text += f"• {fmt(b['amount'])} ➔ {t}\n"
    await message.answer(text)

@router.message(F.text == "🚫 Отмена")
async def cancel_my_bets(message: Message):
    cid = message.chat.id
    uid = message.from_user.id
    if cid in pending_bets:
        user_bets = [b for b in pending_bets[cid] if b['user_id'] == uid]
        if user_bets:
            refund = sum(b['amount'] * len(b['targets']) for b in user_bets)
            pending_bets[cid] = [b for b in pending_bets[cid] if b['user_id'] != uid]
            await update_balance(uid, refund)
            return await message.answer(f"✅ Ставки отменены. Возвращено: {fmt(refund)}")
    await message.answer("У тебя нет активных Ставок")
