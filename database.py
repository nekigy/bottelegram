import sqlite3

def init_orders_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        uc INTEGER,
        price INTEGER,
        final_price INTEGER,
        promo_code TEXT,
        status TEXT,
        created_at INTEGER
    )
    """)
    conn.commit()
    conn.close()

def init_promo_db():
    conn = sqlite3.connect("promocode.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS promos (
        code TEXT PRIMARY KEY,
        discount INTEGER,
        expires_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def init_usedpromo_db():
    conn = sqlite3.connect("usedpromo.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS used (
        telegram_id INTEGER,
        code TEXT,
        PRIMARY KEY (telegram_id, code)
    )
    """)
    conn.commit()
    conn.close()
