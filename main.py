
import asyncio, sqlite3, datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = "8587849255:AAHYtuno3ewMs27H0-BaT3e_c_An3j-xDKc"
SUPER_ADMIN_ID = 8382525189
PAY_URL = "https://pay.cloudtips.ru/p/9534f31b"

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_router = Router()
admin_router = Router()

db = sqlite3.connect("shop.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,
telegram_id INTEGER,
uc INTEGER,
price INTEGER,
final_price INTEGER,
promo TEXT,
status TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS admins(
telegram_id INTEGER PRIMARY KEY)""")

cur.execute("""CREATE TABLE IF NOT EXISTS promos(
code TEXT PRIMARY KEY,
discount INTEGER,
expires_at TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS events(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
discount INTEGER,
until TEXT)""")

db.commit()

admin_state={}
pending_order={}

# ---------- HELPERS ----------

def is_admin(uid):
    if uid==SUPER_ADMIN_ID:
        return True
    cur.execute("SELECT 1 FROM admins WHERE telegram_id=?", (uid,))
    return cur.fetchone() is not None

def get_event_discount():
    now=datetime.datetime.now()
    cur.execute("SELECT discount FROM events WHERE datetime(until)>=datetime('now') ORDER BY id DESC LIMIT 1")
    row=cur.fetchone()
    if row:
        return row[0]
    return 0

# ---------- KEYBOARDS ----------

def main_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="💎 Купить UC")],
        [KeyboardButton(text="📦 Мои заказы")]
    ])

buy_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="28 UC — 64 ₽", callback_data="buy:28:64")],
    [InlineKeyboardButton(text="60 UC — 89 ₽", callback_data="buy:60:89")],
    [InlineKeyboardButton(text="180 UC — 263 ₽", callback_data="buy:180:263")],
    [InlineKeyboardButton(text="355 UC — 515 ₽", callback_data="buy:355:515")]
])

paid_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Я оплатил", callback_data="paid")]
])

def admin_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="🏆 Топ покупателей")],
        [KeyboardButton(text="➕ Добавить админа"), KeyboardButton(text="👥 Админы")],
        [KeyboardButton(text="🎁 Промокод"), KeyboardButton(text="🎉 Ивент")],
        [KeyboardButton(text="📢 Сообщение всем")],
        [KeyboardButton(text="🚪 Выйти")]
    ])

def order_btn(oid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{oid}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel:{oid}")]
    ])

# ================= USER =================

@user_router.message(Command("start"))
async def start(m: Message):
    await m.answer("🎮 <b>Магазин UC PUBG Mobile</b>", reply_markup=main_menu())

@user_router.message(F.text=="💎 Купить UC")
async def buy(m: Message):
    await m.answer("💎 Выберите пакет UC:", reply_markup=buy_kb)

@user_router.callback_query(F.data.startswith("buy:"))
async def buy_pack(c: CallbackQuery):
    _, uc, price = c.data.split(":")
    pending_order[c.from_user.id]={"uc":int(uc),"price":int(price)}
    await c.message.answer("🎁 Введите промокод или напишите НЕТ:")
    await c.answer()

@user_router.message()
async def promo_input(m: Message):
    if m.from_user.id not in pending_order:
        return

    data=pending_order[m.from_user.id]
    promo=None
    final_price=data["price"]

    code=m.text.strip().upper()
    if code!="НЕТ":
        cur.execute("SELECT discount,expires_at FROM promos WHERE code=?", (code,))
        row=cur.fetchone()
        if not row:
            await m.answer("❌ Промокод не найден")
            return
        disc,exp=row
        if datetime.datetime.now()>datetime.datetime.strptime(exp,"%d.%m.%Y %H:%M"):
            await m.answer("⌛ Промокод истёк")
            return
        final_price=int(final_price*(100-disc)/100)
        promo=code

    # EVENT DISCOUNT
    ev_disc=get_event_discount()
    if ev_disc>0:
        final_price=int(final_price*(100-ev_disc)/100)

    cur.execute("INSERT INTO orders(telegram_id,uc,price,final_price,promo,status) VALUES(?,?,?,?,?,?)",
                (m.from_user.id,data["uc"],data["price"],final_price,promo,"waiting"))
    db.commit()
    oid=cur.lastrowid
    pending_order.pop(m.from_user.id)

    await m.answer(
        f"🧾 <b>Заказ #{oid}</b>\n💎 {data['uc']} UC\n💰 {final_price} ₽\n\n<a href='{PAY_URL}'>Перейти к оплате</a>",
        reply_markup=paid_btn
    )

@user_router.callback_query(F.data=="paid")
async def paid(c: CallbackQuery):
    await c.message.answer("⏳ Оплата отмечена. Ожидайте подтверждения.")
    await c.answer()

@user_router.message(F.text=="📦 Мои заказы")
async def history(m: Message):
    cur.execute("SELECT id,uc,final_price,status FROM orders WHERE telegram_id=?", (m.from_user.id,))
    rows=cur.fetchall()
    if not rows:
        await m.answer("Заказов пока нет")
        return
    text="📦 Ваши заказы:\n"
    for r in rows:
        st="⏳" if r[3]=="waiting" else "✅" if r[3]=="completed" else "❌"
        text+=f"#{r[0]} — {r[1]} UC — {r[2]} ₽ — {st}\n"
    await m.answer(text)

# ================= ADMIN =================

@admin_router.message(Command("admin"))
async def admin_panel(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ Нет доступа")
        return
    await m.answer("👑 Админ панель", reply_markup=admin_menu())

@admin_router.message(F.text=="🚪 Выйти")
async def exit_admin(m: Message):
    await m.answer("Вы вышли", reply_markup=main_menu())

@admin_router.message(F.text=="🏆 Топ покупателей")
async def top_users(m: Message):
    cur.execute("SELECT telegram_id,COUNT(*) FROM orders WHERE status='completed' GROUP BY telegram_id ORDER BY COUNT(*) DESC LIMIT 10")
    rows=cur.fetchall()
    if not rows:
        await m.answer("Пока нет данных")
        return
    text="🏆 <b>Топ покупателей:</b>\n"
    for i,r in enumerate(rows,1):
        text+=f"{i}. {r[0]} — {r[1]} заказов\n"
    await m.answer(text)

@admin_router.message(F.text=="➕ Добавить админа")
async def add_admin(m: Message):
    admin_state[m.from_user.id]="add_admin"
    await m.answer("Введите Telegram ID:")

@admin_router.message(F.text=="👥 Админы")
async def list_admins(m: Message):
    cur.execute("SELECT telegram_id FROM admins")
    rows=cur.fetchall()
    text="👥 Админы:\n"
    for r in rows: text+=str(r[0])+"\n"
    await m.answer(text)

@admin_router.message(F.text=="🎁 Промокод")
async def promo_create(m: Message):
    admin_state[m.from_user.id]="promo"
    await m.answer("Формат: CODE | % | 10.01.2026 00:00")

@admin_router.message(F.text=="🎉 Ивент")
async def event_create(m: Message):
    admin_state[m.from_user.id]="event"
    await m.answer("Формат: Название | % | 10.01.2026 00:00")

@admin_router.message(F.text=="📢 Сообщение всем")
async def bc(m: Message):
    admin_state[m.from_user.id]="bc"
    await m.answer("Введите сообщение:")

@admin_router.message(F.text=="📦 Заказы")
async def orders(m: Message):
    cur.execute("SELECT id,telegram_id,uc,final_price,status FROM orders ORDER BY id DESC LIMIT 10")
    for r in cur.fetchall():
        await m.answer(
            f"#{r[0]}\n👤 {r[1]}\n💎 {r[2]} UC\n💰 {r[3]} ₽\n📦 {r[4]}",
            reply_markup=order_btn(r[0])
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
    s=admin_state.get(m.from_user.id)
    if not s: return

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
        cur.execute("INSERT INTO events(name,discount,until) VALUES (?,?,?)",(n,int(d),u))
        db.commit()
        await m.answer("Ивент создан")

    elif s=="bc":
        cur.execute("SELECT DISTINCT telegram_id FROM orders")
        for u in cur.fetchall():
            try: await bot.send_message(u[0],m.text)
            except: pass
        await m.answer("Сообщение отправлено")

    admin_state.pop(m.from_user.id,None)

# ================= RUN =================

dp.include_router(admin_router)
dp.include_router(user_router)

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
