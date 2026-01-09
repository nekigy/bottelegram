import sqlite3
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import shop_keyboards as kb
from config import PAY_URL

shop_dp = Dispatcher()

db = sqlite3.connect("shop.db", check_same_thread=False)
cur = db.cursor()

@shop_dp.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "🎮 <b>Магазин UC PUBG Mobile</b>\n"
        "🔥 Быстро • Надёжно • Безопасно",
        reply_markup=kb.main_menu()
    )

@shop_dp.message(F.text == "💎 Купить UC")
async def buy(m: Message):
    await m.answer("💎 <b>Выберите пакет UC:</b>", reply_markup=kb.buy_uc)

@shop_dp.callback_query(F.data.startswith("buy:"))
async def buy_package(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    uc, price = int(uc), int(price)

    cur.execute(
        "INSERT INTO orders (telegram_id, uc, price, final_price, status) VALUES (?,?,?,?,?)",
        (c.from_user.id, uc, price, price, "waiting")
    )
    db.commit()

    order_id = cur.lastrowid

    await c.message.answer(
        f"🧾 <b>Заказ #{order_id}</b>\n"
        f"💎 UC: <b>{uc}</b>\n"
        f"💰 Цена: <b>{price} ₽</b>\n\n"
        f"🔗 <a href='{PAY_URL}'>Перейти к оплате</a>",
        reply_markup=kb.paid_btn
    )
    await c.answer()

@shop_dp.callback_query(F.data == "paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ <b>Оплата отмечена!</b> Ожидайте подтверждения администратора.")
    await c.answer()

@shop_dp.message(F.text == "📦 Мои заказы")
async def my_orders(m: Message):
    cur.execute("SELECT id, uc, final_price, status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        await m.answer("📭 У вас пока нет заказов.")
        return

    text = "📦 <b>Ваши заказы:</b>\n\n"
    for r in rows:
        status = "⏳ В ожидании" if r[3]=="waiting" else "✅ Выполнен"
        text += f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {status}\n"

    await m.answer(text)
