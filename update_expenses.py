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

# ============================================================
# DATABASE IMPORTS
# ============================================================

from database import (
    initialize_database,
    transaction_exists,
    save_transaction,
    log_update,
    get_dashboard_stats,
    get_last_update,
    get_recent_transactions,
    get_top_merchants
)


# ============================================================
# CREATE STABLE TRANSACTION ID
# ============================================================

def create_source_id(transaction):
    """
    Create a stable ID for each transaction.

    First preference:
        Google Pay Transaction ID

    If Transaction ID is unavailable:
        SHA256(date + merchant + amount + source)

    This prevents the same transaction from being
    inserted again when the same monthly file is uploaded.
    """

    transaction_id = str(
        transaction.get("transaction_id", "")
    ).strip()

    if transaction_id:
        if transaction_id.lower() not in {
            "nan",
            "none",
            "null",
            ""
        }:
            return transaction_id

    date = str(
        transaction.get("date", "")
    ).strip()

    merchant = str(
        transaction.get("merchant", "")
    ).strip()

    amount = str(
        transaction.get("amount", "")
    ).strip()

    source = str(
        transaction.get("source", "Google Pay")
    ).strip()

    text = "|".join([
        date,
        merchant,
        amount,
        source
    ])

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# READ UPLOADED FILE
# ============================================================

def read_uploaded_file(file_path):

    if not file_path:
        raise ValueError(
            "No file was supplied."
        )

    ext = os.path.splitext(
        file_path
    )[1].lower()

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    if ext == ".csv":

        df = read_gpay_transactions(
            file_path
        )

        transactions = clean_gpay_transactions(
            df
        )

        return transactions

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if ext == ".pdf":

        transactions = extract_transactions_from_pdf(
            file_path
        )

        return transactions

    # --------------------------------------------------------
    # Unsupported
    # --------------------------------------------------------

    raise ValueError(
        "Unsupported file type. "
        "Please upload a CSV or PDF file."
    )


# ============================================================
# SAVE ONLY NEW TRANSACTIONS
# ============================================================

def save_new_transactions(transactions):

    new_count = 0
    duplicate_count = 0

    if not transactions:
        return new_count, duplicate_count

    for transaction in transactions:

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        source = str(
            transaction.get(
                "source",
                "Google Pay"
            )
        ).strip()

        if not source:
            source = "Google Pay"

        # ----------------------------------------------------
        # TRANSACTION ID
        # ----------------------------------------------------

        source_id = create_source_id(
            transaction
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date = str(
            transaction.get(
                "date",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # MERCHANT
        # ----------------------------------------------------

        merchant = str(
            transaction.get(
                "merchant",
                "Unknown"
            )
        ).strip()

        if not merchant:
            merchant = "Unknown"

        # ----------------------------------------------------
        # AMOUNT
        # ----------------------------------------------------

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

        # Ignore invalid/zero amounts

        if amount <= 0:
            continue

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        category = transaction.get(
            "category"
        )

        if not category:

            category = categorize_transaction(
                merchant,
                amount
            )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description = str(
            transaction.get(
                "description",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        if transaction_exists(
            source,
            source_id
        ):

            duplicate_count += 1

            continue

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

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

    return (
        new_count,
        duplicate_count
    )


# ============================================================
# BUILD DASHBOARD
# ============================================================

def build_dashboard_result():

    # Make sure tables exist before querying.

    initialize_database()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    stats = get_dashboard_stats()

    # --------------------------------------------------------
    # Recent transactions
    # --------------------------------------------------------

    recent_rows = get_recent_transactions(
        20
    )

    recent = []

    for row in recent_rows:

        recent.append({

            "date": row[0],

            "merchant": row[1],

            "category": row[2],

            "amount": row[3]

        })

    # --------------------------------------------------------
    # Top merchants
    # --------------------------------------------------------

    merchants = get_top_merchants()

    # --------------------------------------------------------
    # Last update
    # --------------------------------------------------------

    last_update = get_last_update()

    # --------------------------------------------------------
    # Return complete dashboard
    # --------------------------------------------------------

    return {

        "stats": stats,

        "recent": recent,

        "merchants": merchants,

        "last_update": (
            last_update
            if last_update
            else "-"
        )
    }


# ============================================================
# PROCESS ONE UPLOADED FILE
# ============================================================

def analyze_uploaded_file(file_path):

    started_at = datetime.now().isoformat()

    try:

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        initialize_database()

        print()
        print("=" * 60)
        print("EXPENSE TRACKER")
        print("PROCESSING NEW FILE")
        print("=" * 60)

        print(
            "File:",
            file_path
        )

        # ----------------------------------------------------
        # READ FILE
        # ----------------------------------------------------

        transactions = read_uploaded_file(
            file_path
        )

        print(
            "Transactions found:",
            len(transactions)
        )

        # ----------------------------------------------------
        # CATEGORIZE
        # ----------------------------------------------------

        for transaction in transactions:

            merchant = transaction.get(
                "merchant",
                "Unknown"
            )

            amount = transaction.get(
                "amount",
                0
            )

            transaction["category"] = (
                categorize_transaction(
                    merchant,
                    amount
                )
            )

        # ----------------------------------------------------
        # SAVE NEW TRANSACTIONS
        # ----------------------------------------------------

        new_count, duplicate_count = (
            save_new_transactions(
                transactions
            )
        )

        # ----------------------------------------------------
        # FINISH TIME
        # ----------------------------------------------------

        finished_at = datetime.now().isoformat()

        # ----------------------------------------------------
        # SUCCESS LOG
        # ----------------------------------------------------

        log_update(

            started_at=started_at,

            finished_at=finished_at,

            status="SUCCESS",

            new_transactions=new_count,

            error=""
        )

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

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

        print("=" * 60)

        # ----------------------------------------------------
        # BUILD COMPLETE DASHBOARD
        # ----------------------------------------------------

        result = build_dashboard_result()

        # ----------------------------------------------------
        # UPLOAD MESSAGE
        # ----------------------------------------------------

        result["upload_message"] = (

            f"Added {new_count} new transaction(s). "

            f"Skipped {duplicate_count} duplicate(s). "

            "Existing expenses were kept."
        )

        return result

    except Exception as error:

        finished_at = datetime.now().isoformat()

        # ----------------------------------------------------
        # FAILED LOG
        # ----------------------------------------------------

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

        print()
        print(
            "UPLOAD ERROR:",
            str(error)
        )

        raise


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def run_update():

    """
    Kept for compatibility with older code.

    The current application processes files uploaded
    through the Flask website.

    It does NOT process a fixed Transactions.csv file.
    """

    raise RuntimeError(

        "run_update() is not used for uploaded files. "

        "Please upload a CSV or PDF through the website."
    )


# ============================================================
# TEST / DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print(
        "Expense Tracker update module loaded."
    )

    print(
        "Use the Flask website to upload a CSV or PDF."
    )