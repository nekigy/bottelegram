from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💎 Купить UC")],
        [KeyboardButton(text="📦 Мои заказы")],
    ], resize_keyboard=True)

buy_uc = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="28 UC — 64 ₽", callback_data="buy:28:64")],
    [InlineKeyboardButton(text="60 UC — 89 ₽", callback_data="buy:60:89")],
    [InlineKeyboardButton(text="180 UC — 263 ₽", callback_data="buy:180:263")],
    [InlineKeyboardButton(text="355 UC — 515 ₽", callback_data="buy:355:515")],
])

promo_ask = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎁 Есть промо", callback_data="promo_yes")],
    [InlineKeyboardButton(text="❌ Нету", callback_data="promo_no")],
])

paid_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Я оплатил", callback_data="paid")]
])
