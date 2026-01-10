
from aiogram.types import *

def main_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="💎 Купить UC")],
        [KeyboardButton(text="📦 Мои заказы")]
    ])

buy_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="28 UC — 64 ₽", callback_data="buy:28:64")],
    [InlineKeyboardButton(text="60 UC — 89 ₽", callback_data="buy:60:89")],
    [InlineKeyboardButton(text="180 UC — 263 ₽", callback_data="buy:180:263")],
    [InlineKeyboardButton(text="355 UC — 515 ₽", callback_data="buy:355:515")]
])

paid_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Я оплатил", callback_data="paid")]
])

def admin_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="➕ Добавить админа"), KeyboardButton(text="👥 Админы")],
        [KeyboardButton(text="📢 Сообщение всем")],
        [KeyboardButton(text="🚪 Выйти")]
    ])

def order_btn(oid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{oid}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel:{oid}")]
    ])
