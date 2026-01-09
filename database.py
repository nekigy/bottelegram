import sqlite3

def init_dbs():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        uc INTEGER,
        price INTEGER,
        final_price INTEGER,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

    conn = sqlite3.connect("events.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        discount INTEGER,
        until TEXT
    )
    """)
    conn.commit()
    conn.close()
