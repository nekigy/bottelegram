import sqlite3

def init_all():
    # Orders
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
    conn.commit(); conn.close()

    # Admins
    conn = sqlite3.connect("admin.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        telegram_id INTEGER PRIMARY KEY
    )
    """)
    conn.commit(); conn.close()

    # Events
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
