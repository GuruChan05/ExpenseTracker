import pdfplumber
import re

def extract_transactions_from_pdf(path):

    data = []

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            for line in text.split("\n"):

                amount = re.search(
                    r'₹\s*([\d,]+\.\d{2})',
                    line
                )

                if not amount:
                    continue

                merchant = line.split("₹")[0].strip()

                value = float(
                    amount.group(1).replace(",", "")
                )

                data.append({

                    "source":"Google Pay",

                    "date":"2026-09",

                    "merchant":merchant,

                    "amount":value

                })

    return data