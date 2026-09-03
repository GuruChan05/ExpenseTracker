import hashlib
import os
import tempfile
from datetime import datetime

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions,
    read_gmail_transactions
)

from categorizer import categorize_transaction

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update
)

# ==========================================
# FILE PATHS
# ==========================================

if os.getenv("VERCEL"):

    CSV_FILE = os.path.join(
        tempfile.gettempdir(),
        "uploads",
        "Transactions.csv"
    )

else:

    CSV_FILE = "uploads/Transactions.csv"

GMAIL_FILE = "data/gmail.mbox"

# ==========================================
# UNIQUE ID
# ==========================================

def create_source_id(transaction):

    transaction_id = str(
        transaction.get(
            "transaction_id",
            ""
        )
    ).strip()

    if transaction_id:
        return transaction_id

    text = (
        str(transaction.get("date")) +
        str(transaction.get("merchant")) +
        str(transaction.get("amount")) +
        str(transaction.get("source"))
    )

    return hashlib.sha256(
        text.encode()
    ).hexdigest()

# ==========================================
# COLLECT DATA
# ==========================================

def get_transactions():

    transactions = []

    if os.path.exists(CSV_FILE):

        df = read_gpay_transactions(CSV_FILE)

        transactions.extend(
            clean_gpay_transactions(df)
        )

    if os.path.exists(GMAIL_FILE):

        gmail = read_gmail_transactions(
            GMAIL_FILE
        )

        if gmail:

            transactions.extend(gmail)

    return transactions

# ==========================================
# SAVE ONLY NEW
# ==========================================

def process_transactions(transactions):

    new_count = 0

    duplicates = 0

    for transaction in transactions:

        source = transaction.get("source")

        source_id = create_source_id(
            transaction
        )

        if transaction_exists(
            source,
            source_id
        ):

            duplicates += 1

            continue

        merchant = transaction.get(
            "merchant",
            "Unknown"
        )

        amount = float(
            transaction.get(
                "amount",
                0
            )
        )

        category = categorize_transaction(
            merchant,
            amount
        )

        save_transaction(
            source,
            source_id,
            transaction.get("date"),
            merchant,
            amount,
            category,
            str(transaction)
        )

        new_count += 1

    return new_count, duplicates

# ==========================================
# MAIN UPDATE
# ==========================================

def run_update():

    initialize_database()

    started = datetime.now().isoformat()

    transactions = get_transactions()

    new_count, duplicates = process_transactions(
        transactions
    )

    finished = datetime.now().isoformat()

    log_update(
        started,
        finished,
        "SUCCESS",
        new_count,
        ""
    )

    print("New:", new_count)

    print("Duplicates:", duplicates)

    return True

# ==========================================

if __name__ == "__main__":

    run_update()