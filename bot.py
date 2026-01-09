import asyncio, time, sqlite3, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import *
from database import init_orders_db, init_promo_db, init_usedpromo_db
import keyboards as kb

init_orders_db()
init_promo_db()
init_usedpromo_db()

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

orders_db = sqlite3.connect("shop.db", check_same_thread=False)
orders_cur = orders_db.cursor()

promo_db = sqlite3.connect("promocode.db", check_same_thread=False)
promo_cur = promo_db.cursor()

used_db = sqlite3.connect("usedpromo.db", check_same_thread=False)
used_cur = used_db.cursor()

pending_orders = {}
last_bot_msg = {}

async def safe_send(user_id, text, reply_markup=None):
    if user_id in last_bot_msg:
        try:
            await bot.delete_message(user_id, last_bot_msg[user_id])
        except:
            pass
    msg = await bot.send_message(user_id, text, reply_markup=reply_markup)
    last_bot_msg[user_id] = msg.message_id

async def cancel_expired_orders():
    while True:
        now = int(time.time())
        orders_cur.execute(
            "SELECT id, telegram_id FROM orders WHERE status='waiting_payment' AND ? - created_at > ?",
            (now, ORDER_LIFETIME)
        )
        for oid, uid in orders_cur.fetchall():
            orders_cur.execute("UPDATE orders SET status='expired' WHERE id=?", (oid,))
            orders_db.commit()
            await safe_send(uid, "⌛ Заказ отменён (время оплаты истекло)")
        await asyncio.sleep(60)

@dp.message(Command("start"))
async def start(m: Message):
    await safe_send(m.from_user.id, "🎮 <b>Магазин UC PUBG Mobile</b>", kb.main_menu())

@dp.message(F.text == "🆘 Поддержка")
async def support(m: Message):
    await safe_send(m.from_user.id, "🆘 Поддержка", kb.support_kb(SUPPORT_USERNAME, CHANNEL_USERNAME))

@dp.message(F.text == "💎 Купить UC")
async def buy(m: Message):
    pending_orders.pop(m.from_user.id, None)
    await safe_send(m.from_user.id, "💎 Выберите пакет UC:", kb.buy_uc)

@dp.callback_query(F.data.startswith("buy:"))
async def buy_package(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    pending_orders[c.from_user.id] = {"uc": int(uc), "price": int(price)}
    await safe_send(c.from_user.id, "🎁 У вас есть промокод?", kb.has_promo)
    await c.answer()

@dp.callback_query(F.data == "promo_no")
async def promo_no(c: CallbackQuery):
    data = pending_orders.get(c.from_user.id)
    if data:
        await create_order(c.from_user.id, data["uc"], data["price"])
    await c.answer()

@dp.callback_query(F.data == "promo_yes")
async def promo_yes(c: CallbackQuery):
    await safe_send(c.from_user.id, "✏️ Напишите ваш промокод:")
    await c.answer()

@dp.message()
async def promo_input(m: Message):
    if m.from_user.id not in pending_orders:
        return

    try:
        await m.delete()
    except:
        pass

    code = m.text.strip().upper()

    promo_cur.execute("SELECT discount, expires_at FROM promos WHERE code=?", (code,))
    row = promo_cur.fetchone()

    if not row:
        await safe_send(m.from_user.id, "❌ Промокод не найден")
        return

    discount, expires_at = row
    exp = datetime.datetime.strptime(expires_at, "%d.%m.%Y %H:%M")

    if datetime.datetime.now() > exp:
        await safe_send(m.from_user.id, "⌛ Срок действия промокода истёк")
        return

    used_cur.execute("SELECT 1 FROM used WHERE telegram_id=? AND code=?", (m.from_user.id, code))
    if used_cur.fetchone():
        await safe_send(m.from_user.id, "❌ Вы уже использовали этот промокод")
        return

    data = pending_orders[m.from_user.id]
    final_price = int(data["price"] * (100 - discount) / 100)

    used_cur.execute("INSERT INTO used VALUES (?,?)", (m.from_user.id, code))
    used_db.commit()

    await create_order(m.from_user.id, data["uc"], data["price"], code, final_price, discount)

async def create_order(user_id, uc, price, promo=None, final_price=None, discount=None):
    if final_price is None:
        final_price = price

    orders_cur.execute(
        "INSERT INTO orders (telegram_id, uc, price, final_price, promo_code, status, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (user_id, uc, price, final_price, promo, "waiting_payment", int(time.time()))
    )
    orders_db.commit()

    pending_orders.pop(user_id, None)

    await safe_send(
        user_id,
        f"🧾 Заказ создан\n"
        f"💎 UC: {uc}\n"
        f"💰 Цена: {final_price} ₽\n"
        f"{f'🎁 Промо: {promo} (-{discount}%)' if promo else ''}\n"
        f"🔗 <a href='{PAY_URL}'>Перейти к оплате</a>",
        kb.paid_btn
    )

@dp.callback_query(F.data == "paid")
async def paid(c: CallbackQuery):
    orders_cur.execute(
        "UPDATE orders SET status='waiting_confirm' WHERE telegram_id=? AND status='waiting_payment'",
        (c.from_user.id,)
    )
    orders_db.commit()

    orders_cur.execute(
        "SELECT id, uc, final_price, promo_code, created_at FROM orders "
        "WHERE telegram_id=? AND status='waiting_confirm'",
        (c.from_user.id,)
    )
    oid, uc, fprice, promo, ts = orders_cur.fetchone()
    dt = datetime.datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Заказ #{oid}\n"
        f"👤 {c.from_user.id}\n"
        f"💎 {uc} UC\n"
        f"💰 {fprice} ₽\n"
        f"{f'🎁 Промо: {promo}' if promo else ''}\n"
        f"🕒 {dt}",
        reply_markup=kb.admin_done_btn(oid)
    )

    await safe_send(c.from_user.id, "⏳ Оплата отмечена. Ожидайте выполнения.")
    await c.answer()

@dp.callback_query(F.data.startswith("done:"))
async def admin_done(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("❌ Нет доступа", show_alert=True)
        return

    oid = int(c.data.split(":")[1])
    orders_cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    orders_db.commit()

    orders_cur.execute("SELECT telegram_id FROM orders WHERE id=?", (oid,))
    user_id = orders_cur.fetchone()[0]

    await safe_send(user_id, "✅ Заказ выполнен! UC начислены 🎉")
    await c.message.answer("✅ Готово")
    await c.answer()

async def main():
    asyncio.create_task(cancel_expired_orders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
