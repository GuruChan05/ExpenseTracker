import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id SERIAL PRIMARY KEY,
        source TEXT,
        source_id TEXT UNIQUE,
        date TEXT,
        merchant TEXT,
        amount REAL,
        category TEXT,
        description TEXT,
        created_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS update_logs(
        id SERIAL PRIMARY KEY,
        started_at TEXT,
        finished_at TEXT,
        status TEXT,
        new_transactions INTEGER,
        error TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


def transaction_exists(source, source_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM transactions WHERE source_id=%s",
        (source_id,)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result is not None


def save_transaction(source, source_id, date,
                     merchant, amount,
                     category, description=""):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO transactions
    (source,source_id,date,merchant,
     amount,category,description,created_at)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT(source_id) DO NOTHING
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

    cur.close()
    conn.close()

    return True