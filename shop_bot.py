import time, sqlite3, datetime
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import shop_keyboards as kb
from config import PAY_URL

shop_dp = Dispatcher()

shop_db = sqlite3.connect("shop.db", check_same_thread=False)
shop_cur = shop_db.cursor()

promo_db = sqlite3.connect("promocode.db", check_same_thread=False)
promo_cur = promo_db.cursor()

used_db = sqlite3.connect("usedpromo.db", check_same_thread=False)
used_cur = used_db.cursor()

event_db = sqlite3.connect("events.db", check_same_thread=False)
event_cur = event_db.cursor()

pending = {}

@shop_dp.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 Магазин UC PUBG Mobile", reply_markup=kb.main_menu())

@shop_dp.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    pending.pop(m.from_user.id, None)
    await m.answer("Выберите пакет:", reply_markup=kb.buy_uc)

@shop_dp.callback_query(F.data.startswith("buy:"))
async def choose(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    pending[c.from_user.id] = {"uc":int(uc),"price":int(price)}
    await c.message.answer("🎁 У вас есть промокод?", reply_markup=kb.promo_ask)
    await c.answer()

@shop_dp.callback_query(F.data=="promo_no")
async def promo_no(c: CallbackQuery):
    data = pending[c.from_user.id]
    await create_order(c.from_user.id, data["uc"], data["price"])
    await c.answer()

@shop_dp.callback_query(F.data=="promo_yes")
async def promo_yes(c: CallbackQuery):
    await c.message.answer("✏️ Напишите промокод:")
    await c.answer()

@shop_dp.message()
async def promo_input(m: Message):
    if m.from_user.id not in pending:
        return

    code = m.text.strip().upper()

    promo_cur.execute("SELECT discount, expires_at FROM promos WHERE code=?", (code,))
    row = promo_cur.fetchone()

    if not row:
        await m.answer("❌ Промокод не найден")
        return

    discount, exp = row
    if datetime.datetime.now() > datetime.datetime.strptime(exp, "%d.%m.%Y %H:%M"):
        await m.answer("⌛ Промокод истёк")
        return

    used_cur.execute("SELECT 1 FROM used WHERE telegram_id=? AND code=?", (m.from_user.id, code))
    if used_cur.fetchone():
        await m.answer("❌ Вы уже использовали этот промокод")
        return

    used_cur.execute("INSERT INTO used VALUES (?,?)", (m.from_user.id, code))
    used_db.commit()

    data = pending[m.from_user.id]
    final_price = int(data["price"]*(100-discount)/100)

    await create_order(m.from_user.id, data["uc"], data["price"], code, final_price)

async def create_order(uid, uc, price, promo=None, final_price=None):
    if not final_price:
        final_price = price

    shop_cur.execute(
        "INSERT INTO orders (telegram_id, uc, price, final_price, promo_code, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (uid, uc, price, final_price, promo, "waiting", int(time.time()))
    )
    shop_db.commit()

    pending.pop(uid, None)

    await shop_dp.bot.send_message(
        uid,
        f"🧾 Заказ создан\n💎 {uc} UC\n💰 {final_price} ₽\n🔗 {PAY_URL}",
        reply_markup=kb.paid_btn
    )

@shop_dp.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    shop_cur.execute("UPDATE orders SET status='waiting_confirm' WHERE telegram_id=? AND status='waiting'", (c.from_user.id,))
    shop_db.commit()
    await c.message.answer("⏳ Ожидайте подтверждения")
    await c.answer()

@shop_dp.message(F.text=="📦 Мои заказы")
async def history(m: Message):
    shop_cur.execute("SELECT id, uc, final_price, status FROM orders WHERE telegram_id=? ORDER BY id DESC", (m.from_user.id,))
    rows = shop_cur.fetchall()
    if not rows:
        await m.answer("Заказов нет")
        return
    text="📦 Ваши заказы:\n"
    for o in rows:
        text+=f"#{o[0]} — {o[1]} UC — {o[2]} ₽ — {o[3]}\n"
    await m.answer(text)
