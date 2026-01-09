import sqlite3, asyncio, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import *
from database import init_db
import keyboards as kb

init_db()

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

db = sqlite3.connect("shop.db", check_same_thread=False)
cur = db.cursor()

state = {}
pending = {}

def is_admin(uid):
    if uid == SUPER_ADMIN_ID:
        return True
    cur.execute("SELECT 1 FROM admins WHERE telegram_id=?", (uid,))
    return cur.fetchone() is not None

# -------- USER --------

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 <b>Магазин UC PUBG Mobile</b>", reply_markup=kb.main_menu())

@dp.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    await m.answer("💎 Выберите пакет UC:", reply_markup=kb.buy_uc)

@dp.callback_query(F.data.startswith("buy:"))
async def choose(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    pending[c.from_user.id] = {"uc":int(uc),"price":int(price)}
    await c.message.answer("🎁 Введите промокод или напишите НЕТ:")
    await c.answer()

@dp.message()
async def promo_input(m: Message):
    if m.from_user.id not in pending:
        return

    text = m.text.strip().upper()
    data = pending[m.from_user.id]

    final_price = data["price"]
    promo = None

    if text != "НЕТ":
        cur.execute("SELECT discount, expires_at FROM promos WHERE code=?", (text,))
        row = cur.fetchone()
        if not row:
            await m.answer("❌ Промокод не найден")
            return
        disc, exp = row
        if datetime.datetime.now() > datetime.datetime.strptime(exp,"%d.%m.%Y %H:%M"):
            await m.answer("⌛ Промокод истёк")
            return
        final_price = int(data["price"]*(100-disc)/100)
        promo = text

    cur.execute("INSERT INTO orders (telegram_id, uc, price, final_price, promo, status) VALUES (?,?,?,?,?,?)",
                (m.from_user.id,data["uc"],data["price"],final_price,promo,"waiting"))
    db.commit()
    oid = cur.lastrowid
    pending.pop(m.from_user.id)

    await m.answer(
        f"🧾 Заказ #{oid}\n💎 {data['uc']} UC\n💰 {final_price} ₽\n\n🔗 {PAY_URL}",
        reply_markup=kb.paid_btn
    )

@dp.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ Оплата отмечена. Ожидайте подтверждения.")
    await c.answer()

@dp.message(F.text=="📦 Мои заказы")
async def history(m: Message):
    cur.execute("SELECT id,uc,final_price,status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows=cur.fetchall()
    if not rows:
        await m.answer("Заказов нет")
        return
    text="📦 Ваши заказы:\n"
    for r in rows:
        st="⏳" if r[3]=="waiting" else "❌" if r[3]=="canceled" else "✅"
        text+=f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {st}\n"
    await m.answer(text)

# -------- ADMIN --------

@dp.message(Command("admin"))
async def admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 Админ панель", reply_markup=kb.admin_menu())

@dp.message(F.text=="🚪 Выйти")
async def exit_admin(m: Message):
    await m.answer("Вы вышли", reply_markup=kb.main_menu())

@dp.message(F.text=="➕ Админ")
async def add_admin(m: Message):
    state[m.from_user.id]="add_admin"
    await m.answer("Введите ID:")

@dp.message(F.text=="👥 Админы")
async def list_admins(m: Message):
    cur.execute("SELECT telegram_id FROM admins")
    rows=cur.fetchall()
    text="👥 Админы:\n"
    for r in rows: text+=str(r[0])+"\n"
    await m.answer(text)

@dp.message(F.text=="🎁 Промокод")
async def promo_create(m: Message):
    state[m.from_user.id]="promo"
    await m.answer("Формат: CODE | % | 10.01.2026 00:00")

@dp.message(F.text=="🎉 Ивент")
async def event_create(m: Message):
    state[m.from_user.id]="event"
    await m.answer("Формат: Название | % | 10.01.2026 00:00")

@dp.message(F.text=="📢 Сообщение всем")
async def bc(m: Message):
    state[m.from_user.id]="bc"
    await m.answer("Введите сообщение:")

@dp.message(F.text=="📦 Заказы")
async def orders(m: Message):
    cur.execute("SELECT id,telegram_id,uc,final_price,status FROM orders ORDER BY id DESC LIMIT 10")
    for r in cur.fetchall():
        await m.answer(
            f"#{r[0]}\n👤 {r[1]}\n💎 {r[2]} UC\n💰 {r[3]} ₽\n📦 {r[4]}",
            reply_markup=kb.order_btn(r[0])
        )

@dp.callback_query(F.data.startswith("confirm:"))
async def confirm(c: CallbackQuery):
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    db.commit()
    cur.execute("SELECT telegram_id FROM orders WHERE id=?", (oid,))
    uid=cur.fetchone()[0]
    await bot.send_message(uid,"🎉 Ваш заказ выполнен!")
    await c.answer("Подтверждено")

@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery):
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='canceled' WHERE id=?", (oid,))
    db.commit()
    await c.answer("Отменено")

@dp.message()
async def admin_inputs(m: Message):
    s=state.get(m.from_user.id)
    if s=="add_admin":
        cur.execute("INSERT OR IGNORE INTO admins VALUES (?)",(int(m.text),))
        db.commit()
        await m.answer("Админ добавлен")
    elif s=="promo":
        c,d,u=[x.strip() for x in m.text.split("|")]
        cur.execute("INSERT INTO promos VALUES (?,?,?)",(c.upper(),int(d),u))
        db.commit()
        await m.answer("Промокод создан")
    elif s=="event":
        n,d,u=[x.strip() for x in m.text.split("|")]
        cur.execute("INSERT INTO events (name,discount,until) VALUES (?,?,?)",(n,int(d),u))
        db.commit()
        await m.answer("Ивент создан")
    elif s=="bc":
        cur.execute("SELECT DISTINCT telegram_id FROM orders")
        for u in cur.fetchall():
            try: await bot.send_message(u[0],m.text)
            except: pass
        await m.answer("Сообщение отправлено")
    state.pop(m.from_user.id,None)

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
