from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

import os
import tempfile

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

# ==================================================
# UPLOAD FOLDER (LOCAL + VERCEL)
# ==================================================

if os.getenv("VERCEL"):
    UPLOAD_FOLDER = os.path.join(
        tempfile.gettempdir(),
        "uploads"
    )
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "uploads"
    )

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==================================================
# HOME PAGE
# ==================================================

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

# ==================================================
# CSV UPLOAD
# ==================================================

@app.route("/upload", methods=["POST"])
def upload_csv():

    file = request.files.get("csv_file")

    if file is None or file.filename == "":

        flash(
            "Please select a CSV file.",
            "error"
        )

        return redirect(url_for("dashboard"))

    save_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "Transactions.csv"
    )

    file.save(save_path)

    flash(
        "Google Pay CSV uploaded successfully!",
        "success"
    )

    return redirect(url_for("dashboard"))

# ==================================================
# UPDATE EXPENSES
# ==================================================

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

    except Exception as error:

        print("Update Error:", error)

        flash(
            str(error),
            "error"
        )

    return redirect(url_for("dashboard"))

# ==================================================
# HEALTH CHECK
# ==================================================

@app.route("/health")
def health():

    return {
        "status": "running",
        "platform": "vercel"
        if os.getenv("VERCEL")
        else "local"
    }

# ==================================================
# LOCAL RUN
# ==================================================

if __name__ == "__main__":

    initialize_database()

    print("=" * 40)
    print("EXPENSE TRACKER WEB APP")
    print("=" * 40)
    print("Upload Folder:", UPLOAD_FOLDER)
    print("http://127.0.0.1:5000")
    print("=" * 40)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )