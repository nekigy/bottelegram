import asyncio, sqlite3, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import *
from database import init_dbs

init_dbs()

# --- DB ---
shop_db = sqlite3.connect("shop.db", check_same_thread=False)
shop_cur = shop_db.cursor()

event_db = sqlite3.connect("events.db", check_same_thread=False)
event_cur = event_db.cursor()

# --- BOTS ---
shop_bot = Bot(SHOP_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML")) # pyright: ignore[reportUndefinedVariable]
admin_bot = Bot(ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

shop_dp = Dispatcher()
admin_dp = Dispatcher()

# ================= SHOP BOT =================

@shop_dp.message(Command("start"))
async def shop_start(m: Message):
    await m.answer("🎮 Магазин UC PUBG Mobile\nНажми: Купить")

@shop_dp.message(F.text.lower() == "купить")
async def shop_buy(m: Message):
    price = 263
    uc = 180

    event_cur.execute("SELECT name, discount, until FROM events ORDER BY id DESC LIMIT 1")
    row = event_cur.fetchone()

    final_price = price
    event_text = ""

    if row:
        name, discount, until = row
        until_dt = datetime.datetime.strptime(until, "%d.%m.%Y %H:%M")
        if datetime.datetime.now() < until_dt:
            final_price = int(price * (100 - discount) / 100)
            event_text = f"🎉 Акция: {name} (-{discount}%)\n"

    shop_cur.execute(
        "INSERT INTO orders (telegram_id, uc, price, final_price, status) VALUES (?,?,?,?,?)",
        (m.from_user.id, uc, price, final_price, "waiting")
    )
    shop_db.commit()

    await m.answer(
        f"{event_text}"
        f"💎 UC: {uc}\n"
        f"💰 Цена: {final_price} ₽"
    )

# ================= ADMIN BOT =================

def is_super(uid):
    return uid == SUPER_ADMIN_ID

@admin_dp.message(Command("start"))
async def admin_start(m: Message):
    if not is_super(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 Админ-панель\n/event создать ивент")

@admin_dp.message(F.text.startswith("/event "))
async def admin_event(m: Message):
    if not is_super(m.from_user.id):
        return

    try:
        data = m.text.replace("/event ","").split("|")
        name = data[0].strip()
        discount = int(data[1].strip())
        until = data[2].strip()

        event_cur.execute(
            "INSERT INTO events (name, discount, until) VALUES (?,?,?)",
            (name, discount, until)
        )
        event_db.commit()

        await m.answer("🎉 Ивент создан и применён к магазину")
    except:
        await m.answer("Формат: /event Название | % | 10.01.2026 00:00")

# ================= RUN BOTH =================

async def main():
    print("SHOP BOT + ADMIN BOT STARTED")
    await asyncio.gather(
        shop_dp.start_polling(shop_bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
