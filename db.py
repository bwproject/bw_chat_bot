import sqlite3

DB_PATH = "bot.db"


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dialogs (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        last_message TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        notify INTEGER DEFAULT 1,
        auto_reply INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_replied (
        user_id INTEGER PRIMARY KEY
    )
    """)

    conn.commit()
    conn.close()


def set_dialog(user_id, name, last_message):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO dialogs (user_id, name, last_message)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
    name=excluded.name,
    last_message=excluded.last_message
    """, (user_id, name, last_message))

    conn.commit()
    conn.close()


def get_dialogs():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT user_id, name FROM dialogs")
    rows = cur.fetchall()

    conn.close()
    return rows


def set_setting(user_id, field, value):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO settings (user_id, notify, auto_reply)
    VALUES (?, 1, 1)
    ON CONFLICT(user_id) DO NOTHING
    """, (user_id,))

    cur.execute(f"""
    UPDATE settings SET {field} = ?
    WHERE user_id = ?
    """, (value, user_id))

    conn.commit()
    conn.close()


def get_setting(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT notify, auto_reply
    FROM settings
    WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return {"notify": 1, "auto_reply": 1}

    return {"notify": row[0], "auto_reply": row[1]}


def add_admin_reply(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO admin_replied (user_id)
    VALUES (?)
    """, (user_id,))

    conn.commit()
    conn.close()


def check_admin_reply(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT 1 FROM admin_replied WHERE user_id = ?
    """, (user_id,))

    return cur.fetchone() is not None