from collections import defaultdict
from html import escape
from datetime import datetime


def get_amount(transaction):

    try:
        return float(
            transaction.get("amount", 0)
        )
    except (ValueError, TypeError):
        return 0.0


def get_month(transaction):

    date_value = transaction.get(
        "date",
        ""
    )

    if not date_value:
        return "Unknown"

    date_text = str(date_value).strip()

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y"
    ]

    for date_format in formats:

        try:

            date_obj = datetime.strptime(
                date_text,
                date_format
            )

            return date_obj.strftime(
                "%B %Y"
            )

        except ValueError:
            continue

    try:

        date_obj = datetime.fromisoformat(
            date_text.replace("Z", "")
        )

        return date_obj.strftime(
            "%B %Y"
        )

    except ValueError:

        return "Unknown"


def generate_summary(transactions):

    total = 0

    category_totals = defaultdict(float)

    monthly_totals = defaultdict(float)

    for transaction in transactions:

        amount = get_amount(
            transaction
        )

        total += amount

        category = transaction.get(
            "category",
            "Other"
        )

        category_totals[
            category
        ] += amount

        month = get_month(
            transaction
        )

        monthly_totals[
            month
        ] += amount

    return (
        total,
        dict(category_totals),
        dict(monthly_totals)
    )


def generate_html(
    transactions,
    total,
    category_totals,
    monthly_totals
):

    # ---------------------------------
    # Transaction table
    # ---------------------------------

    rows = ""

    for transaction in transactions:

        date = escape(
            str(
                transaction.get(
                    "date",
                    ""
                )
            )
        )

        merchant = escape(
            str(
                transaction.get(
                    "merchant",
                    "Unknown"
                )
            )
        )

        amount = get_amount(
            transaction
        )

        category = escape(
            str(
                transaction.get(
                    "category",
                    "Other"
                )
            )
        )

        rows += f"""
        <tr>
            <td>{date}</td>
            <td>{merchant}</td>
            <td>₹{amount:,.2f}</td>
            <td>{category}</td>
        </tr>
        """

    # ---------------------------------
    # Category table
    # ---------------------------------

    category_rows = ""

    for category, amount in sorted(
        category_totals.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        category_rows += f"""
        <tr>
            <td>{escape(str(category))}</td>
            <td>₹{amount:,.2f}</td>
        </tr>
        """

    # ---------------------------------
    # Monthly table
    # ---------------------------------

    monthly_rows = ""

    for month, amount in sorted(
        monthly_totals.items()
    ):

        monthly_rows += f"""
        <tr>
            <td>{escape(str(month))}</td>
            <td>₹{amount:,.2f}</td>
        </tr>
        """

    # ---------------------------------
    # HTML
    # ---------------------------------

    html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Personal Expense Tracker</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background: #f4f6f8;
    color: #222;
}}

.container {{
    max-width: 1250px;
    margin: auto;
    padding: 40px 25px;
}}

.header {{
    text-align: center;
    margin-bottom: 35px;
}}

.header h1 {{
    font-size: 36px;
    margin-bottom: 8px;
}}

.header p {{
    color: #666;
    font-size: 16px;
}}

/* --------------------------------
   TOTAL SPENDING
-------------------------------- */

.total-card {{
    background: white;
    border-radius: 18px;
    padding: 40px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
}}

.total-label {{
    font-size: 20px;
    color: #666;
    margin-bottom: 12px;
}}

.total {{
    font-size: 64px;
    font-weight: 800;
    margin: 5px 0 15px;
}}

.total-description {{
    color: #777;
    font-size: 15px;
}}

/* --------------------------------
   CARDS
-------------------------------- */

.card {{
    background: white;
    padding: 30px;
    margin-bottom: 30px;
    border-radius: 16px;
    box-shadow: 0 3px 15px rgba(0,0,0,0.06);
}}

.card h2 {{
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 24px;
}}

/* --------------------------------
   TABLE
-------------------------------- */

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 14px;
    border-bottom: 1px solid #e5e5e5;
    text-align: left;
}}

th {{
    background: #f5f5f5;
    font-weight: bold;
}}

tr:hover {{
    background: #fafafa;
}}

/* --------------------------------
   CHART
-------------------------------- */

.chart {{
    text-align: center;
}}

.chart img {{
    max-width: 100%;
    width: 800px;
    margin-top: 10px;
}}

/* --------------------------------
   FOOTER
-------------------------------- */

.footer {{
    text-align: center;
    color: #777;
    padding: 20px;
}}

</style>

</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <h1>Personal Expense Tracker</h1>

        <p>
            Google Pay and Gmail transaction analysis
        </p>

    </div>


    <!-- TOTAL SPENDING -->

    <div class="total-card">

        <div class="total-label">
            Total Spending
        </div>

        <div class="total">
            ₹{total:,.2f}
        </div>

        <div class="total-description">

            Total Transactions:
            <strong>{len(transactions)}</strong>

        </div>

    </div>


    <!-- MONTHLY SPENDING -->

    <div class="card">

        <h2>Monthly Spending</h2>

        <table>

            <tr>
                <th>Month</th>
                <th>Total Spending</th>
            </tr>

            {monthly_rows}

        </table>

    </div>


    <!-- CATEGORY SPENDING -->

    <div class="card">

        <h2>Spending by Category</h2>

        <table>

            <tr>
                <th>Category</th>
                <th>Total Spending</th>
            </tr>

            {category_rows}

        </table>

    </div>


    <!-- CHART -->

    <div class="card chart">

        <h2>Expense Chart</h2>

        <img
            src="category_chart.png"
            alt="Spending by Category"
        >

    </div>


    <!-- TRANSACTIONS -->

    <div class="card">

        <h2>All Transactions</h2>

        <table>

            <tr>
                <th>Date</th>
                <th>Merchant</th>
                <th>Amount</th>
                <th>Category</th>
            </tr>

            {rows}

        </table>

    </div>


    <!-- FOOTER -->

    <div class="footer">

        Expense Tracker • Personal Financial Analysis

    </div>

</div>

</body>

</html>
"""

    with open(
        "output/report.html",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print(
        "\nHTML report generated successfully!"
    )