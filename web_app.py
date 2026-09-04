from flask import Flask, render_template, request
import os
import tempfile

from update_expenses import analyze_uploaded_file

app = Flask(__name__)

app.secret_key = "expense-tracker"

# Empty dashboard
EMPTY_STATS = {
    "total_expense": 0,
    "total_transactions": 0,
    "category_totals": [],
    "monthly_totals": []
}

@app.route("/")
def home():

    return render_template(
        "dashboard.html",
        stats=EMPTY_STATS,
        recent=[],
        merchants=[],
        last_update="-"
    )


@app.route("/update", methods=["POST"])
def update():

    file = request.files.get("expense_file")

    if not file:
        return "No file uploaded"

    temp_dir = tempfile.gettempdir()

    file_path = os.path.join(
        temp_dir,
        file.filename
    )

    file.save(file_path)

    result = analyze_uploaded_file(file_path)

    return render_template(
        "dashboard.html",
        stats=result["stats"],
        recent=result["recent"],
        merchants=result["merchants"],
        last_update=result["last_update"]
    )


if __name__ == "__main__":

    app.run(debug=True)