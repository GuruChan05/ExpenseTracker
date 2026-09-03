from parser import (
    read_gpay_transactions,
    clean_gpay_transactions,
    read_gmail_transactions
)

from database import (
    initialize_database,
    transaction_exists,
    save_transaction
)

import hashlib


CSV_FILE = "data/Transactions.csv"
GMAIL_FILE = "data/gmail.mbox"


def create_source_id(transaction):

    transaction_id = str(
        transaction.get(
            "transaction_id",
            ""
        )
    ).strip()

    # Prefer the real transaction/message ID
    if transaction_id:
        return transaction_id

    # Fallback if an ID is unavailable
    text = (
        str(transaction.get("date", "")) +
        "|" +
        str(transaction.get("merchant", "")) +
        "|" +
        str(transaction.get("amount", "")) +
        "|" +
        str(transaction.get("source", ""))
    )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def main():

    print("=" * 60)
    print("IMPORTING EXISTING EXPENSE DATA")
    print("=" * 60)

    # Create database
    initialize_database()

    all_transactions = []

    # ==========================================
    # GOOGLE PAY
    # ==========================================

    print("\nReading Google Pay CSV...")

    try:

        df = read_gpay_transactions(
            CSV_FILE
        )

        gpay_transactions = (
            clean_gpay_transactions(df)
        )

        print(
            "Google Pay transactions:",
            len(gpay_transactions)
        )

        all_transactions.extend(
            gpay_transactions
        )

    except Exception as error:

        print(
            "Google Pay error:",
            error
        )

    # ==========================================
    # GMAIL
    # ==========================================

    print("\nReading Gmail...")

    try:

        gmail_transactions = (
            read_gmail_transactions(
                GMAIL_FILE
            )
        )

        if gmail_transactions is None:
            gmail_transactions = []

        print(
            "Gmail transactions:",
            len(gmail_transactions)
        )

        all_transactions.extend(
            gmail_transactions
        )

    except Exception as error:

        print(
            "Gmail error:",
            error
        )

    # ==========================================
    # IMPORT
    # ==========================================

    print("\n" + "=" * 60)
    print("IMPORTING INTO DATABASE")
    print("=" * 60)

    added = 0
    skipped = 0

    for index, transaction in enumerate(
        all_transactions,
        start=1
    ):

        source = transaction.get(
            "source",
            "Unknown"
        )

        source_id = create_source_id(
            transaction
        )

        merchant = transaction.get(
            "merchant",
            "Unknown"
        )

        amount = transaction.get(
            "amount",
            0
        )

        try:

            amount = float(amount)

        except (ValueError, TypeError):

            amount = 0.0

        date = transaction.get(
            "date",
            ""
        )

        print(
            f"[{index}/{len(all_transactions)}] "
            f"{source} | {merchant} | ₹{amount:.2f}"
        )

        # Check duplicate
        if transaction_exists(
            source,
            source_id
        ):

            skipped += 1

            continue

        # --------------------------------------
        # IMPORTANT
        # --------------------------------------
        # We don't call Ollama here.
        #
        # Existing transactions will initially
        # receive "Other".
        #
        # Your current app.py can continue doing
        # the AI categorization.
        # --------------------------------------

        category = "Other"

        saved = save_transaction(
            source=source,
            source_id=source_id,
            date=date,
            merchant=merchant,
            amount=amount,
            category=category,
            description=str(transaction)
        )

        if saved:

            added += 1

        else:

            skipped += 1

    print("\n" + "=" * 60)
    print("IMPORT COMPLETED")
    print("=" * 60)

    print(
        "Total processed:",
        len(all_transactions)
    )

    print(
        "New transactions added:",
        added
    )

    print(
        "Duplicates skipped:",
        skipped
    )


if __name__ == "__main__":
    main()