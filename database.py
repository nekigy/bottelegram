import sqlite3

def init_db():
    db = sqlite3.connect("shop.db")
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        uc INTEGER,
        price INTEGER,
        final_price INTEGER,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS admins(
        telegram_id INTEGER PRIMARY KEY
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        discount INTEGER,
        until TEXT
    )""")

    db.commit()
    db.close()
