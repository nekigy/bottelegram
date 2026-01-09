import sqlite3

def init_all():
    # orders
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
    conn.commit(); conn.close()

    # promos
    conn = sqlite3.connect("promocode.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS promos (
        code TEXT PRIMARY KEY,
        discount INTEGER,
        expires_at TEXT
    )
    """)
    conn.commit(); conn.close()

    # used promo
    conn = sqlite3.connect("usedpromo.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS used (
        telegram_id INTEGER,
        code TEXT,
        PRIMARY KEY (telegram_id, code)
    )
    """)
    conn.commit(); conn.close()

    # admins
    conn = sqlite3.connect("admin.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        telegram_id INTEGER PRIMARY KEY
    )
    """)
    conn.commit(); conn.close()

    # events
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
    conn.commit(); conn.close()
