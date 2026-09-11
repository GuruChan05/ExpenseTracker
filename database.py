import os
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Connect to the permanent Supabase PostgreSQL database."""

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        row_factory=dict_row,
        prepare_threshold=None,
    )


def initialize_database():
    """Create the required tables if they don't already exist."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    transaction_id TEXT,
                    date TEXT,
                    merchant TEXT,
                    paid_to TEXT,
                    amount NUMERIC(12, 2) NOT NULL,
                    category TEXT,
                    description TEXT,
                    payment_method TEXT,
                    status TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),

                    CONSTRAINT unique_transaction
                    UNIQUE (source, source_id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS update_logs (
                    id BIGSERIAL PRIMARY KEY,
                    started_at TEXT,
                    finished_at TEXT,
                    status TEXT,
                    new_transactions INTEGER DEFAULT 0,
                    error TEXT
                )
            """)

        conn.commit()

    finally:
        conn.close()


def transaction_exists(source, source_id):
    """Check whether a transaction is already stored."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM transactions
                WHERE source = %s
                  AND source_id = %s
                LIMIT 1
            """, (source, source_id))

            return cur.fetchone() is not None

    finally:
        conn.close()


def save_transaction(
    source,
    source_id,
    date,
    merchant,
    amount,
    category,
    description="",
    transaction_id="",
    paid_to="",
    payment_method="",
    status=""
):
    """Save one transaction permanently in Supabase."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO transactions (
                    source,
                    source_id,
                    transaction_id,
                    date,
                    merchant,
                    paid_to,
                    amount,
                    category,
                    description,
                    payment_method,
                    status,
                    created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (source, source_id)
                DO NOTHING
                RETURNING id
            """, (
                source,
                source_id,
                transaction_id,
                date,
                merchant,
                paid_to,
                amount,
                category,
                description,
                payment_method,
                status,
                datetime.now()
            ))

            saved = cur.fetchone() is not None

        conn.commit()
        return saved

    finally:
        conn.close()


def get_dashboard_stats():
    """Return cumulative statistics from ALL stored transactions."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            # Total expenses
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM transactions
            """)
            total = float(cur.fetchone()["total"])

            # Number of transactions
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM transactions
            """)
            count = int(cur.fetchone()["count"])

            # Google Pay total
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM transactions
                WHERE source = 'Google Pay'
            """)
            gpay = float(cur.fetchone()["total"])

            # Gmail total
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM transactions
                WHERE source = 'Gmail'
            """)
            gmail = float(cur.fetchone()["total"])

            # Category totals
            cur.execute("""
                SELECT
                    COALESCE(category, 'Uncategorized') AS category,
                    SUM(amount) AS total
                FROM transactions
                GROUP BY category
                ORDER BY SUM(amount) DESC
            """)
            category_totals = [
                (
                    row["category"],
                    float(row["total"])
                )
                for row in cur.fetchall()
            ]

            # Monthly totals
            cur.execute("""
                SELECT
                    SUBSTRING(date, 1, 7) AS month,
                    SUM(amount) AS total
                FROM transactions
                WHERE date IS NOT NULL
                  AND date <> ''
                GROUP BY SUBSTRING(date, 1, 7)
                ORDER BY SUBSTRING(date, 1, 7)
            """)
            monthly_totals = [
                (
                    row["month"],
                    float(row["total"])
                )
                for row in cur.fetchall()
            ]

        return {
            "total_expenses": total,
            "total_expense": total,
            "total_transactions": count,
            "gpay_total": gpay,
            "gmail_total": gmail,
            "category_totals": category_totals,
            "monthly_totals": monthly_totals
        }

    finally:
        conn.close()


def get_last_update():
    """Return the time of the most recent successful upload."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT finished_at
                FROM update_logs
                WHERE status = 'SUCCESS'
                ORDER BY id DESC
                LIMIT 1
            """)

            row = cur.fetchone()

            if row:
                return row["finished_at"]

            return None

    finally:
        conn.close()


def log_update(
    started_at,
    finished_at,
    status,
    new_transactions=0,
    error=""
):
    """Store an upload/update log permanently."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO update_logs (
                    started_at,
                    finished_at,
                    status,
                    new_transactions,
                    error
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                started_at,
                finished_at,
                status,
                new_transactions,
                error
            ))

        conn.commit()

    finally:
        conn.close()


def get_recent_transactions(limit=20):
    """Return the most recently stored transactions."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    date,
                    merchant,
                    paid_to,
                    amount,
                    category,
                    description,
                    payment_method,
                    status,
                    transaction_id,
                    source
                FROM transactions
                ORDER BY
                    CASE
                        WHEN date IS NULL OR date = '' THEN 1
                        ELSE 0
                    END,
                    date DESC,
                    id DESC
                LIMIT %s
            """, (limit,))

            rows = cur.fetchall()

            return [
                {
                    "date": row["date"],
                    "merchant": row["merchant"],
                    "paid_to": row["paid_to"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "description": row["description"],
                    "payment_method": row["payment_method"],
                    "status": row["status"],
                    "transaction_id": row["transaction_id"],
                    "source": row["source"]
                }
                for row in rows
            ]

    finally:
        conn.close()


def get_all_transactions():
    """Return the complete permanent expense ledger."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    date,
                    merchant,
                    paid_to,
                    amount,
                    category,
                    description,
                    payment_method,
                    status,
                    transaction_id,
                    source,
                    created_at
                FROM transactions
                ORDER BY date DESC, id DESC
            """)

            rows = cur.fetchall()

            return [
                {
                    "id": row["id"],
                    "date": row["date"],
                    "merchant": row["merchant"],
                    "paid_to": row["paid_to"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "description": row["description"],
                    "payment_method": row["payment_method"],
                    "status": row["status"],
                    "transaction_id": row["transaction_id"],
                    "source": row["source"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

    finally:
        conn.close()


def get_top_merchants():
    """Return the top merchants by total spending."""

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(merchant, 'Unknown') AS merchant,
                    SUM(amount) AS total
                FROM transactions
                GROUP BY merchant
                ORDER BY SUM(amount) DESC
                LIMIT 5
            """)

            return [
                (
                    row["merchant"],
                    float(row["total"])
                )
                for row in cur.fetchall()
            ]

    finally:
        conn.close()