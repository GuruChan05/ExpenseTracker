import hashlib
from datetime import datetime

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions,
    read_gmail_transactions
)

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update
)

from categorizer import categorize_transaction


CSV_FILE = "data/Transactions.csv"
GMAIL_FILE = "data/gmail.mbox"


def create_source_id(transaction):

    transaction_id = str(
        transaction.get(
            "transaction_id",
            ""
        )
    ).strip()

    # Google Pay / Gmail real ID
    if transaction_id:
        return transaction_id

    # Fallback ID
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


def get_transactions():

    transactions = []

    # ==========================================
    # GOOGLE PAY
    # ==========================================

    print("\nReading Google Pay...")

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

        transactions.extend(
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

        transactions.extend(
            gmail_transactions
        )

    except FileNotFoundError:

        print(
            "Gmail file not found."
        )

    except Exception as error:

        print(
            "Gmail error:",
            error
        )

    return transactions


def process_new_transactions(
    transactions
):

    new_count = 0
    duplicate_count = 0

    print("\n" + "=" * 60)
    print("CHECKING FOR NEW TRANSACTIONS")
    print("=" * 60)

    for index, transaction in enumerate(
        transactions,
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

        date = transaction.get(
            "date",
            ""
        )

        try:

            amount = float(amount)

        except (
            ValueError,
            TypeError
        ):

            amount = 0.0

        # ======================================
        # DUPLICATE CHECK
        # ======================================

        if transaction_exists(
            source,
            source_id
        ):

            duplicate_count += 1

            continue

        print(
            f"\nNEW TRANSACTION [{index}]"
        )

        print(
            "Source:",
            source
        )

        print(
            "Merchant:",
            merchant
        )

        print(
            f"Amount: ₹{amount:.2f}"
        )

        # ======================================
        # AI CATEGORIZATION
        # ======================================

        try:

            category = categorize_transaction(
                merchant,
                amount
            )

        except Exception as error:

            print(
                "Categorization error:",
                error
            )

            category = "Other"

        print(
            "Category:",
            category
        )

        # ======================================
        # SAVE
        # ======================================

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

            new_count += 1

            print(
                "Status: SAVED"
            )

        else:

            duplicate_count += 1

            print(
                "Status: DUPLICATE"
            )

    return new_count, duplicate_count


def run_update():

    started_at = datetime.now().isoformat()

    print("=" * 60)
    print("EXPENSE TRACKER - CONTINUOUS UPDATE")
    print("=" * 60)

    print(
        "Started:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    try:

        # ======================================
        # DATABASE
        # ======================================

        initialize_database()

        # ======================================
        # COLLECT DATA
        # ======================================

        transactions = get_transactions()

        print(
            "\nTotal collected:",
            len(transactions)
        )

        # ======================================
        # PROCESS NEW DATA
        # ======================================

        new_count, duplicate_count = (
            process_new_transactions(
                transactions
            )
        )

        finished_at = datetime.now().isoformat()

        # ======================================
        # LOG SUCCESS
        # ======================================

        log_update(
            started_at=started_at,
            finished_at=finished_at,
            status="SUCCESS",
            new_transactions=new_count,
            error=""
        )

        print("\n" + "=" * 60)
        print("UPDATE COMPLETED")
        print("=" * 60)

        print(
            "New transactions:",
            new_count
        )

        print(
            "Duplicates ignored:",
            duplicate_count
        )

        print(
            "Finished:",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        return True

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

        print("\n" + "=" * 60)
        print("UPDATE FAILED")
        print("=" * 60)

        print(error)

        return False


if __name__ == "__main__":

    success = run_update()

    if not success:
        raise SystemExit(1)