import hashlib
import os
from datetime import datetime

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions
)

from categorizer import categorize_transaction

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update
)

# ==========================================
# UNIQUE TRANSACTION ID
# ==========================================

def create_source_id(transaction):

    transaction_id = str(
        transaction.get("transaction_id", "")
    ).strip()

    if transaction_id:
        return transaction_id

    text = (
        str(transaction.get("date")) +
        "|" +
        str(transaction.get("merchant")) +
        "|" +
        str(transaction.get("amount")) +
        "|" +
        str(transaction.get("source"))
    )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

# ==========================================
# READ CSV
# ==========================================

def get_transactions(csv_file):

    print("\nReading uploaded CSV...")

    df = read_gpay_transactions(csv_file)

    transactions = clean_gpay_transactions(df)

    print(
        "Transactions Found:",
        len(transactions)
    )

    return transactions

# ==========================================
# PROCESS
# ==========================================

def process_transactions(transactions):

    new_count = 0

    duplicate_count = 0

    for transaction in transactions:

        source = transaction["source"]

        source_id = create_source_id(transaction)

        if transaction_exists(
            source,
            source_id
        ):

            duplicate_count += 1

            continue

        merchant = transaction["merchant"]

        amount = float(transaction["amount"])

        category = categorize_transaction(
            merchant,
            amount
        )

        save_transaction(
            source,
            source_id,
            transaction["date"],
            merchant,
            amount,
            category,
            str(transaction)
        )

        new_count += 1

    print("New:", new_count)

    print("Duplicates:", duplicate_count)

    return new_count

# ==========================================
# MAIN UPDATE
# ==========================================

def run_update(csv_file):

    initialize_database()

    started = datetime.now().isoformat()

    transactions = get_transactions(csv_file)

    new_count = process_transactions(
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

    return True

# ==========================================

if __name__ == "__main__":

    run_update("uploads/Transactions.csv")