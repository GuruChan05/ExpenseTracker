from flask import Flask, render_template, request, redirect, url_for, flash
import os
import tempfile
from werkzeug.utils import secure_filename

from update_expenses import (
    analyze_uploaded_file,
    build_dashboard_result
)

from database import initialize_database


app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "expense-tracker-secret"
)

ALLOWED_EXTENSIONS = {".csv", ".pdf"}


def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# Initialize the permanent local database when the app starts.
initialize_database()


@app.route("/")
def home():
    result = build_dashboard_result()

    return render_template(
        "dashboard.html",
        stats=result["stats"],
        recent=result["recent"],
        merchants=result["merchants"],
        last_update=result["last_update"],
        upload_message=None
    )


@app.route("/update", methods=["POST"])
def update():
    file = request.files.get("expense_file")

    if file is None or not file.filename:
        flash("Please select a CSV or PDF file.", "error")
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        flash(
            "Unsupported file. Please upload CSV or PDF.",
            "error"
        )
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)

    # Temporary location is only used while reading this upload.
    # The transactions themselves are saved permanently in the DB.
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    try:
        file.save(file_path)

        result = analyze_uploaded_file(file_path)

        flash(
            result.get(
                "upload_message",
                "File processed successfully."
            ),
            "success"
        )

        return redirect(url_for("home"))

    except Exception as error:
        flash(
            f"Upload failed: {error}",
            "error"
        )
        return redirect(url_for("home"))

    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
