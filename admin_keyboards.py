from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Добавить админа"), KeyboardButton(text="👥 Список админов")],
        [KeyboardButton(text="🎉 Создать ивент"), KeyboardButton(text="📋 Список ивентов")],
        [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="📢 Рассылка")],
    ], resize_keyboard=True)

def order_btn(oid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"done:{oid}")]
    ])
