
# --- АДМИН-ЧИТ: ОБНУЛЕНИЕ ТАЙМЕРОВ ---
@dp.message(lambda m: m.text and m.text.lower().startswith("обнулить"))
async def admin_reset(message: Message):
    logging.info(f"Команда 'обнулить' от ID: {message.from_user.id}")

    if message.from_user.id != ADMIN_ID:
        return 

    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""UPDATE users SET 
                           last_steal = NULL, 
                           shame_mark = NULL, 
                           last_bonus = NULL 
                           WHERE id = ?""", (target_user.id,))
            await db.commit()
        
        await message.answer(f"🪄 **Магия!** Таймеры для {target_user.first_name} сброшены.")
    except Exception as e:
        logging.error(f"Ошибка при обнулении: {e}")
        await message.answer("❌ Произошла ошибка в базе данных.")

# --- АДМИН-КОМАНДЫ (ИСПРАВЛЕННЫЕ) ---

@dp.message(F.reply_to_message, F.text.lower().startswith("+предмет"), lambda m: m.from_user.id == ADMIN_ID)
async def admin_give_item(message: Message):
    parts = message.text.split()
    try:
        item_name = parts[1]
        amount = int(parts[2]) if len(parts) > 2 else 1
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO inventory (user_id, item_name, amount) 
                VALUES (?, ?, ?) 
                ON CONFLICT(user_id, item_name) DO UPDATE SET amount = amount + ?
            """, (target_id, item_name, amount, amount))
            await db.commit()
        
        await message.answer(f"🪄 Админ выдал <b>{target_name}</b> предмет: <b>{item_name}</b> ({amount} шт.)", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Ошибка. Пример: <code>+предмет Клевер 5</code>")


@dp.message(F.reply_to_message, F.text.lower().startswith("-предмет"), lambda m: m.from_user.id == ADMIN_ID)
async def admin_take_item(message: Message):
    parts = message.text.split()
    try:
        item_name = parts[1]
        amount = int(parts[2]) if len(parts) > 2 else 1
        target_id = message.reply_to_message.from_user.id
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE inventory SET amount = MAX(0, amount - ?) 
                WHERE user_id = ? AND item_name = ?
            """, (amount, target_id, item_name))
            await db.commit()
        
        await message.answer(f"🧹 Админ изъял у игрока предмет: <b>{item_name}</b> ({amount} шт.)", parse_mode="HTML")
    except:
        await message.answer("❌ Ошибка. Пример: <code>-предмет Шар 1</code>")



# Стало:
@dp.message(F.reply_to_message, lambda m: m.from_user.id == ADMIN_ID)
async def admin_balance_change(message: Message):
    if message.text.startswith(("+", "-")) and "предмет" not in message.text.lower():
        try:
            val = int(message.text.replace(" ", ""))
            await update_balance(message.reply_to_message.from_user.id, val)
            await message.answer(f"👑 Изменено на {fmt(val)}")
        except: pass
