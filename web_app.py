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

from database import (
    initialize_database,
    get_dashboard_stats,
    get_last_update
)

from update_expenses import run_update

app = Flask(__name__)
app.secret_key = "expense-tracker-secret"


# ===============================
# HOME PAGE
# ===============================

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


# ===============================
# UPLOAD + UPDATE
# ===============================

@app.route("/update", methods=["POST"])
def update():

    file = request.files.get("expense_file")

    if not file:

        flash("Please choose a file.")

        return redirect("/")

    upload_folder = os.path.join(
        tempfile.gettempdir(),
        "uploads"
    )

    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(
        upload_folder,
        file.filename
    )

    file.save(file_path)

    success = run_update(file_path)

    if success:

        flash("Expense updated successfully!")

    else:

        flash("No new transaction found.")

    return redirect("/")


# ===============================
# HEALTH CHECK
# ===============================

@app.route("/health")
def health():
    return {"status": "running"}


# ===============================
# LOCAL RUN
# ===============================

if __name__ == "__main__":

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )