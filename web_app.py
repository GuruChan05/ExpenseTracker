from flask import Flask, render_template, redirect, url_for, flash
from update_expenses import run_update
from database import get_dashboard_stats, get_last_update
import os

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "expense-tracker-secret"
)


@app.route("/")
def dashboard():

    stats = get_dashboard_stats()
    last_update = get_last_update()

    return render_template(
        "dashboard.html",
        stats=stats,
        last_update=last_update
    )


@app.route("/update", methods=["POST"])
def update():

    print("\n====================================")
    print("MANUAL UPDATE REQUESTED")
    print("====================================")

    try:

        success = run_update()

        if success:
            flash(
                "Expense data updated successfully!",
                "success"
            )
        else:
            flash(
                "Expense update failed. Check terminal.",
                "error"
            )

    except Exception as error:

        print("\nUPDATE ERROR:")
        print(error)

        flash(
            f"Update failed: {error}",
            "error"
        )

    return redirect(url_for("dashboard"))


if __name__ == "__main__":

    print("====================================")
    print("   EXPENSE TRACKER WEB APP")
    print("====================================")
    print("Starting Flask server...")
    print("Open: http://127.0.0.1:5000")
    print("====================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )