from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup # Добавь эту строку!

from keyboards.reply import get_main_kb # Импорт, который мы обсуждали ранее
from database.db import update_balance, get_user
from utils.formatters import fmt

import asyncio, random

router = Router()
pending_bets = {}


# Обязательно добавь этот класс, чтобы ошибка GameStates исчезла!
class GameStates(StatesGroup):
    guessing = State() 



# --- МИНИ-ИГРА: УГАДАЙ ЧИСЛО ---
@router.message(F.text == "🎮 Играть")
async def start_guess(message: Message, state: FSMContext):
    num = random.randint(1, 10)
    await state.set_state(GameStates.guessing)
    await state.update_data(target=num, attempts=3)
    await message.answer("Я загадал число от 1 до 10. У тебя 3 попытки! Пиши число:")

@router.message(GameStates.guessing)
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

# --- РУЛЕТКА ---
def is_valid_bet_format(m: Message):
    if not m.text: return False
    parts = m.text.lower().split()
    if len(parts) < 2: return False # Должно быть хотя бы 2 слова (сумма + ставка)
    
    first_word = parts[0]
    if not (first_word.isdigit() or first_word in ["все", "всё"]):
        return False
        
    return True

@router.message(is_valid_bet_format)
async def take_bet(message: Message):
    if message.chat.type == "private":
        return await message.answer("🎰 В рулетку можно играть только в группах! Добавь меня в чат с друзьями.")
    parts = message.text.split()
    if len(parts) < 2:
        return 

    try:
        raw_targets = [t.lower() for t in parts[1:]]
        valid_targets = []
        invalid_targets = []
        
        for t in raw_targets:
            if t in ["к", "кр", "красное", "ч", "чр", "черное", "чет", "нечет"]:
                valid_targets.append(t)
            elif t.isdigit() and 0 <= int(t) <= 36:
                valid_targets.append(t)
            elif "-" in t:
                try:
                    low, high = map(int, t.split("-"))
                    if 0 <= low <= 36 and 0 <= high <= 36 and low < high:
                        valid_targets.append(t)
                    else:
                        invalid_targets.append(t)
                except:
                    invalid_targets.append(t)
            else:
                invalid_targets.append(t)
                
        if invalid_targets:
            return await message.answer(f"❌ Ошибка в купоне!\nЯ не понимаю эти ставки: **{', '.join(invalid_targets)}**\n\nРазрешены: числа (0-36), цвета (к, ч), чет/нечет и диапазоны (например 1-18).", parse_mode="Markdown")
        
        targets = valid_targets
        count = len(targets)

        uid = message.from_user.id
        user_name = message.from_user.full_name
        res = await get_user(uid, user_name)
        bal = res[0]
        
        first_word = parts[0].lower() 

        if first_word in ["все", "всё"]:
            amount = bal // count  
            if amount <= 0:
                return await message.answer("❌ Твоего баланса не хватит!")
        else:
            amount = int(first_word)
            if amount <= 0: return

        total_needed = amount * count
        if bal < total_needed:
            return await message.answer(f"❌ Не хватает Угадаек!\nВаш баланс: {fmt(bal)}\nНужно: {fmt(total_needed)}")

        cid = message.chat.id
        if cid not in pending_bets:
            pending_bets[cid] = []
        
        pending_bets[cid].append({
            "user_id": uid, 
            "name": message.from_user.first_name, 
            "amount": amount, 
            "targets": targets
        })
        
        await update_balance(uid, -total_needed)
        
        report = f"✅ Ставок принято: {count}\n"
        if first_word in ["все", "всё"]:
            report += f"🔥 **ВА-БАНК!**\n"
        
        report += f"💸 Потрачено: {fmt(total_needed)}\n\n📊 **Ваш купон:**\n"
        for t in targets:
            report += f"• {fmt(amount)} ➔ {t}\n"
            
        await message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Ошибка в ставке: {e}")

@router.message(F.text.lower() == "go")
@router.message(F.text.lower() == "го")
async def spin(message: Message):
    if message.chat.type == "private":
        return await message.answer("🎰 В рулетку можно играть только в группах!")
    
    cid = message.chat.id
    if cid not in pending_bets or not pending_bets[cid]:
        return await message.answer("🎰 Ставок пока нет!")

    # 1. Крутим колесо
    res_num = random.randint(0, 36)
    
    # Открываем соединение с БД для записи истории и проверки кланов
    async with aiosqlite.connect(DB_PATH) as db:
        # Сохраняем в историю
        await db.execute("INSERT INTO history (number) VALUES (?)", (res_num,))
        await db.commit()

        # Определяем цвет для заголовка
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        if res_num == 0:
            header_color = "🟢 ЗЕРО"
            res_color_key = "зеро"
        elif res_num in red_numbers:
            header_color = "🔴 КРАСНОЕ"
            res_color_key = "к"
        else:
            header_color = "⚫ ЧЁРНОЕ"
            res_color_key = "ч"

        header_text = f"🎰 {header_color} {res_num}\n\n"
        user_reports = []

        # 2. Обрабатываем ставки каждого игрока
        for bet in pending_bets[cid]:
            uid = bet['user_id']
            name = bet['name']
            amount = bet['amount']
            targets = bet['targets']
            
            # --- НОВАЯ ЛОГИКА: Получаем клановый множитель игрока ---
            query = "SELECT multiplier FROM clans WHERE id = (SELECT clan_id FROM users WHERE id = ?)"
            async with db.execute(query, (uid,)) as cur:
                row = await cur.fetchone()
                clan_mult = row[0] if row else 1.0 # Если нет клана, множитель 1.0
            
            total_won = 0
            target_lines = []
            
            for t in targets:
                is_win = False
                mult = 0
                
                if t.isdigit() and int(t) == res_num:
                    is_win, mult = True, 36
                elif t in ["к", "кр", "красное"] and res_color_key == "к":
                    is_win, mult = True, 2
                elif t in ["ч", "чр", "черное"] and res_color_key == "ч":
                    is_win, mult = True, 2
                elif t == "чет" and res_num != 0 and res_num % 2 == 0:
                    is_win, mult = True, 2
                elif t == "нечет" and res_num % 2 != 0:
                    is_win, mult = True, 2
                elif "-" in t:
                    low, high = map(int, t.split("-"))
                    if low <= res_num <= high:
                        is_win, mult = True, 2

                if is_win:
                    # ПРИМЕНЯЕМ КЛАНОВЫЙ МНОЖИТЕЛЬ
                    current_win = int(amount * mult * clan_mult) 
                    total_won += current_win
                    target_lines.append(f"✅ {fmt(amount)} ➔ {t}")
                else:
                    target_lines.append(f"❌ {fmt(amount)} ➔ {t}")

            # Рассчитываем чистый итог (сколько выиграл минус сколько поставил)
            total_spent = amount * len(targets)
            profit_loss = total_won - total_spent
            
            if total_won > 0:
                await update_balance(uid, total_won)

            user_block = f"👤 {name}:\n" + "\n".join(target_lines)
            
            # Если множитель больше 1, добавляем пометку о бонусе
            sign = "+" if profit_loss > 0 else ""
            bonus_text = f" (x{clan_mult} 💎)" if clan_mult > 1.0 else ""
            user_block += f"\n💰 Итог: {sign}{fmt(profit_loss)}{bonus_text}"
            
            user_reports.append(user_block)

    # 3. Собираем всё сообщение и отправляем
    final_text = header_text + "\n\n".join(user_reports)
    pending_bets[cid] = []
    
    await message.answer(final_text, parse_mode="HTML")

@router.message(F.text.lower() == "лог")
async def show_history(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        # Достаем 10 последних записей
        async with db.execute("SELECT number FROM history ORDER BY rowid DESC LIMIT 10") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.answer("📜 История игр пока пуста.")

    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    history_lines = []

    for i, (num,) in enumerate(rows, 1):
        if num == 0:
            color_circle = "🟢"
            color_name = "ЗЕРО"
        elif num in red_numbers:
            color_circle = "🔴"
            color_name = "КРАСНОЕ"
        else:
            color_circle = "⚫"
            color_name = "ЧЁРНОЕ"
        
        history_lines.append(f"{i}. 🎰 {color_circle} {color_name} {num}")

    res_text = "📜 <b>История:</b>\n\n" + "\n".join(history_lines)
    await message.answer(res_text, parse_mode="HTML")

# --- ИГРА: ДУЭЛЬ ---
@router.message(F.text.lower().startswith("дуэль ") | F.text.lower().startswith("дуель "), F.reply_to_message)
async def start_duel(message: Message):
    if message.chat.type == "private":
        return await message.answer("❌ Дуэли возможны только в группах!")

    try:
        parts = message.text.split()
        if len(parts) < 2: return
        
        amount = int(parts[1])
        if amount <= 0: return
        
        challenger = message.from_user 
        victim = message.reply_to_message.from_user 
        
        if challenger.id == victim.id:
            return await message.answer("🤔 Самострел запрещен! Выбери другого оппонента.")
        if victim.is_bot:
            return await message.answer("🤖 Боты бессмертны, с ними нет смысла стреляться.")

        res_c = await get_user(challenger.id, challenger.full_name)
        c_bal = res_c[0]
        
        res_v = await get_user(victim.id, victim.full_name)
        v_bal = res_v[0]

        if c_bal < amount:
            return await message.answer(f"❌ У тебя не хватает {fmt(amount)} Угадаек!")
        if v_bal < amount:
            return await message.answer(f"❌ У {victim.first_name} маловато денег для такой дуэли.")

        cid = message.chat.id
        if cid not in pending_duels:
            pending_duels[cid] = {}
            
        pending_duels[cid][victim.id] = {
            "challenger_id": challenger.id,
            "challenger_name": challenger.first_name,
            "amount": amount
        }

        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🤝 Принять дуэль")]
        ], resize_keyboard=True, one_time_keyboard=True)

        await message.answer(
            f"🔫 <b>{challenger.first_name}</b> вызывает на дуэль <b>{victim.first_name}</b>!\n"
            f"💰 Ставка: <b>{fmt(amount)}</b> Угадаек.\n\n"
            f"<i>{victim.first_name}, ты принимаешь вызов?</i>",
            reply_markup=kb, parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка дуэли: {e}")

@router.message(F.text == "🤝 Принять дуэль")
async def accept_duel(message: Message):
    if message.chat.type == "private": return
    
    cid = message.chat.id
    vid = message.from_user.id 
    
    if cid not in pending_duels or vid not in pending_duels[cid]:
        return 
        
    duel = pending_duels[cid].pop(vid) 
    amount = duel["amount"]
    cid_challenger = duel["challenger_id"]
    c_name = duel["challenger_name"]
    v_name = message.from_user.first_name
    
    res_c = await get_user(cid_challenger, c_name)
    c_bal = res_c[0]
    
    res_v = await get_user(vid, v_name)
    v_bal = res_v[0]
    
    if c_bal < amount or v_bal < amount:
        return await message.answer("❌ Дуэль сорвалась: у кого-то закончились деньги!", reply_markup=get_main_kb(message.chat.type))
        
    await update_balance(cid_challenger, -amount)
    await update_balance(vid, -amount)
    
    winner_is_challenger = random.choice([True, False])
    total_win = amount * 2
    
    if winner_is_challenger:
        await update_balance(cid_challenger, total_win)
        winner_name, loser_name = c_name, v_name
    else:
        await update_balance(vid, total_win)
        winner_name, loser_name = v_name, c_name

    await message.answer(
        f"💥 ПАХ!\n\n🏆 <b>{winner_name}</b> оказался быстрее и застрелил <b>{loser_name}</b>!\n"
        f"💰 Весь банк в размере <b>{fmt(total_win)}</b> Угадаек уходит победителю!",
        parse_mode="HTML", reply_markup=get_main_kb(message.chat.type)
    )

