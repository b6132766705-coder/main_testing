from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_kb(chat_type: str):
    if chat_type == 'private':
        buttons = [
            [KeyboardButton(text="🎮 Играть"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🏆 Рейтинг"), KeyboardButton(text="🛡 Клан")],
            [KeyboardButton(text="🎁 Бонус"), KeyboardButton(text="🎒 Инвентарь")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="🎮 Играть"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📊 Ставки"), KeyboardButton(text="🚫 Отмена")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
