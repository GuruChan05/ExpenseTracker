import sqlite3
import os
from datetime import datetime

DATABASE = "expense_tracker.db"


def get_connection():
    return sqlite3.connect(DATABASE)


# ==========================================
# CREATE DATABASE & TABLES
# ==========================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            date TEXT,
            merchant TEXT,
            amount REAL,
            category TEXT,
            description TEXT,
            created_at TEXT
        )
    """)

    # Prevent duplicates
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_transaction
        ON transactions(source, source_id)
    """)

    # Update history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS update_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            new_transactions INTEGER,
            error TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")


# ==========================================
# CHECK DUPLICATE
# ==========================================

def transaction_exists(source, source_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM transactions
        WHERE source = ?
        AND source_id = ?
    """, (source, source_id))

    result = cursor.fetchone()

    connection.close()

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

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO transactions
            (
                source,
                source_id,
                date,
                merchant,
                amount,
                category,
                description,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            source_id,
            date,
            merchant,
            amount,
            category,
            description,
            datetime.now().isoformat()
        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        connection.close()


# ==========================================
# DASHBOARD STATISTICS
# ==========================================

def get_dashboard_stats():

    connection = get_connection()
    cursor = connection.cursor()

    # Total expenses
    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM transactions
    """)
    total_expenses = cursor.fetchone()[0]

    # Total transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
    """)
    total_transactions = cursor.fetchone()[0]

    # Google Pay
    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM transactions
        WHERE source='Google Pay'
    """)
    gpay_total = cursor.fetchone()[0]

    # Gmail
    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM transactions
        WHERE source='Gmail'
    """)
    gmail_total = cursor.fetchone()[0]

    # Categories
    cursor.execute("""
        SELECT category,
               SUM(amount)
        FROM transactions
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """)
    category_totals = cursor.fetchall()

    # Monthly
    cursor.execute("""
        SELECT substr(date,1,7),
               SUM(amount)
        FROM transactions
        GROUP BY substr(date,1,7)
        ORDER BY substr(date,1,7)
    """)
    monthly_totals = cursor.fetchall()

    connection.close()

    return {
        "total_expenses": total_expenses,
        "total_transactions": total_transactions,
        "gpay_total": gpay_total,
        "gmail_total": gmail_total,
        "category_totals": category_totals,
        "monthly_totals": monthly_totals
    }


# ==========================================
# LAST SUCCESSFUL UPDATE
# ==========================================

def get_last_update():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT finished_at
        FROM update_logs
        WHERE status='SUCCESS'
        ORDER BY id DESC
        LIMIT 1
    """)

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


# ==========================================
# LOG UPDATE (REQUIRED BY update_expenses.py)
# ==========================================

def log_update(
    started_at,
    finished_at,
    status,
    new_transactions=0,
    error=""
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO update_logs
        (
            started_at,
            finished_at,
            status,
            new_transactions,
            error
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        started_at,
        finished_at,
        status,
        new_transactions,
        error
    ))

    connection.commit()
    connection.close()