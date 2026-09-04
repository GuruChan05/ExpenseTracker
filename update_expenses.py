import os

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions
)

from pdf_parser import (
    extract_transactions_from_pdf
)

from categorizer import categorize_transaction

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update
)

from datetime import datetime
import hashlib

def create_id(t):

    text = (
        str(t["date"]) +
        str(t["merchant"]) +
        str(t["amount"])
    )

    return hashlib.sha256(text.encode()).hexdigest()

def read_file(path):

    extension = os.path.splitext(path)[1].lower()

    if extension == ".csv":

        df = read_gpay_transactions(path)

        return clean_gpay_transactions(df)

    elif extension == ".pdf":

        return extract_transactions_from_pdf(path)

    else:

        return []

def run_update(file_path):

    initialize_database()

    started = datetime.now().isoformat()

    transactions = read_file(file_path)

    new_count = 0

    for t in transactions:

        source_id = create_id(t)

        if transaction_exists(
            t["source"],
            source_id
        ):
            continue

        category = categorize_transaction(
            t["merchant"],
            t["amount"]
        )

        save_transaction(

            t["source"],

            source_id,

            t["date"],

            t["merchant"],

            t["amount"],

            category,

            ""

        )

        new_count += 1

    log_update(

        started,

        datetime.now().isoformat(),

        "SUCCESS",

        new_count,

        ""

    )

    print("Imported:", new_count)

    return True