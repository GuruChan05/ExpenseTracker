from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

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

# Folder to store uploaded CSV
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def dashboard():

    try:

        initialize_database()

        stats = get_dashboard_stats()

        last_update = get_last_update()

    except Exception as error:

        print("Dashboard Error:", error)

        stats = {
            "total_expenses": 0,
            "total_transactions": 0,
            "gpay_total": 0,
            "gmail_total": 0,
            "category_totals": [],
            "monthly_totals": []
        }

        last_update = None

    return render_template(
        "dashboard.html",
        stats=stats,
        last_update=last_update
    )


# ==========================================
# UPLOAD GOOGLE PAY CSV
# ==========================================

@app.route("/upload", methods=["POST"])
def upload_csv():

    if "csv_file" not in request.files:

        flash("Please choose a CSV file.", "error")

        return redirect(url_for("dashboard"))

    file = request.files["csv_file"]

    if file.filename == "":

        flash("No file selected.", "error")

        return redirect(url_for("dashboard"))

    save_path = os.path.join(
        UPLOAD_FOLDER,
        "Transactions.csv"
    )

    file.save(save_path)

    flash(
        "Google Pay CSV uploaded successfully!",
        "success"
    )

    print("CSV Saved:", save_path)

    return redirect(url_for("dashboard"))


# ==========================================
# UPDATE EXPENSES
# ==========================================

@app.route("/update", methods=["POST"])
def update():

    print("\n====================================")
    print("MANUAL UPDATE REQUESTED")
    print("====================================")

    try:

        initialize_database()

        success = run_update()

        if success:

            flash(
                "Expense data updated successfully!",
                "success"
            )

        else:

            flash(
                "No new transactions found.",
                "error"
            )

    except Exception as error:

        print("Update Error:", error)

        flash(
            f"Update failed: {error}",
            "error"
        )

    return redirect(url_for("dashboard"))


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return {
        "status": "running",
        "platform": "vercel" if os.getenv("VERCEL") else "local"
    }


# ==========================================
# RUN LOCALLY
# ==========================================

if __name__ == "__main__":

    print("====================================")
    print("   EXPENSE TRACKER WEB APP")
    print("====================================")
    print("Starting Flask Server...")
    print("http://127.0.0.1:5000")
    print("====================================")

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )