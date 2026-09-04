import pdfplumber
import re
from datetime import datetime

def extract_transactions_from_pdf(pdf_path):

    transactions = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                # Find amount
                amount_match = re.search(
                    r'₹\s*([\d,]+\.\d{2})',
                    line
                )

                if not amount_match:
                    continue

                amount = float(
                    amount_match.group(1).replace(",", "")
                )

                # Find date
                date_match = re.search(
                    r'(\d{2}/\d{2}/\d{4})',
                    line
                )

                if date_match:
                    date = datetime.strptime(
                        date_match.group(1),
                        "%d/%m/%Y"
                    ).strftime("%Y-%m-%d")
                else:
                    date = ""

                # Merchant
                merchant = line.split("₹")[0].strip()

                transactions.append({

                    "source": "Google Pay",

                    "date": date,

                    "merchant": merchant,

                    "amount": amount

                })

    return transactions