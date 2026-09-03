CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Healthcare",
    "Groceries",
    "Other"
]


def categorize_transaction(merchant, amount=0):

    merchant_text = str(merchant).strip().lower()

    if (
        not merchant_text
        or merchant_text in [
            "unknown",
            "none",
            "nan",
            "null",
            ""
        ]
    ):
        return "Other"

    # Food
    food_merchants = [
        "swiggy",
        "zomato",
        "dominos",
        "pizza",
        "kfc",
        "mcdonald",
        "restaurant",
        "food",
        "eat",
        "hotel",
        "cafe",
        "bakery"
    ]

    # Transport
    transport_merchants = [
        "ola",
        "uber",
        "rapido",
        "metro",
        "irctc",
        "bus",
        "transport",
        "redbus",
        "taxi"
    ]

    # Shopping
    shopping_merchants = [
        "amazon",
        "flipkart",
        "myntra",
        "meesho",
        "ajio",
        "shopping",
        "retail"
    ]

    # Groceries
    grocery_merchants = [
        "bigbasket",
        "blinkit",
        "zepto",
        "instamart",
        "grocery",
        "supermarket"
    ]

    # Entertainment
    entertainment_merchants = [
        "netflix",
        "spotify",
        "prime video",
        "bookmyshow",
        "youtube",
        "hotstar",
        "movie"
    ]

    # Healthcare
    healthcare_merchants = [
        "apollo",
        "hospital",
        "pharmacy",
        "medical",
        "doctor",
        "clinic",
        "healthcare"
    ]

    # Bills
    bill_merchants = [
        "electricity",
        "water bill",
        "internet",
        "broadband",
        "airtel",
        "jio",
        "vi ",
        "recharge",
        "mobile bill"
    ]

    if any(word in merchant_text for word in food_merchants):
        return "Food"

    if any(word in merchant_text for word in transport_merchants):
        return "Transport"

    if any(word in merchant_text for word in shopping_merchants):
        return "Shopping"

    if any(word in merchant_text for word in grocery_merchants):
        return "Groceries"

    if any(word in merchant_text for word in entertainment_merchants):
        return "Entertainment"

    if any(word in merchant_text for word in healthcare_merchants):
        return "Healthcare"

    if any(word in merchant_text for word in bill_merchants):
        return "Bills"

    return "Other"