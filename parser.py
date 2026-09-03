import pandas as pd
import mailbox
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime


# ============================================================
# AMOUNT CLEANING
# ============================================================

def clean_amount(value):
    """
    Convert different currency formats into an exact float.

    Examples:
        INR 29.00
        INR\xa029.00
        ₹29.00
        Rs. 29.00
        1,299.50
    """

    if value is None:
        return 0.0

    try:
        if pd.isna(value):
            return 0.0
    except Exception:
        pass

    amount_text = str(value).strip()

    # Remove currency labels/symbols
    amount_text = (
        amount_text
        .replace("₹", "")
        .replace("INR", "")
        .replace("inr", "")
        .replace("Rs.", "")
        .replace("RS.", "")
        .replace("Rs", "")
        .replace("RS", "")
    )

    # IMPORTANT:
    # Google Pay may use a non-breaking space \xa0
    amount_text = (
        amount_text
        .replace("\xa0", "")
        .replace("\u2007", "")
        .replace("\u202f", "")
        .replace(" ", "")
        .replace(",", "")
        .strip()
    )

    # Keep only valid numeric characters
    amount_text = re.sub(
        r"[^0-9.\-]",
        "",
        amount_text
    )

    try:
        return float(amount_text)

    except (ValueError, TypeError):
        print(
            f"Could not convert amount: {repr(value)}"
        )
        return 0.0


# ============================================================
# READ GOOGLE PAY CSV
# ============================================================

def read_gpay_transactions(csv_file):

    print("Reading Google Pay CSV...")

    df = pd.read_csv(
        csv_file
    )

    print("CSV Read Successfully!")

    print(
        "Google Pay Rows:",
        len(df)
    )

    print(
        "Columns:",
        list(df.columns)
    )

    return df


# ============================================================
# DECODE EMAIL SUBJECT
# ============================================================

def decode_subject(subject):

    if not subject:
        return ""

    decoded_parts = []

    try:

        for part, encoding in decode_header(subject):

            if isinstance(part, bytes):

                try:

                    decoded_parts.append(
                        part.decode(
                            encoding or "utf-8",
                            errors="replace"
                        )
                    )

                except Exception:

                    decoded_parts.append(
                        part.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

            else:

                decoded_parts.append(
                    str(part)
                )

    except Exception:

        return str(subject)

    return "".join(
        decoded_parts
    )


# ============================================================
# GET EMAIL BODY
# ============================================================

def get_email_body(message):

    # --------------------------------------------------------
    # Multipart email
    # --------------------------------------------------------

    if message.is_multipart():

        # Prefer text/plain
        for part in message.walk():

            if (
                part.get_content_type()
                == "text/plain"
            ):

                try:

                    payload = part.get_payload(
                        decode=True
                    )

                    if payload:

                        return payload.decode(
                            part.get_content_charset()
                            or "utf-8",
                            errors="replace"
                        )

                except Exception:
                    pass

        # Fallback to text/html
        for part in message.walk():

            if (
                part.get_content_type()
                == "text/html"
            ):

                try:

                    payload = part.get_payload(
                        decode=True
                    )

                    if payload:

                        html = payload.decode(
                            part.get_content_charset()
                            or "utf-8",
                            errors="replace"
                        )

                        # Remove HTML tags
                        text = re.sub(
                            r"<[^>]+>",
                            " ",
                            html
                        )

                        return text

                except Exception:
                    pass

    # --------------------------------------------------------
    # Non-multipart email
    # --------------------------------------------------------

    else:

        try:

            payload = message.get_payload(
                decode=True
            )

            if payload:

                return payload.decode(
                    message.get_content_charset()
                    or "utf-8",
                    errors="replace"
                )

        except Exception:
            pass

    return ""


# ============================================================
# EXTRACT CURRENCY AMOUNTS
# ============================================================

def extract_currency_amounts(text):
    """
    Extract currency values from email text.

    Handles:
        ₹29.00
        INR 29.00
        INR\xa029.00
        Rs 29.00
        Rs. 29.00
    """

    if not text:
        return []

    patterns = [

        r"(?:₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",

        r"(?:INR)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",

        r"(?:Rs\.?)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)"

    ]

    amounts = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            try:

                amount = float(
                    value.replace(",", "")
                )

                if amount > 0:

                    amounts.append(
                        amount
                    )

            except ValueError:
                continue

    return amounts


# ============================================================
# EXTRACT EXACT PAYMENT AMOUNT
# ============================================================

def extract_amount(text):

    """
    Find the most likely actual payment amount.

    First looks for amounts close to payment/debit words.
    This prevents promotional prices from being treated
    as expenses.
    """

    if not text:
        return None

    # --------------------------------------------------------
    # Normalize non-breaking spaces
    # --------------------------------------------------------

    normalized_text = (
        text
        .replace("\xa0", " ")
        .replace("\u2007", " ")
        .replace("\u202f", " ")
    )

    # --------------------------------------------------------
    # Payment/debit sentence patterns
    # --------------------------------------------------------

    payment_patterns = [

        # ₹ 120 / INR 120 near paid
        r"(?:paid|pay|payment(?:\s+of)?|debit(?:ed)?|debited)"
        r".{0,80}?"
        r"(?:₹|INR|Rs\.?)\s*"
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)",

        # Amount first, payment word later
        r"(?:₹|INR|Rs\.?)\s*"
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
        r".{0,80}?"
        r"(?:paid|payment|debited|debit)",

        # "amount of INR 120"
        r"(?:amount|total|value)"
        r".{0,30}?"
        r"(?:₹|INR|Rs\.?)\s*"
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)",

        # UPI amount
        r"(?:upi)"
        r".{0,100}?"
        r"(?:₹|INR|Rs\.?)\s*"
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"

    ]

    candidates = []

    for pattern in payment_patterns:

        matches = re.findall(
            pattern,
            normalized_text,
            re.IGNORECASE |
            re.DOTALL
        )

        for value in matches:

            try:

                amount = float(
                    value.replace(",", "")
                )

                if amount > 0:

                    candidates.append(
                        amount
                    )

            except ValueError:
                continue

    # Remove duplicates while preserving order
    unique_candidates = list(
        dict.fromkeys(candidates)
    )

    # If exactly one payment-related amount exists
    if len(unique_candidates) == 1:

        return unique_candidates[0]

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    # If there is only one currency amount anywhere
    # in the email, it is reasonably safe to use it.
    all_amounts = extract_currency_amounts(
        normalized_text
    )

    unique_all_amounts = list(
        dict.fromkeys(all_amounts)
    )

    if len(unique_all_amounts) == 1:

        return unique_all_amounts[0]

    # Multiple amounts = don't guess
    return None


# ============================================================
# NON-EXPENSE EMAIL DETECTION
# ============================================================

def is_non_expense(text):

    if not text:
        return True

    text = text.lower()

    non_expense_keywords = [

        # Salary
        "salary credited",
        "salary credit",
        "salary received",
        "salary has been credited",

        # Stipend
        "stipend credited",
        "stipend credit",
        "stipend received",

        # Credit / incoming money
        "amount credited",
        "amount has been credited",
        "money credited",
        "money received",
        "funds received",
        "credit received",
        "credited to your account",
        "credited to your a/c",

        # Refund
        "refund received",
        "refund credited",
        "refund processed",
        "refund has been initiated",
        "amount refunded",

        # Cashback
        "cashback received",
        "cashback credited",
        "cashback added",

        # Offers
        "special offer",
        "limited time offer",
        "exclusive offer",
        "discount",
        "coupon",
        "promo code",
        "promotional offer",
        "sale is back",
        "unbeatable value",
        "best price",
        "shop now",
        "buy now",
        "save up to",
        "flat off",

        # Authentication
        "otp",
        "one time password",
        "verification code",
        "security code",

        # Account/security
        "password reset",
        "password changed",
        "login alert",
        "new sign-in",
        "new login",

        # Social/newsletters
        "unsubscribe",
        "newsletter",
        "job alert",
        "internship alert",
        "notification",

        # Delivery failure
        "delivery status notification",
        "mail delivery failed",
        "message delivery failed"
    ]

    return any(
        keyword in text
        for keyword in non_expense_keywords
    )


# ============================================================
# PAYMENT EMAIL DETECTION
# ============================================================

def is_payment_email(text):

    if not text:
        return False

    text = text.lower()

    payment_keywords = [

        # General payment
        "payment",
        "paid",
        "payment made",
        "payment successful",
        "payment completed",
        "payment confirmation",
        "payment receipt",
        "payment of",

        # Debit
        "debited",
        "debit",
        "amount debited",
        "amount has been debited",
        "account debited",
        "a/c debited",
        "debited from your account",
        "debited from your a/c",

        # Transactions
        "transaction",
        "transaction successful",
        "transaction completed",
        "transaction id",
        "transaction reference",

        # Purchase
        "purchase",
        "purchase successful",
        "purchase completed",
        "order placed",
        "order confirmed",
        "order confirmation",
        "receipt",

        # UPI
        "upi",
        "upi payment",
        "upi transaction",

        # Payment platforms
        "google pay",
        "googlepay",
        "gpay",
        "phonepe",
        "paytm",
        "razorpay",

        # Common merchants
        "swiggy",
        "zomato",
        "amazon",
        "flipkart",
        "myntra",
        "meesho",
        "ola",
        "uber",
        "rapido",
        "blinkit",
        "zepto",
        "bigbasket"
    ]

    return any(
        keyword in text
        for keyword in payment_keywords
    )


# ============================================================
# FIND MERCHANT
# ============================================================

def find_merchant(text):

    if not text:
        return "Unknown"

    text = text.lower()

    merchant_names = {

        "swiggy": "Swiggy",
        "zomato": "Zomato",

        "amazon": "Amazon",
        "flipkart": "Flipkart",
        "myntra": "Myntra",
        "meesho": "Meesho",

        "uber": "Uber",
        "ola": "Ola",
        "rapido": "Rapido",

        "razorpay": "Razorpay",
        "paytm": "Paytm",
        "phonepe": "PhonePe",

        "google pay": "Google Pay",
        "googlepay": "Google Pay",
        "gpay": "Google Pay",

        "blinkit": "Blinkit",
        "zepto": "Zepto",
        "bigbasket": "BigBasket",

        "netflix": "Netflix",
        "spotify": "Spotify",

        "airtel": "Airtel",
        "jio": "Jio",
        "amazon pay": "Amazon Pay"
    }

    for keyword, merchant in merchant_names.items():

        if keyword in text:

            return merchant

    return "Unknown"


# ============================================================
# GET EMAIL DATE
# ============================================================

def get_email_date(message):

    email_date = message.get(
        "date",
        ""
    )

    if not email_date:
        return ""

    try:

        parsed_date = parsedate_to_datetime(
            email_date
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except Exception:

        return email_date


# ============================================================
# READ GMAIL TRANSACTIONS
# ============================================================

def read_gmail_transactions(mbox_file):

    print(
        "\nReading Gmail payment emails..."
    )

    gmail_transactions = []

    try:

        mbox = mailbox.mbox(
            mbox_file
        )

    except Exception as error:

        print(
            "ERROR opening Gmail MBOX:"
        )

        print(error)

        return []

    total_emails = 0

    skipped_non_expense = 0
    skipped_not_payment = 0
    skipped_no_amount = 0

    for message in mbox:

        total_emails += 1

        # ----------------------------------------------------
        # Subject
        # ----------------------------------------------------

        subject = decode_subject(
            message.get(
                "subject",
                ""
            )
        )

        # ----------------------------------------------------
        # Body
        # ----------------------------------------------------

        body = get_email_body(
            message
        )

        # ----------------------------------------------------
        # Combined content
        # ----------------------------------------------------

        combined_text = (
            subject
            + "\n"
            + body
        )

        text_lower = combined_text.lower()

        # ----------------------------------------------------
        # Ignore non-expense messages
        # ----------------------------------------------------

        if is_non_expense(
            text_lower
        ):

            skipped_non_expense += 1

            continue

        # ----------------------------------------------------
        # Must look like payment
        # ----------------------------------------------------

        if not is_payment_email(
            text_lower
        ):

            skipped_not_payment += 1

            continue

        # ----------------------------------------------------
        # Extract exact amount
        # ----------------------------------------------------

        amount = extract_amount(
            combined_text
        )

        if amount is None:

            skipped_no_amount += 1

            continue

        if amount <= 0:

            skipped_no_amount += 1

            continue

        # ----------------------------------------------------
        # Merchant
        # ----------------------------------------------------

        merchant = find_merchant(
            text_lower
        )

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        date_value = get_email_date(
            message
        )

        # ----------------------------------------------------
        # Store transaction
        # ----------------------------------------------------

        gmail_transactions.append({

            "date": date_value,

            "merchant": merchant,

            "amount": float(
                amount
            ),

            "source": "Gmail",

            "description": subject

        })

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\nGmail scanning completed."
    )

    print(
        "Total Gmail emails:",
        total_emails
    )

    print(
        "Ignored non-expense emails:",
        skipped_non_expense
    )

    print(
        "Ignored non-payment emails:",
        skipped_not_payment
    )

    print(
        "Ignored emails with unclear amount:",
        skipped_no_amount
    )

    print(
        "Gmail payment transactions:",
        len(gmail_transactions)
    )

    gmail_total = sum(
        transaction["amount"]
        for transaction in gmail_transactions
    )

    print(
        f"Gmail expense total: ₹{gmail_total:,.2f}"
    )

    return gmail_transactions


# ============================================================
# CLEAN GOOGLE PAY TRANSACTIONS
# ============================================================

def clean_gpay_transactions(df):

    transactions = []

    print(
        "\nProcessing Google Pay transactions..."
    )

    if df is None:

        return []

    if len(df) == 0:

        return []

    for _, row in df.iterrows():

        # ----------------------------------------------------
        # EXACT GPay amount
        # ----------------------------------------------------

        amount = clean_amount(
            row.get(
                "Amount",
                0
            )
        )

        if amount <= 0:

            continue

        # ----------------------------------------------------
        # Description / merchant
        # ----------------------------------------------------

        description = str(
            row.get(
                "Description",
                "Unknown"
            )
        ).strip()

        if not description:

            description = "Unknown"

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = str(
            row.get(
                "Status",
                ""
            )
        ).strip()

        status_lower = status.lower()

        # Ignore only clearly failed/cancelled transactions
        if any(
            word in status_lower
            for word in [
                "failed",
                "cancelled",
                "canceled",
                "declined"
            ]
        ):

            continue

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        date_value = str(
            row.get(
                "Time",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        product = str(
            row.get(
                "Product",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Payment method
        # ----------------------------------------------------

        payment_method = str(
            row.get(
                "Payment method",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Transaction ID
        # ----------------------------------------------------

        transaction_id = str(
            row.get(
                "Transaction ID",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Create transaction
        # ----------------------------------------------------

        transactions.append({

            "date": date_value,

            "merchant": description,

            # Exact amount from GPay
            "amount": float(
                amount
            ),

            "source": "Google Pay",

            "description": product,

            "payment_method": payment_method,

            "status": status,

            "transaction_id": transaction_id

        })

    # --------------------------------------------------------
    # Total
    # --------------------------------------------------------

    total = sum(
        transaction["amount"]
        for transaction in transactions
    )

    print(
        "\nGoogle Pay valid transactions:",
        len(transactions)
    )

    print(
        f"Exact Google Pay expense total: ₹{total:,.2f}"
    )

    return transactions