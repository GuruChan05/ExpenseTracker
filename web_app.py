from flask import Flask, render_template, redirect, url_for, flash
import os

from update_expenses import run_update

from database import (
    initialize_database,
    get_dashboard_stats,
    get_last_update
)

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "expense-tracker-secret"
)


# ======================================
# HOME PAGE
# ======================================

@app.route("/")
def dashboard():

    try:

        initialize_database()

        stats = get_dashboard_stats()

        last_update = get_last_update()

    except Exception as e:

        print("Dashboard Error:", e)

        stats = {
            "total_expenses": 0,
            "gpay_total": 0,
            "gmail_total": 0,
            "total_transactions": 0,
            "category_totals": [],
            "monthly_totals": []
        }

        last_update = None

    return render_template(
        "dashboard.html",
        stats=stats,
        last_update=last_update
    )


# ======================================
# UPDATE BUTTON
# ======================================

@app.route("/update", methods=["POST"])
def update():

    try:

        initialize_database()

        success = run_update()

        if success:

            flash(
                "Expenses updated successfully!",
                "success"
            )

        else:

            flash(
                "No new transactions found.",
                "error"
            )

    except Exception as e:

        print("Update Error:", e)

        flash(
            str(e),
            "error"
        )

    return redirect(url_for("dashboard"))


# ======================================
# HEALTH
# ======================================

@app.route("/health")
def health():

    return {
        "status": "running"
    }


# ======================================
# LOCAL RUN
# ======================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )