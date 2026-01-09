import sqlite3

def init_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        uc INTEGER,
        price INTEGER,
        final_price INTEGER,
        promo TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        telegram_id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS promos (
        code TEXT PRIMARY KEY,
        discount INTEGER,
        expires_at TEXT
    )
    """)

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
