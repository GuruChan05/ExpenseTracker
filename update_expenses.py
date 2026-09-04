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


def analyze_uploaded_file(file_path):

    ext = os.path.splitext(file_path)[1].lower()

    # ----------------------------
    # CSV
    # ----------------------------

    if ext == ".csv":

        df = read_gpay_transactions(file_path)

        transactions = clean_gpay_transactions(df)

    # ----------------------------
    # PDF
    # ----------------------------

    elif ext == ".pdf":

        transactions = extract_transactions_from_pdf(
            file_path
        )

    else:

        transactions = []

    # ----------------------------
    # Categorize
    # ----------------------------

    for t in transactions:

        t["category"] = categorize_transaction(
            t["merchant"],
            t["amount"]
        )

    # ----------------------------
    # Total
    # ----------------------------

    total = sum(
        t["amount"] for t in transactions
    )

    # ----------------------------
    # Category
    # ----------------------------

    category = defaultdict(float)

    for t in transactions:

        category[
            t["category"]
        ] += t["amount"]

    category_totals = list(category.items())

    # ----------------------------
    # Monthly
    # ----------------------------

    monthly = defaultdict(float)

    for t in transactions:

        month = t["date"][:7]

        monthly[month] += t["amount"]

    monthly_totals = list(monthly.items())

    # ----------------------------
    # Merchant
    # ----------------------------

    merchant = defaultdict(float)

    for t in transactions:

        merchant[
            t["merchant"]
        ] += t["amount"]

    merchants = sorted(
        merchant.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    recent = sorted(
        transactions,
        key=lambda x: x["date"],
        reverse=True
    )[:10]

    stats = {

        "total_expense": total,

        "total_transactions": len(transactions),

        "category_totals": category_totals,

        "monthly_totals": monthly_totals

    }

    return {

        "stats": stats,

        "recent": recent,

        "merchants": merchants,

        "last_update": datetime.now().strftime(
            "%d-%m-%Y %H:%M"
        )

    }