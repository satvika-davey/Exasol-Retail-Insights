"""
main.py — FastAPI backend for the Retail/E-commerce Demand &
Inventory Insights Platform.

Run:
    uvicorn main:app --reload --port 8000
"""

import os
import re
import time
from typing import Optional

import pyexasol
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_client import pick_query_or_generate_sql, summarize_result

load_dotenv()

EXASOL_HOST = os.environ["EXASOL_HOST"]
EXASOL_PORT = os.environ.get("EXASOL_PORT", "8563")
EXASOL_USER = os.environ["EXASOL_USER"]
EXASOL_PASSWORD = os.environ["EXASOL_PASSWORD"]
EXASOL_SCHEMA = os.environ.get("EXASOL_SCHEMA", "RETAIL")

app = FastAPI(title="Retail Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a local hackathon demo; tighten for prod
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    try:
        return pyexasol.connect(
            dsn=f"{EXASOL_HOST}:{EXASOL_PORT}",
            user=EXASOL_USER,
            password=EXASOL_PASSWORD,
            schema=EXASOL_SCHEMA,
            encryption=True,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Exasol: {e}")


# ---------------------------------------------------------------
# SQL safety gate. This is the ONE thing not to weaken to save time.
# Two independent checks: (1) keyword blocklist, (2) single-table
# allowlist derived from the FROM/JOIN clauses. Both must pass.
# ---------------------------------------------------------------
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "EXECUTE", "CALL",
]
ALLOWED_TABLES = {"sales"}


def validate_sql(sql: str) -> None:
    stripped = sql.strip().rstrip(";")

    if not re.match(r"(?is)^\s*(with\b.*?)?select\b", stripped):
        raise HTTPException(400, "Generated query must be a single SELECT statement.")

    if ";" in stripped:
        raise HTTPException(400, "Multiple statements are not allowed.")

    upper = stripped.upper()
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise HTTPException(400, f"Query contains a forbidden keyword: {kw}")

    cte_names = set(
        n.lower() for n in re.findall(r"(?:WITH|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(", stripped, re.IGNORECASE)
    )

    tables_referenced = set(
        t.lower() for t in re.findall(r"(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", stripped, re.IGNORECASE)
    ) - cte_names
    if not tables_referenced.issubset(ALLOWED_TABLES):
        raise HTTPException(
            400,
            f"Query references disallowed table(s): {tables_referenced - ALLOWED_TABLES}",
        )


def run_query(sql: str, params: Optional[dict] = None):
    conn = get_conn()
    try:
        stmt = conn.execute(sql, params or {})
        columns = [c[0] for c in stmt.description()] if hasattr(stmt, "description") else None
        rows = stmt.fetchall()
        return rows, columns
    except Exception as e:
        print(f"[run_query] SQL failed.\nSQL: {sql}\nParams: {params}\nError: {e}")
        raise HTTPException(status_code=500, detail="Query failed. Check server logs for details.")
    finally:
        conn.close()


# ---------------------------------------------------------------
# Pre-built endpoints
# ---------------------------------------------------------------

@app.get("/kpis")
def get_kpis():
    total_revenue = run_query("SELECT ROUND(SUM(line_revenue), 2) FROM sales")[0][0][0]
    total_orders = run_query("SELECT COUNT(DISTINCT invoice_no) FROM sales")[0][0][0]
    top_product_row = run_query(
        """
        SELECT description, ROUND(SUM(line_revenue), 2) AS revenue
        FROM sales GROUP BY description ORDER BY revenue DESC LIMIT 1
        """
    )[0]
    top_product = top_product_row[0][0] if top_product_row else None

    # growth % = this-month revenue vs last-month revenue
    growth_rows = run_query(
        """
        SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS ym, ROUND(SUM(line_revenue), 2)
        FROM sales GROUP BY 1 ORDER BY 1 DESC LIMIT 2
        """
    )[0]
    growth_pct = None
    if len(growth_rows) == 2:
        latest, prev = float(growth_rows[0][1]), float(growth_rows[1][1])
        if prev:
            growth_pct = round(100.0 * (latest - prev) / prev, 1)

    return {
        "total_revenue": float(total_revenue) if total_revenue is not None else 0,
        "total_orders": int(total_orders) if total_orders is not None else 0,
        "top_product": top_product,
        "growth_pct": growth_pct,
    }


@app.get("/trend")
def get_trend(metric: str = "revenue", groupby: str = "month"):
    rows, _ = run_query(
        """
        SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS ym, ROUND(SUM(line_revenue), 2) AS revenue
        FROM sales GROUP BY 1 ORDER BY 1
        """
    )
    return {"labels": [r[0] for r in rows], "values": [float(r[1]) for r in rows]}


@app.get("/top-products")
def get_top_products(n: int = 5, by: str = "revenue"):
    order_col = "SUM(line_revenue)" if by == "revenue" else "SUM(quantity)"
    rows, _ = run_query(
        f"""
        SELECT description, {order_col} AS val
        FROM sales GROUP BY description ORDER BY val DESC LIMIT {int(n)}
        """
    )
    return {"labels": [r[0] for r in rows], "values": [float(r[1]) for r in rows]}


@app.get("/restock-alerts")
def get_restock_alerts():
    sql = """
        WITH bounds AS (SELECT MAX(invoice_date) AS max_date FROM sales),
        recent AS (
            SELECT stock_code, description, SUM(quantity) AS recent_qty
            FROM sales, bounds
            WHERE invoice_date > bounds.max_date - INTERVAL '30' DAY(3)
            GROUP BY stock_code, description
        ),
        historical AS (
            SELECT stock_code, AVG(monthly_qty) AS avg_monthly_qty
            FROM (
                SELECT stock_code, TO_CHAR(invoice_date, 'YYYY-MM') AS ym, SUM(quantity) AS monthly_qty
                FROM sales, bounds
                WHERE invoice_date <= bounds.max_date - INTERVAL '30' DAY(3)
                  AND invoice_date >  bounds.max_date - INTERVAL '120' DAY(3)
                GROUP BY stock_code, TO_CHAR(invoice_date, 'YYYY-MM')
            ) GROUP BY stock_code
        )
        SELECT r.stock_code, r.description, r.recent_qty,
               ROUND(h.avg_monthly_qty, 1) AS avg_hist,
               ROUND(100.0 * (r.recent_qty - h.avg_monthly_qty) / NULLIF(h.avg_monthly_qty, 0), 1) AS pct_above_avg
        FROM recent r JOIN historical h ON r.stock_code = h.stock_code
        WHERE h.avg_monthly_qty > 0 AND r.recent_qty > h.avg_monthly_qty * 1.5
        ORDER BY pct_above_avg DESC
        LIMIT 20
    """
    rows, _ = run_query(sql)
    return {
        "alerts": [
            {
                "stock_code": r[0],
                "description": r[1],
                "recent_qty": float(r[2]),
                "avg_historical_qty": float(r[3]) if r[3] is not None else None,
                "pct_above_avg": float(r[4]) if r[4] is not None else None,
            }
            for r in rows
        ]
    }


@app.get("/benchmark")
def get_benchmark():
    start = time.perf_counter()
    rows, _ = run_query(
        """
        SELECT COUNT(*), COUNT(DISTINCT customer_id), COUNT(DISTINCT stock_code), ROUND(SUM(line_revenue), 2)
        FROM sales
        """
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    r = rows[0]
    return {
        "rows_scanned": int(r[0]),
        "unique_customers": int(r[1]),
        "unique_products": int(r[2]),
        "total_revenue": float(r[3]),
        "elapsed_ms": elapsed_ms,
    }


# ---------------------------------------------------------------
# Natural-language Q&A
# ---------------------------------------------------------------

class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    sql, chart_hint = pick_query_or_generate_sql(req.question)
    validate_sql(sql)

    rows, columns = run_query(sql)

    # Build a simple chartData shape the frontend can pass to Chart.js
    chart_data = None
    if columns and len(columns) >= 2 and rows:
        chart_data = {
            "labels": [str(r[0]) for r in rows[:20]],
            "values": [float(r[1]) if r[1] is not None else 0 for r in rows[:20]],
        }

    answer = summarize_result(req.question, columns, rows)

    return {"answer": answer, "chartData": chart_data, "sql": sql}


@app.get("/health")
def health():
    return {"status": "ok"}
