import sqlite3, asyncio
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

admin_state = {}

def is_admin(uid):
    if uid == SUPER_ADMIN_ID:
        return True
    cur.execute("SELECT 1 FROM admins WHERE telegram_id=?", (uid,))
    return cur.fetchone() is not None

# ---------- USER ----------

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 <b>Магазин UC PUBG Mobile</b>\nВыберите действие:", reply_markup=kb.main_menu())

@dp.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    await m.answer("💎 Выберите пакет UC:", reply_markup=kb.buy_uc)

@dp.callback_query(F.data.startswith("buy:"))
async def buy_pack(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    uc=int(uc); price=int(price)

    cur.execute("INSERT INTO orders (telegram_id, uc, price, status) VALUES (?,?,?,?)",
                (c.from_user.id, uc, price, "waiting"))
    db.commit()

    oid = cur.lastrowid

    await c.message.answer(
        f"🧾 <b>Заказ #{oid}</b>\n💎 {uc} UC\n💰 {price} ₽\n\n🔗 <a href='{PAY_URL}'>Перейти к оплате</a>",
        reply_markup=kb.paid_btn
    )
    await c.answer()

@dp.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ Оплата отмечена. Ожидайте подтверждения администратора.")
    await c.answer()

@dp.message(F.text=="📦 Мои заказы")
async def my_orders(m: Message):
    cur.execute("SELECT id, uc, price, status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows=cur.fetchall()
    if not rows:
        await m.answer("📭 У вас пока нет заказов.")
        return
    text="📦 <b>Ваши заказы:</b>\n"
    for r in rows:
        st="⏳ В ожидании" if r[3]=="waiting" else "✅ Выполнен"
        text+=f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {st}\n"
    await m.answer(text)

# ---------- ADMIN PANEL ----------

@dp.message(Command("admin"))
async def admin_panel(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 <b>Админ панель</b>", reply_markup=kb.admin_menu())

@dp.message(F.text=="🚪 Выйти")
async def exit_admin(m: Message):
    await m.answer("Вы вышли из админ панели.", reply_markup=kb.main_menu())

@dp.message(F.text=="➕ Добавить админа")
async def add_admin(m: Message):
    admin_state[m.from_user.id]="add_admin"
    await m.answer("Введите Telegram ID нового админа:")

@dp.message(F.text=="👥 Список админов")
async def list_admins(m: Message):
    cur.execute("SELECT telegram_id FROM admins")
    rows=cur.fetchall()
    text="👥 Админы:\n"
    for r in rows:
        text+=str(r[0])+"\n"
    await m.answer(text)

@dp.message(F.text=="📦 Заказы")
async def admin_orders(m: Message):
    cur.execute("SELECT id,telegram_id,uc,price,status FROM orders ORDER BY id DESC LIMIT 10")
    rows=cur.fetchall()
    for r in rows:
        await m.answer(
            f"🧾 Заказ #{r[0]}\n👤 {r[1]}\n💎 {r[2]} UC\n💰 {r[3]} ₽\n📦 {r[4]}",
            reply_markup=kb.order_btn(r[0])
        )

@dp.callback_query(F.data.startswith("confirm:"))
async def confirm(c: CallbackQuery):
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    db.commit()

    cur.execute("SELECT telegram_id FROM orders WHERE id=?", (oid,))
    uid=cur.fetchone()[0]

    await bot.send_message(uid, "🎉 <b>Ваш заказ выполнен!</b> UC начислены.")
    await c.answer("Готово")

@dp.message(F.text=="📢 Рассылка")
async def broadcast(m: Message):
    admin_state[m.from_user.id]="broadcast"
    await m.answer("Введите текст для рассылки:")

@dp.message()
async def admin_inputs(m: Message):
    state=admin_state.get(m.from_user.id)

    if state=="add_admin":
        try:
            uid=int(m.text)
            cur.execute("INSERT OR IGNORE INTO admins VALUES (?)",(uid,))
            db.commit()
            await m.answer("✅ Админ добавлен")
        except:
            await m.answer("❌ Неверный ID")
        admin_state.pop(m.from_user.id)

    elif state=="broadcast":
        cur.execute("SELECT DISTINCT telegram_id FROM orders")
        for u in cur.fetchall():
            try: await bot.send_message(u[0], m.text)
            except: pass
        await m.answer("✅ Рассылка завершена")
        admin_state.pop(m.from_user.id)

# ---------- RUN ----------

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
