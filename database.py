
import sqlite3

def init_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        uc INTEGER,
        price INTEGER,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS admins(
        telegram_id INTEGER PRIMARY KEY
    )""")

    conn.commit()
    conn.close()
