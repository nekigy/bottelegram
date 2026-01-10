
import asyncio, sqlite3
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import *
from database import init_db
import keyboards as kb

init_db()

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_router = Router()
admin_router = Router()

db = sqlite3.connect("shop.db", check_same_thread=False)
cur = db.cursor()

state = {}

def is_admin(uid):
    if uid == SUPER_ADMIN_ID:
        return True
    cur.execute("SELECT 1 FROM admins WHERE telegram_id=?", (uid,))
    return cur.fetchone() is not None

# ===== USER =====

@user_router.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 <b>Магазин UC PUBG Mobile</b>", reply_markup=kb.main_menu())

@user_router.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    await m.answer("💎 Выберите пакет UC:", reply_markup=kb.buy_kb)

@user_router.callback_query(F.data.startswith("buy:"))
async def buy_pack(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    cur.execute("INSERT INTO orders(telegram_id,uc,price,status) VALUES(?,?,?,?)",
                (c.from_user.id,int(uc),int(price),"waiting"))
    db.commit()
    oid = cur.lastrowid

    await c.message.answer(
        f"🧾 Заказ #{oid}\n💎 {uc} UC\n💰 {price} ₽\n\n<a href='{PAY_URL}'>Перейти к оплате</a>",
        reply_markup=kb.paid_btn
    )
    await c.answer()

@user_router.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ Оплата отмечена. Ожидайте подтверждения.")
    await c.answer()

@user_router.message(F.text=="📦 Мои заказы")
async def history(m: Message):
    cur.execute("SELECT id,uc,price,status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows=cur.fetchall()
    if not rows:
        await m.answer("📭 Заказов пока нет")
        return
    text="📦 <b>Ваши заказы:</b>\n"
    for r in rows:
        st="⏳" if r[3]=="waiting" else "✅" if r[3]=="completed" else "❌"
        text+=f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {st}\n"
    await m.answer(text)

# ===== ADMIN =====

@admin_router.message(Command("admin"))
async def admin_panel(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 Админ панель", reply_markup=kb.admin_menu())

@admin_router.message(F.text=="🚪 Выйти")
async def exit_admin(m: Message):
    await m.answer("Вы вышли", reply_markup=kb.main_menu())

@admin_router.message(F.text=="➕ Добавить админа")
async def add_admin(m: Message):
    state[m.from_user.id]="add_admin"
    await m.answer("Введите Telegram ID:")

@admin_router.message(F.text=="👥 Админы")
async def list_admins(m: Message):
    cur.execute("SELECT telegram_id FROM admins")
    rows=cur.fetchall()
    text="👥 Админы:\n"
    for r in rows: text+=str(r[0])+"\n"
    await m.answer(text)

@admin_router.message(F.text=="📢 Сообщение всем")
async def bc(m: Message):
    state[m.from_user.id]="bc"
    await m.answer("Введите сообщение:")

@admin_router.message(F.text=="📦 Заказы")
async def orders(m: Message):
    cur.execute("SELECT id,telegram_id,uc,price,status FROM orders ORDER BY id DESC LIMIT 10")
    for r in cur.fetchall():
        await m.answer(
            f"#{r[0]}\n👤 {r[1]}\n💎 {r[2]} UC\n💰 {r[3]} ₽\n📦 {r[4]}",
            reply_markup=kb.order_btn(r[0])
        )

@admin_router.callback_query(F.data.startswith("confirm:"))
async def confirm(c: CallbackQuery):
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    db.commit()
    cur.execute("SELECT telegram_id FROM orders WHERE id=?", (oid,))
    uid=cur.fetchone()[0]
    await bot.send_message(uid,"🎉 Ваш заказ выполнен!")
    await c.answer("Готово")

@admin_router.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery):
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='canceled' WHERE id=?", (oid,))
    db.commit()
    await c.answer("Отменено")

@admin_router.message()
async def admin_inputs(m: Message):
    s=state.get(m.from_user.id)
    if not s: return

    if s=="add_admin":
        cur.execute("INSERT OR IGNORE INTO admins VALUES (?)",(int(m.text),))
        db.commit()
        await m.answer("Админ добавлен")

    elif s=="bc":
        cur.execute("SELECT DISTINCT telegram_id FROM orders")
        for u in cur.fetchall():
            try: await bot.send_message(u[0],m.text)
            except: pass
        await m.answer("Сообщение отправлено")

    state.pop(m.from_user.id,None)

# ===== RUN =====

dp.include_router(admin_router)
dp.include_router(user_router)

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
