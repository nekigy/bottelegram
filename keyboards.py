from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Купить UC")],
            [KeyboardButton(text="🆘 Поддержка")]
        ],
        resize_keyboard=True
    )

buy_uc = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💠 28 UC — 64 ₽", callback_data="buy:28:64")],
    [InlineKeyboardButton(text="💠 60 UC — 89 ₽", callback_data="buy:60:89")],
    [InlineKeyboardButton(text="💠 180 UC — 263 ₽", callback_data="buy:180:263")],
    [InlineKeyboardButton(text="💠 355 UC — 515 ₽", callback_data="buy:355:515")]
])

has_promo = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎁 Есть промо", callback_data="promo_yes")],
    [InlineKeyboardButton(text="❌ Нету", callback_data="promo_no")]
])

paid_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Я оплатил", callback_data="paid")]
])

def admin_done_btn(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"done:{order_id}")]
    ])

def support_kb(support: str, channel: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в ЛС", url=f"https://t.me/{support}")],
        [InlineKeyboardButton(text="📣 Наш канал", url=f"https://t.me/{channel}")],
    ])
