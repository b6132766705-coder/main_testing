import aiosqlite
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import DB_PATH
from utils.formatters import fmt
from keyboards.reply import get_main_kb

router = Router()

# Состояния для создания клана
class ClanStates(StatesGroup):
    waiting_for_name = State()

@router.message(F.text.lower() == "клан")
@router.message(F.text == "🛡 Клан")
async def clan_menu(message: Message):
    uid = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT clan_id FROM users WHERE id = ?", (uid,)) as cur:
            row = await cur.fetchone()
            clan_id = row[0] if row else None

        if not clan_id:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✨ Создать клан (20к)", callback_data="clan_create_flow")],
                [InlineKeyboardButton(text="🏆 Топ кланов", callback_data="clan_top")]
            ])
            return await message.answer("🛡 <b>Кланы</b>\n\nВы пока не состоите в клане.", reply_markup=kb, parse_mode="HTML")

        query = """
            SELECT clans.name, clans.owner_id, clans.balance, users.name 
            FROM clans 
            JOIN users ON clans.owner_id = users.id 
            WHERE clans.id = ?
        """
        async with db.execute(query, (clan_id,)) as cur:
            c_name, c_owner_id, c_bal, owner_name = await cur.fetchone()

        async with db.execute("SELECT COUNT(id) FROM users WHERE clan_id = ?", (clan_id,)) as cur:
            members_count = (await cur.fetchone())[0]

    buttons = [
        [InlineKeyboardButton(text="💰 Пополнить казну", callback_data="clan_deposit")],
        [InlineKeyboardButton(text="👥 Список участников", callback_data="clan_members")],
        [InlineKeyboardButton(text="🏆 Топ кланов", callback_data="clan_top")]
    ]
    if uid == c_owner_id:
        buttons.append([InlineKeyboardButton(text="🚪 Покинуть клан (Лидер)", callback_data="clan_leave_confirm")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    role = "👑 Лидер" if uid == c_owner_id else "👤 Участник"
    
    text = (f"🛡 <b>Клан: {c_name}</b>\n👑 <b>Лидер:</b> {owner_name}\n"
            f"💰 <b>Казна:</b> {fmt(c_bal)} Угадаек\n👥 <b>Членов:</b> {members_count}/10\n\n"
            f"<b>Твоя роль:</b> {role}")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "clan_create_flow")
async def create_flow(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🛡 Введи название для клана (до 20 символов):")
    await state.set_state(ClanStates.waiting_for_name)
    await callback.answer()

@router.message(ClanStates.waiting_for_name)
async def create_clan_finish(message: Message, state: FSMContext):
    clan_name = message.text.strip()
    if len(clan_name) > 20:
        return await message.answer("❌ Слишком длинное название!")
        
    uid = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, clan_id FROM users WHERE id = ?", (uid,)) as cur:
            bal, c_id = await cur.fetchone()
        if c_id: return await message.answer("❌ Ты уже в клане!")
        if bal < 20000: return await message.answer("❌ Нужно 20 000 Угадаек!")
        
        try:
            await db.execute("UPDATE users SET balance = balance - 20000 WHERE id = ?", (uid,))
            cur = await db.execute("INSERT INTO clans (name, owner_id) VALUES (?, ?)", (clan_name, uid))
            await db.execute("UPDATE users SET clan_id = ? WHERE id = ?", (cur.lastrowid, uid))
            await db.commit()
        except:
            return await message.answer("❌ Название занято!")
            
    await state.clear()
    await message.answer(f"🎉 Клан <b>{clan_name}</b> создан!", reply_markup=get_main_kb(message.chat.type), parse_mode="HTML")

# --- КАЗНА ---
@router.message(F.text.lower().regexp(r"^(в|во)\s+(казну)\s+(\d+)"))
async def donate_to_clan(message: Message):
    match = re.search(r"(\d+)", message.text)
    amount = int(match.group(1))
    uid = message.from_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, clan_id FROM users WHERE id = ?", (uid,)) as cur:
            bal, cid = await cur.fetchone()
        if not cid or bal < amount: return await message.answer("❌ Ошибка доната!")
        
        await db.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, uid))
        await db.execute("UPDATE clans SET balance = balance + ? WHERE id = ?", (amount, cid))
        await db.commit()
    await message.answer(f"✅ Внесено {fmt(amount)} в казну!")
