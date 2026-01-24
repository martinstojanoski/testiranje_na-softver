import sqlite3

DB_NAME = "hotel.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    # ----------------------------
    # BOOKINGS
    # ----------------------------
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            checkout_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ----------------------------
    # USERS
    # ----------------------------
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            password_changed_at TEXT,
            password_changed_by TEXT
        )
    """)

    # ----------------------------
    # MIGRATION (ако табелата е стара)
    # ----------------------------
    existing_cols = {
        row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }

    if "password_changed_at" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_changed_at TEXT")

    if "password_changed_by" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_changed_by TEXT")

    conn.commit()
    conn.close()
