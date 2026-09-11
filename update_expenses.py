import hashlib
import os
from datetime import datetime

from parser import (
    read_gpay_transactions,
    clean_gpay_transactions
)

from pdf_parser import (
    extract_transactions_from_pdf
)

from categorizer import (
    categorize_transaction
)

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update,
    get_dashboard_stats,
    get_last_update,
    get_recent_transactions,
    get_all_transactions,
    get_top_merchants
)


def clean_value(value):
    """Convert a value safely to a clean string."""

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {
        "nan",
        "none",
        "null"
    }:
        return ""

    return text


def create_source_id(transaction):
    """
    Create a stable unique ID.

    Google Pay transaction ID is preferred.
    If unavailable, create a SHA256 ID from
    date + merchant + amount + source.
    """

    transaction_id = clean_value(
        transaction.get("transaction_id", "")
    )

    if transaction_id:
        return transaction_id

    date = clean_value(
        transaction.get("date", "")
    )

    merchant = clean_value(
        transaction.get("merchant", "")
    )

    amount = clean_value(
        transaction.get("amount", "")
    )

    source = clean_value(
        transaction.get("source", "Google Pay")
    ) or "Google Pay"

    text = "|".join([
        date,
        merchant,
        amount,
        source
    ])

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def extract_paid_to(transaction):
    """
    Get the person/business the payment was made to.

    Uses paid_to when available.
    Otherwise falls back to merchant.
    """

    paid_to = clean_value(
        transaction.get("paid_to", "")
    )

    if paid_to:
        return paid_to

    merchant = clean_value(
        transaction.get("merchant", "")
    )

    return merchant or "Unknown"


def read_uploaded_file(file_path):

    if not file_path:
        raise ValueError(
            "No file was supplied."
        )

    ext = os.path.splitext(
        file_path
    )[1].lower()

    if ext == ".csv":

        df = read_gpay_transactions(
            file_path
        )

        return clean_gpay_transactions(
            df
        )

    if ext == ".pdf":

        return extract_transactions_from_pdf(
            file_path
        )

    raise ValueError(
        "Unsupported file type. "
        "Please upload a CSV or PDF file."
    )


def save_new_transactions(transactions):

    new_count = 0
    duplicate_count = 0

    if not transactions:
        return new_count, duplicate_count

    for transaction in transactions:

        # -------------------------------
        # BASIC INFORMATION
        # -------------------------------

        source = clean_value(
            transaction.get(
                "source",
                "Google Pay"
            )
        ) or "Google Pay"

        source_id = create_source_id(
            transaction
        )

        transaction_id = clean_value(
            transaction.get(
                "transaction_id",
                ""
            )
        )

        date = clean_value(
            transaction.get(
                "date",
                ""
            )
        )

        merchant = clean_value(
            transaction.get(
                "merchant",
                "Unknown"
            )
        ) or "Unknown"

        paid_to = extract_paid_to(
            transaction
        )

        # -------------------------------
        # AMOUNT
        # -------------------------------

        try:

            amount = float(
                transaction.get(
                    "amount",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            amount = 0.0

        if amount <= 0:
            continue

        # -------------------------------
        # CATEGORY
        # -------------------------------

        category = clean_value(
            transaction.get(
                "category",
                ""
            )
        )

        if not category:

            category = categorize_transaction(
                merchant,
                amount
            )

        # -------------------------------
        # DESCRIPTION
        # -------------------------------

        description = clean_value(
            transaction.get(
                "description",
                ""
            )
        )

        # -------------------------------
        # PAYMENT METHOD
        # -------------------------------

        payment_method = clean_value(
            transaction.get(
                "payment_method",
                ""
            )
        )

        # -------------------------------
        # STATUS
        # -------------------------------

        status = clean_value(
            transaction.get(
                "status",
                ""
            )
        )

        # -------------------------------
        # DUPLICATE CHECK
        # -------------------------------

        if transaction_exists(
            source,
            source_id
        ):

            duplicate_count += 1
            continue

        # -------------------------------
        # SAVE PERMANENTLY
        # -------------------------------

        saved = save_transaction(

            source=source,

            source_id=source_id,

            transaction_id=transaction_id,

            date=date,

            merchant=merchant,

            paid_to=paid_to,

            amount=amount,

            category=category,

            description=description,

            payment_method=payment_method,

            status=status
        )

        if saved:

            new_count += 1

        else:

            duplicate_count += 1

    return (
        new_count,
        duplicate_count
    )


def build_dashboard_result():
    initialize_database()

    stats = get_dashboard_stats()
    transactions = get_all_transactions()
    merchants = get_top_merchants()
    last_update = get_last_update()

    return {
        "stats": stats,
        "transactions": transactions,
        "recent": transactions[:20],
        "merchants": merchants,
        "last_update": last_update
    }


def analyze_uploaded_file(file_path):

    started_at = datetime.now().isoformat()

    try:

        initialize_database()

        print("=" * 60)
        print("EXPENSE TRACKER")
        print("PROCESSING NEW FILE")
        print("=" * 60)

        print(
            "File:",
            file_path
        )

        # -------------------------------
        # READ FILE
        # -------------------------------

        transactions = read_uploaded_file(
            file_path
        )

        print(
            "Transactions found:",
            len(transactions)
        )

        # -------------------------------
        # CATEGORIZE
        # -------------------------------

        for transaction in transactions:

            merchant = clean_value(
                transaction.get(
                    "merchant",
                    "Unknown"
                )
            ) or "Unknown"

            try:
                amount = float(
                    transaction.get(
                        "amount",
                        0
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                amount = 0

            transaction["category"] = (
                categorize_transaction(
                    merchant,
                    amount
                )
            )

            # Ensure paid_to exists
            transaction["paid_to"] = (
                extract_paid_to(
                    transaction
                )
            )

        # -------------------------------
        # SAVE
        # -------------------------------

        new_count, duplicate_count = (
            save_new_transactions(
                transactions
            )
        )

        finished_at = datetime.now().isoformat()

        # -------------------------------
        # SUCCESS LOG
        # -------------------------------

        log_update(

            started_at=started_at,

            finished_at=finished_at,

            status="SUCCESS",

            new_transactions=new_count,

            error=""
        )

        print(
            "NEW TRANSACTIONS:",
            new_count
        )

        print(
            "DUPLICATES SKIPPED:",
            duplicate_count
        )

        print(
            "Existing transactions were kept."
        )

        # -------------------------------
        # BUILD DASHBOARD FROM
        # THE COMPLETE DATABASE
        # -------------------------------

        result = build_dashboard_result()

        result["upload_message"] = (
            f"Added {new_count} new "
            f"transaction(s). "
            f"Skipped {duplicate_count} "
            f"duplicate(s). "
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

        print(
            "UPLOAD ERROR:",
            str(error)
        )

        raise


def run_update():

    raise RuntimeError(
        "run_update() is not used for "
        "uploaded files. "
        "Please upload a CSV or PDF "
        "through the website."
    )


if __name__ == "__main__":

    print(
        "Expense Tracker update module loaded."
    )

    print(
        "Use the Flask website to upload "
        "a CSV or PDF."
    )