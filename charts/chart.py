import matplotlib.pyplot as plt


def generate_chart(category_totals):

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    plt.figure(figsize=(9, 5))

    plt.bar(categories, amounts)

    plt.title("Spending by Category")

    plt.xlabel("Category")

    plt.ylabel("Amount")

    plt.xticks(rotation=30)

    plt.tight_layout()

    plt.savefig(
        "output/category_chart.png"
    )

    plt.close()

    print("Category chart generated successfully!")