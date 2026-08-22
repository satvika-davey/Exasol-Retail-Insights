"""
generate_synthetic_data.py

Fallback if a real dataset isn't ready yet. Produces a synthetic
retail CSV with ~200K rows matching the same schema load_data.py
expects, so nobody is blocked waiting on the "real" data.

Usage:
    python generate_synthetic_data.py
    # writes synthetic_sales.csv in the current directory
    python load_data.py synthetic_sales.csv
"""

import random
import csv
from datetime import datetime, timedelta

random.seed(42)

N_ROWS = 200_000
OUTPUT_FILE = "synthetic_sales.csv"

CATEGORIES = ["Electronics", "Home & Kitchen", "Toys", "Apparel", "Sports", "Books", "Beauty"]
PRODUCTS = {
    "Electronics": ["Wireless Mouse", "USB-C Charger", "Bluetooth Speaker", "Phone Case", "Webcam"],
    "Home & Kitchen": ["Ceramic Mug", "Cutting Board", "LED Desk Lamp", "Storage Bin", "Kettle"],
    "Toys": ["Building Blocks", "Puzzle Set", "RC Car", "Plush Bear", "Board Game"],
    "Apparel": ["Cotton T-Shirt", "Denim Jacket", "Wool Socks", "Baseball Cap", "Running Shorts"],
    "Sports": ["Yoga Mat", "Resistance Bands", "Water Bottle", "Jump Rope", "Tennis Balls"],
    "Books": ["Notebook Set", "Sketchbook", "Planner", "Bookmark Pack", "Pen Set"],
    "Beauty": ["Face Cream", "Shampoo Bar", "Lip Balm", "Nail Kit", "Hair Brush"],
}
COUNTRIES = ["United Kingdom", "Germany", "France", "United States", "India",
             "Australia", "Canada", "Netherlands", "Spain", "Ireland"]

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_date():
    delta = END_DATE - START_DATE
    return START_DATE + timedelta(
        days=random.randint(0, delta.days),
        seconds=random.randint(0, 86400),
    )


def main():
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["InvoiceNo", "StockCode", "Description", "Quantity",
             "InvoiceDate", "UnitPrice", "CustomerID", "Country", "Category"]
        )

        n_customers = 5000
        for i in range(N_ROWS):
            category = random.choice(CATEGORIES)
            product = random.choice(PRODUCTS[category])
            stock_code = f"{category[:3].upper()}{hash(product) % 1000:03d}"
            quantity = random.randint(1, 20)
            unit_price = round(random.uniform(2.5, 120.0), 2)
            invoice_no = f"INV{100000 + i // 3}"  # a few line items share an invoice
            customer_id = f"C{random.randint(1, n_customers):05d}"
            country = random.choices(COUNTRIES, weights=[30, 12, 10, 15, 8, 6, 6, 5, 4, 4])[0]

            writer.writerow(
                [
                    invoice_no,
                    stock_code,
                    product,
                    quantity,
                    random_date().strftime("%Y-%m-%d %H:%M:%S"),
                    unit_price,
                    customer_id,
                    country,
                    category,
                ]
            )

            if (i + 1) % 50_000 == 0:
                print(f"  ...{i+1:,} rows written")

    print(f"Wrote {N_ROWS:,} synthetic rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
