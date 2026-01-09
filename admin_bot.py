import sqlite3, datetime
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import SUPER_ADMIN_ID
import admin_keyboards as kb

admin_dp = Dispatcher()

admin_db = sqlite3.connect("admin.db", check_same_thread=False)
admin_cur = admin_db.cursor()

shop_db = sqlite3.connect("shop.db", check_same_thread=False)
shop_cur = shop_db.cursor()

event_db = sqlite3.connect("events.db", check_same_thread=False)
event_cur = event_db.cursor()

def is_admin(uid):
    if uid == SUPER_ADMIN_ID:
        return True
    admin_cur.execute("SELECT 1 FROM admins WHERE telegram_id=?", (uid,))
    return admin_cur.fetchone() is not None

@admin_dp.message(Command("start"))
async def start(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 Админ панель", reply_markup=kb.admin_menu())

@admin_dp.message(F.text=="➕ Добавить админа")
async def add_admin(m: Message):
    await m.answer("Введите ID:")

@admin_dp.message(F.text=="👥 Список админов")
async def list_admin(m: Message):
    admin_cur.execute("SELECT telegram_id FROM admins")
    rows=admin_cur.fetchall()
    text="👥 Админы:\n"
    for r in rows: text+=str(r[0])+"\n"
    await m.answer(text)

@admin_dp.message(F.text=="🎉 Создать ивент")
async def ev(m: Message):
    await m.answer("Формат: Название | % | 10.01.2026 00:00")

@admin_dp.message(F.text=="📋 Список ивентов")
async def evlist(m: Message):
    event_cur.execute("SELECT name, discount, until FROM events")
    rows=event_cur.fetchall()
    text="🎉 Ивенты:\n"
    for r in rows: text+=f"{r[0]} — {r[1]}% до {r[2]}\n"
    await m.answer(text)

@admin_dp.message(F.text=="📦 Заказы")
async def orders(m: Message):
    shop_cur.execute("SELECT id, telegram_id, uc, final_price, status FROM orders ORDER BY id DESC LIMIT 5")
    rows=shop_cur.fetchall()
    for r in rows:
        await m.answer(
            f"#{r[0]}\n👤 {r[1]}\n💎 {r[2]} UC\n💰 {r[3]} ₽\n📦 {r[4]}",
            reply_markup=kb.order_btn(r[0])
        )

@admin_dp.callback_query(F.data.startswith("done:"))
async def done(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    oid=int(c.data.split(":")[1])
    shop_cur.execute("UPDATE orders SET status='completed' WHERE id=?", (oid,))
    shop_db.commit()
    await c.answer("Готово")

@admin_dp.message(F.text=="📢 Рассылка")
async def bc(m: Message):
    await m.answer("Отправьте сообщение для рассылки:")

