
import asyncio, sqlite3, datetime
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

admin_state = {}

def is_admin(uid):
    return uid == SUPER_ADMIN_ID

def event_discount():
    cur.execute("SELECT discount FROM events WHERE datetime(until)>=datetime('now') ORDER BY id DESC LIMIT 1")
    r = cur.fetchone()
    return r[0] if r else 0

# ========== USER ==========

@user_router.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 Магазин UC PUBG Mobile", reply_markup=kb.main_menu())

@user_router.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    await m.answer("Выберите пакет:", reply_markup=kb.buy_kb)

@user_router.callback_query(F.data.startswith("buy:"))
async def buy_pack(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    price=int(price)
    disc=event_discount()
    final=int(price*(100-disc)/100)

    cur.execute("INSERT INTO orders(telegram_id,uc,price,final_price,status) VALUES(?,?,?,?,?)",
                (c.from_user.id,int(uc),price,final,"waiting"))
    db.commit()
    oid=cur.lastrowid

    await c.message.answer(
        f"🧾 Заказ #{oid}\n💎 {uc} UC\n💰 {final} ₽\n\n{PAY_URL}",
        reply_markup=kb.paid_btn
    )
    await c.answer()

@user_router.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ Ожидайте подтверждения администратора")
    await c.answer()

@user_router.message(F.text=="📦 Мои заказы")
async def my_orders(m: Message):
    cur.execute("SELECT id,uc,final_price,status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows=cur.fetchall()
    if not rows:
        await m.answer("Заказов нет")
        return
    text="📦 Ваши заказы:\n"
    for r in rows:
        text+=f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {r[3]}\n"
    await m.answer(text)

# ========== ADMIN ==========

@admin_router.message(Command("admin"))
async def admin_panel(m: Message):
    if not is_admin(m.from_user.id):
        return
    await m.answer("👑 Админ панель", reply_markup=kb.admin_menu())

@admin_router.message(F.text=="🚪 Выйти")
async def exit_admin(m: Message):
    if not is_admin(m.from_user.id): return
    await m.answer("Вы вышли", reply_markup=kb.main_menu())

@admin_router.message(F.text=="🎉 Создать ивент")
async def create_event(m: Message):
    if not is_admin(m.from_user.id): return
    admin_state[m.from_user.id]="event"
    await m.answer("Формат: Название | % | 10.01.2026 00:00")

@admin_router.message(F.text=="📦 Заказы")
async def orders(m: Message):
    if not is_admin(m.from_user.id): return
    cur.execute("SELECT id,telegram_id,uc,final_price,status FROM orders ORDER BY id DESC LIMIT 10")
    for r in cur.fetchall():
        await m.answer(f"#{r[0]}\n{r[1]}\n{r[2]} UC\n{r[3]} ₽\n{r[4]}", reply_markup=kb.order_btn(r[0]))

@admin_router.callback_query(F.data.startswith("confirm:"))
async def confirm(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    db.commit()
    await c.answer("Подтверждено")

@admin_router.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    oid=int(c.data.split(":")[1])
    cur.execute("UPDATE orders SET status='canceled' WHERE id=?", (oid,))
    db.commit()
    await c.answer("Отменено")

@admin_router.message()
async def admin_input(m: Message):
    if not is_admin(m.from_user.id): return
    if admin_state.get(m.from_user.id)=="event":
        n,d,u=[x.strip() for x in m.text.split("|")]
        cur.execute("INSERT INTO events(name,discount,until) VALUES(?,?,?)",(n,int(d),u))
        db.commit()
        await m.answer("Ивент создан")
        admin_state.pop(m.from_user.id)

dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
