"""
load_data.py

Reads a retail CSV (e.g. Kaggle "Online Retail II"), cleans it, and
loads it into the Exasol `RETAIL.sales` table via pyexasol.

Usage:
    python load_data.py path/to/online_retail_II.csv

Expects columns roughly like:
    InvoiceNo, StockCode, Description, Quantity, InvoiceDate,
    UnitPrice, CustomerID, Country, (Category - optional)

If your CSV's column names differ, edit COLUMN_MAP below rather
than renaming the file — that's the one thing every teammate will
need to tweak for their own copy of the dataset.
"""

import os
import sys
import pandas as pd
import pyexasol
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

EXASOL_HOST = os.environ["EXASOL_HOST"]
EXASOL_PORT = os.environ.get("EXASOL_PORT", "8563")
EXASOL_USER = os.environ["EXASOL_USER"]
EXASOL_PASSWORD = os.environ["EXASOL_PASSWORD"]
EXASOL_SCHEMA = os.environ.get("EXASOL_SCHEMA", "RETAIL")

# Map from your CSV's actual header names -> our standard schema.
# Edit the LEFT side if your CSV headers differ.
COLUMN_MAP = {
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "UnitPrice": "unit_price",
    "CustomerID": "customer_id",
    "Country": "country",
    "Category": "category",  # optional; filled with NULL if absent
}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=COLUMN_MAP)

    required = ["invoice_no", "stock_code", "quantity", "invoice_date", "unit_price"]
    missing_required = [c for c in required if c not in df.columns]
    if missing_required:
        raise ValueError(
            f"CSV is missing required columns after mapping: {missing_required}. "
            f"Check COLUMN_MAP against your CSV's actual headers."
        )

    if "category" not in df.columns:
        df["category"] = None
    if "customer_id" not in df.columns:
        df["customer_id"] = None
    if "country" not in df.columns:
        df["country"] = "Unknown"

    # Drop rows with no quantity/price/date — can't analyze those anyway.
    df = df.dropna(subset=["quantity", "unit_price", "invoice_date"])

    # Type coercion
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df = df.dropna(subset=["quantity", "unit_price", "invoice_date"])

    # Drop obviously bad rows (cancellations/returns show up as negative
    # quantity in Online Retail II — keep them out of a first demo pass,
    # you can revisit this if "returns analysis" becomes a stretch goal).
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]

    df["line_revenue"] = (df["quantity"] * df["unit_price"]).round(2)

    df = df[
        [
            "invoice_no",
            "stock_code",
            "description",
            "quantity",
            "invoice_date",
            "unit_price",
            "customer_id",
            "country",
            "category",
            "line_revenue",
        ]
    ]
    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: python load_data.py path/to/file.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    print(f"Reading {csv_path} ...")
    df = pd.read_csv(csv_path, encoding="ISO-8859-1", low_memory=False)
    print(f"Loaded {len(df):,} raw rows. Cleaning...")
    df = clean(df)
    print(f"{len(df):,} rows remain after cleaning.")

    print(f"Connecting to Exasol at {EXASOL_HOST}:{EXASOL_PORT} ...")
    conn = pyexasol.connect(
        dsn=f"{EXASOL_HOST}:{EXASOL_PORT}",
        user=EXASOL_USER,
        password=EXASOL_PASSWORD,
        schema=EXASOL_SCHEMA,
        encryption=True,  # most trial instances require TLS
    )

    print("Importing rows (this uses pyexasol's fast CSV import path)...")
    conn.import_from_pandas(df, "sales")

    count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"Done. sales table now has {count:,} rows.")
    conn.close()


if __name__ == "__main__":
    main()
