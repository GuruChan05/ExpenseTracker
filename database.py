import sqlite3
import os
from datetime import datetime

# ==========================================
# DATABASE LOCATION
# ==========================================

if os.getenv("VERCEL"):
    DATABASE = "/tmp/expense_tracker.db"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE = os.path.join(BASE_DIR, "expense_tracker.db")


def get_connection():
    return sqlite3.connect(DATABASE)


# ==========================================
# CREATE TABLES
# ==========================================

def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        source_id TEXT,
        date TEXT,
        merchant TEXT,
        amount REAL,
        category TEXT,
        description TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS unique_transaction
    ON transactions(source, source_id)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS update_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT,
        finished_at TEXT,
        status TEXT,
        new_transactions INTEGER,
        error TEXT
    )
    """)

    conn.commit()
    conn.close()


# ==========================================
# DUPLICATE CHECK
# ==========================================

def transaction_exists(source, source_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id FROM transactions
    WHERE source=? AND source_id=?
    """, (source, source_id))

    result = cur.fetchone()

    conn.close()

    return result is not None


# ==========================================
# SAVE TRANSACTION
# ==========================================

def save_transaction(
    source,
    source_id,
    date,
    merchant,
    amount,
    category,
    description=""
):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
        INSERT INTO transactions(
            source,
            source_id,
            date,
            merchant,
            amount,
            category,
            description,
            created_at
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            source,
            source_id,
            date,
            merchant,
            amount,
            category,
            description,
            datetime.now().isoformat()
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


# ==========================================
# DASHBOARD
# ==========================================

def get_dashboard_stats():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM transactions")
    count = cur.fetchone()[0]

    cur.execute("""
    SELECT COALESCE(SUM(amount),0)
    FROM transactions
    WHERE source='Google Pay'
    """)
    gpay = cur.fetchone()[0]

    cur.execute("""
    SELECT COALESCE(SUM(amount),0)
    FROM transactions
    WHERE source='Gmail'
    """)
    gmail = cur.fetchone()[0]

    cur.execute("""
    SELECT category,SUM(amount)
    FROM transactions
    GROUP BY category
    ORDER BY SUM(amount) DESC
    """)
    category = cur.fetchall()

    cur.execute("""
    SELECT substr(date,1,7),SUM(amount)
    FROM transactions
    GROUP BY substr(date,1,7)
    ORDER BY substr(date,1,7)
    """)
    monthly = cur.fetchall()

    conn.close()

    return {
        "total_expenses": total,
        "total_transactions": count,
        "gpay_total": gpay,
        "gmail_total": gmail,
        "category_totals": category,
        "monthly_totals": monthly
    }


# ==========================================
# LAST UPDATE
# ==========================================

def get_last_update():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT finished_at
    FROM update_logs
    WHERE status='SUCCESS'
    ORDER BY id DESC
    LIMIT 1
    """)

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


# ==========================================
# LOG UPDATE
# ==========================================

def log_update(
    started_at,
    finished_at,
    status,
    new_transactions=0,
    error=""
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO update_logs(
        started_at,
        finished_at,
        status,
        new_transactions,
        error
    )
    VALUES(?,?,?,?,?)
    """,
    (
        started_at,
        finished_at,
        status,
        new_transactions,
        error
    ))

    conn.commit()
    conn.close()

    # ==========================================
# RECENT TRANSACTIONS
# ==========================================

def get_recent_transactions(limit=10):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date,
               merchant,
               category,
               amount
        FROM transactions
        ORDER BY date DESC
        LIMIT ?
    """,(limit,))

    data = cur.fetchall()

    conn.close()

    return data


# ==========================================
# TOP MERCHANTS
# ==========================================

def get_top_merchants():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT merchant,
               SUM(amount) total
        FROM transactions
        GROUP BY merchant
        ORDER BY total DESC
        LIMIT 5
    """)

    data = cur.fetchall()

    conn.close()

    return data