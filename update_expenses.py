import hashlib
import os
from collections import defaultdict
from datetime import datetime

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions
)

from pdf_parser import (
    extract_transactions_from_pdf
)

from categorizer import categorize_transaction

from database import (
    get_dashboard_stats,
    get_last_update,
    get_recent_transactions,
    get_top_merchants
)


# ============================================================
# CREATE A STABLE ID
# ============================================================

def create_source_id(transaction):
    """
    Prefer the GPay transaction ID.

    If the file does not contain one, create a stable hash from
    date + merchant + amount + source.

    This lets later monthly uploads skip transactions already
    stored in the database.
    """
    transaction_id = str(
        transaction.get("transaction_id", "")
    ).strip()

    if transaction_id and transaction_id.lower() not in {
        "nan", "none", "null"
    }:
        return transaction_id

    text = "|".join([
        str(transaction.get("date", "")).strip(),
        str(transaction.get("merchant", "")).strip(),
        str(transaction.get("amount", "")).strip(),
        str(transaction.get("source", "")).strip()
    ])

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# READ ONE UPLOADED FILE
# ============================================================

def read_uploaded_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df = read_gpay_transactions(file_path)
        return clean_gpay_transactions(df)

    if ext == ".pdf":
        return extract_transactions_from_pdf(file_path)

    raise ValueError(
        "Unsupported file type. Please upload a CSV or PDF."
    )


# ============================================================
# ADD ONLY NEW TRANSACTIONS
# ============================================================

def save_new_transactions(transactions):
    new_count = 0
    duplicate_count = 0

    for transaction in transactions:
        source = str(
            transaction.get("source", "Google Pay")
        ).strip() or "Google Pay"

        source_id = create_source_id(transaction)

        date = str(
            transaction.get("date", "")
        ).strip()

        merchant = str(
            transaction.get("merchant", "Unknown")
        ).strip() or "Unknown"

        try:
            amount = float(transaction.get("amount", 0))
        except (TypeError, ValueError):
            amount = 0.0

        if amount <= 0:
            continue

        category = transaction.get("category")

        if not category:
            category = categorize_transaction(
                merchant,
                amount
            )

        description = str(
            transaction.get("description", "")
        )

        # IMPORTANT:
        # Existing months are NEVER deleted.
        if transaction_exists(source, source_id):
            duplicate_count += 1
            continue

        saved = save_transaction(
            source=source,
            source_id=source_id,
            date=date,
            merchant=merchant,
            amount=amount,
            category=category,
            description=description
        )

        if saved:
            new_count += 1
        else:
            duplicate_count += 1

    return new_count, duplicate_count


# ============================================================
# MAIN UPLOAD PROCESS
# ============================================================

def analyze_uploaded_file(file_path):
    started_at = datetime.now().isoformat()

    try:
        initialize_database()

        print("\n" + "=" * 60)
        print("EXPENSE TRACKER - NEW FILE")
        print("=" * 60)
        print("File:", file_path)

        # Read ONLY the file uploaded in this request.
        transactions = read_uploaded_file(file_path)

        print("Transactions found in uploaded file:", len(transactions))

        # Categorize before saving.
        for transaction in transactions:
            transaction["category"] = categorize_transaction(
                transaction.get("merchant", "Unknown"),
                transaction.get("amount", 0)
            )

        new_count, duplicate_count = save_new_transactions(
            transactions
        )

        finished_at = datetime.now().isoformat()

        log_update(
            started_at=started_at,
            finished_at=finished_at,
            status="SUCCESS",
            new_transactions=new_count,
            error=""
        )

        print("NEW TRANSACTIONS:", new_count)
        print("DUPLICATES SKIPPED:", duplicate_count)
        print("Existing database data was kept.")

        result = build_dashboard_result()

        result["upload_message"] = (
            f"Added {new_count} new transaction(s). "
            f"Skipped {duplicate_count} duplicate(s). "
            f"Existing expenses were kept."
        )

        return result

    except Exception as error:
        finished_at = datetime.now().isoformat()

        try:
            log_update(
                started_at=started_at,
                finished_at=finished_at,
                status="FAILED",
                new_transactions=0,
                error=str(error)
            )
        except Exception:
            pass

        print("UPLOAD ERROR:", error)
        raise


# ============================================================
# LOAD THE COMPLETE DASHBOARD
# ============================================================

def build_dashboard_result():
    initialize_database()

    stats = get_dashboard_stats()
    recent_rows = get_recent_transactions(20)
    merchants = get_top_merchants()
    last_update = get_last_update()

    recent = [
        {
            "date": row[0],
            "merchant": row[1],
            "category": row[2],
            "amount": row[3]
        }
        for row in recent_rows
    ]

    return {
        "stats": stats,
        "recent": recent,
        "merchants": merchants,
        "last_update": last_update or "-"
    }


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def run_update():
    """
    Kept for compatibility with older code.

    This project now expects an uploaded file, so there is no
    hard-coded old Transactions.csv file to process here.
    """
    raise RuntimeError(
        "run_update() no longer reads an old fixed file. "
        "Upload a new CSV/PDF through the website."
    )


if __name__ == "__main__":
    print(
        "Use the Flask upload page to import a new expense file."
    )
