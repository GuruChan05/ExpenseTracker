from parser import (
    read_gpay_transactions,
    read_gmail_transactions,
    clean_gpay_transactions
)

from categorizer import categorize_transaction

from report import (
    generate_summary,
    generate_html
)

from charts.chart import generate_chart


# ============================================================
# REMOVE DUPLICATE TRANSACTIONS
# ============================================================

def remove_duplicate_transactions(transactions):

    unique_transactions = []
    seen = set()

    for transaction in transactions:

        merchant = str(
            transaction.get(
                "merchant",
                "Unknown"
            )
        ).strip().lower()

        amount = transaction.get(
            "amount",
            0
        )

        try:
            amount = round(
                float(amount),
                2
            )
        except (ValueError, TypeError):
            continue

        date = str(
            transaction.get(
                "date",
                ""
            )
        ).strip()

        # Use only YYYY-MM-DD where possible
        date_key = date[:10]

        # ----------------------------------------------------
        # Duplicate key
        # ----------------------------------------------------

        key = (
            date_key,
            merchant,
            amount
        )

        if key in seen:
            continue

        seen.add(key)

        unique_transactions.append(
            transaction
        )

    return unique_transactions


# ============================================================
# CALCULATE EXACT TOTAL
# ============================================================

def calculate_total(transactions):

    total = 0.0

    for transaction in transactions:

        try:

            amount = float(
                transaction.get(
                    "amount",
                    0
                )
            )

            if amount > 0:
                total += amount

        except (ValueError, TypeError):

            continue

    return round(
        total,
        2
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n====================================")
    print("       EXPENSE TRACKER")
    print("====================================")

    # ========================================================
    # FILE LOCATIONS
    # ========================================================

    csv_file = "data/Transactions.csv"
    gmail_file = "data/gmail.mbox"

    # ========================================================
    # 1. READ GOOGLE PAY CSV
    # ========================================================

    print("\n====================================")
    print("1. GOOGLE PAY")
    print("====================================")

    try:

        gpay_df = read_gpay_transactions(
            csv_file
        )

        print(
            "Google Pay CSV loaded successfully."
        )

        print(
            "Google Pay rows:",
            len(gpay_df)
        )

    except Exception as error:

        print(
            "\nERROR reading Google Pay CSV:"
        )

        print(error)

        return

    # ========================================================
    # 2. CLEAN GOOGLE PAY
    # ========================================================

    print("\n====================================")
    print("2. CLEANING GOOGLE PAY")
    print("====================================")

    try:

        gpay_transactions = (
            clean_gpay_transactions(
                gpay_df
            )
        )

        print(
            "Valid Google Pay transactions:",
            len(gpay_transactions)
        )

    except Exception as error:

        print(
            "\nERROR cleaning Google Pay:"
        )

        print(error)

        return

    # ========================================================
    # 3. READ GMAIL
    # ========================================================

    print("\n====================================")
    print("3. GMAIL")
    print("====================================")

    try:

        gmail_transactions = (
            read_gmail_transactions(
                gmail_file
            )
        )

        if gmail_transactions is None:
            gmail_transactions = []

        print(
            "Valid Gmail payment transactions:",
            len(gmail_transactions)
        )

    except FileNotFoundError:

        print(
            "Gmail MBOX file not found."
        )

        print(
            "Continuing with Google Pay only."
        )

        gmail_transactions = []

    except Exception as error:

        print(
            "\nERROR reading Gmail:"
        )

        print(error)

        print(
            "Continuing with Google Pay only."
        )

        gmail_transactions = []

    # ========================================================
    # 4. COMBINE BOTH SOURCES
    # ========================================================

    print("\n====================================")
    print("4. COMBINING TRANSACTIONS")
    print("====================================")

    all_transactions = []

    all_transactions.extend(
        gpay_transactions
    )

    all_transactions.extend(
        gmail_transactions
    )

    print(
        "Google Pay transactions:",
        len(gpay_transactions)
    )

    print(
        "Gmail transactions:",
        len(gmail_transactions)
    )

    print(
        "Combined transactions:",
        len(all_transactions)
    )

    # ========================================================
    # 5. REMOVE DUPLICATES
    # ========================================================

    print("\n====================================")
    print("5. REMOVING DUPLICATES")
    print("====================================")

    before_duplicate_removal = len(
        all_transactions
    )

    all_transactions = (
        remove_duplicate_transactions(
            all_transactions
        )
    )

    after_duplicate_removal = len(
        all_transactions
    )

    duplicates_removed = (
        before_duplicate_removal
        - after_duplicate_removal
    )

    print(
        "Transactions before duplicate removal:",
        before_duplicate_removal
    )

    print(
        "Duplicates removed:",
        duplicates_removed
    )

    print(
        "Final transactions:",
        after_duplicate_removal
    )

    # ========================================================
    # CHECK DATA
    # ========================================================

    if not all_transactions:

        print(
            "\nNo valid expense transactions found."
        )

        return

    # ========================================================
    # 6. DISPLAY TRANSACTIONS
    # ========================================================

    print("\n====================================")
    print("6. FINAL TRANSACTIONS")
    print("====================================")

    for index, transaction in enumerate(
        all_transactions,
        start=1
    ):

        merchant = transaction.get(
            "merchant",
            "Unknown"
        )

        amount = transaction.get(
            "amount",
            0
        )

        source = transaction.get(
            "source",
            "Unknown"
        )

        date = transaction.get(
            "date",
            ""
        )

        print(
            f"{index}. "
            f"{date} | "
            f"{merchant} | "
            f"₹{float(amount):,.2f} | "
            f"{source}"
        )

    # ========================================================
    # 7. AI CATEGORIZATION
    # ========================================================

    print("\n====================================")
    print("7. AI CATEGORIZATION")
    print("====================================")

    total_transactions = len(
        all_transactions
    )

    for index, transaction in enumerate(
        all_transactions,
        start=1
    ):

        merchant = transaction.get(
            "merchant",
            "Unknown"
        )

        amount = transaction.get(
            "amount",
            0
        )

        print(
            f"\n[{index}/{total_transactions}] "
            f"Categorizing: {merchant}"
        )

        try:

            category = (
                categorize_transaction(
                    merchant,
                    amount
                )
            )

            if not category:
                category = "Other"

        except KeyboardInterrupt:

            print(
                "\nCategorization stopped by user."
            )

            return

        except Exception as error:

            print(
                "Categorization error:"
            )

            print(error)

            category = "Other"

        transaction["category"] = (
            category
        )

        print(
            f"    Category: {category}"
        )

    # ========================================================
    # 8. EXACT TOTAL
    # ========================================================

    print("\n====================================")
    print("8. EXPENSE TOTAL")
    print("====================================")

    exact_total = calculate_total(
        all_transactions
    )

    print(
        f"\nEXACT TOTAL SPENDING: "
        f"₹{exact_total:,.2f}"
    )

    # ========================================================
    # 9. GENERATE SUMMARY
    # ========================================================

    print("\n====================================")
    print("9. EXPENSE SUMMARY")
    print("====================================")

    try:

        total, category_totals, monthly_totals = (
            generate_summary(
                all_transactions
            )
        )

    except Exception as error:

        print(
            "ERROR generating summary:"
        )

        print(error)

        return

    # Use our independently calculated exact total
    # so the final report does not accidentally include
    # invalid/extra values.

    total = exact_total

    # ========================================================
    # MONTHLY TOTALS
    # ========================================================

    print("\nMonthly Spending:")

    if monthly_totals:

        for month, amount in sorted(
            monthly_totals.items()
        ):

            print(
                f"{month}: ₹{float(amount):,.2f}"
            )

    else:

        print(
            "No monthly data available."
        )

    # ========================================================
    # CATEGORY TOTALS
    # ========================================================

    print("\nCategory-wise Spending:")

    if category_totals:

        for category, amount in sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        ):

            print(
                f"{category}: "
                f"₹{float(amount):,.2f}"
            )

    else:

        print(
            "No category data available."
        )

    # ========================================================
    # 10. GENERATE CHART
    # ========================================================

    print("\n====================================")
    print("10. GENERATING CHART")
    print("====================================")

    try:

        generate_chart(
            category_totals
        )

        print(
            "Category chart generated successfully!"
        )

    except Exception as error:

        print(
            "ERROR generating chart:"
        )

        print(error)

    # ========================================================
    # 11. GENERATE HTML
    # ========================================================

    print("\n====================================")
    print("11. GENERATING HTML REPORT")
    print("====================================")

    try:

        generate_html(
            all_transactions,
            total,
            category_totals,
            monthly_totals
        )

        print(
            "HTML report generated successfully!"
        )

    except Exception as error:

        print(
            "ERROR generating HTML report:"
        )

        print(error)

        return

    # ========================================================
    # 12. FINAL RESULT
    # ========================================================

    print("\n====================================")
    print("       PROCESS COMPLETED")
    print("====================================")

    print(
        f"Google Pay transactions: "
        f"{len(gpay_transactions)}"
    )

    print(
        f"Gmail transactions: "
        f"{len(gmail_transactions)}"
    )

    print(
        f"Duplicates removed: "
        f"{duplicates_removed}"
    )

    print(
        f"Final transactions: "
        f"{len(all_transactions)}"
    )

    print(
        f"TOTAL SPENDING: "
        f"₹{total:,.2f}"
    )

    print("\nGenerated files:")

    print(
        "1. output/category_chart.png"
    )

    print(
        "2. output/report.html"
    )

    print("\nOpen the report using:")

    print(
        "start output\\report.html"
    )

    print("\n====================================")
    print("          DONE")
    print("====================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()