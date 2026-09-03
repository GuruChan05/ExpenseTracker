from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
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

# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def dashboard():

    initialize_database()

    stats = get_dashboard_stats()

    last_update = get_last_update()

    return render_template(
        "dashboard.html",
        stats=stats,
        last_update=last_update
    )

# ==========================================
# UPLOAD + UPDATE (ONE REQUEST)
# ==========================================

@app.route("/update", methods=["POST"])
def update():

    file = request.files.get("csv_file")

    if file is None or file.filename == "":

        flash(
            "Please choose a Google Pay CSV.",
            "error"
        )

        return redirect(url_for("dashboard"))

    upload_dir = os.path.join(
        tempfile.gettempdir(),
        "uploads"
    )

    os.makedirs(upload_dir, exist_ok=True)

    csv_path = os.path.join(
        upload_dir,
        "Transactions.csv"
    )

    file.save(csv_path)

    success = run_update(csv_path)

    if success:

        flash(
            "New transactions imported successfully!",
            "success"
        )

    else:

        flash(
            "No new transactions found.",
            "warning"
        )

    return redirect(url_for("dashboard"))

# ==========================================
# HEALTH
# ==========================================

@app.route("/health")
def health():

    return {
        "status": "running"
    }

# ==========================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )