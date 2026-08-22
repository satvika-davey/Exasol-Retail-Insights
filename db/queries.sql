-- ============================================================
-- queries.sql
-- Pre-built, tested queries. The /ask endpoint's LLM prompt
-- references these by name (see llm_client.py: QUERY_INTENTS)
-- so the model can pick a known-safe query instead of freehanding
-- SQL whenever possible.
-- ============================================================

-- 1. TOTAL_REVENUE — overall total revenue
SELECT ROUND(SUM(line_revenue), 2) AS total_revenue
FROM sales;

-- 1b. TOTAL_REVENUE_RANGE — revenue within a date range
-- params: :start_date, :end_date
SELECT ROUND(SUM(line_revenue), 2) AS total_revenue
FROM sales
WHERE invoice_date BETWEEN :start_date AND :end_date;

-- 2. REVENUE_TREND_MONTHLY — revenue trend by month
SELECT
    TO_CHAR(invoice_date, 'YYYY-MM') AS month,
    ROUND(SUM(line_revenue), 2)      AS revenue
FROM sales
GROUP BY 1
ORDER BY 1;

-- 3a. TOP_PRODUCTS_BY_REVENUE — top N products by revenue
-- params: :n
SELECT
    stock_code,
    description,
    ROUND(SUM(line_revenue), 2) AS revenue
FROM sales
GROUP BY stock_code, description
ORDER BY revenue DESC
LIMIT :n;

-- 3b. TOP_PRODUCTS_BY_QUANTITY — top N products by quantity sold
-- params: :n
SELECT
    stock_code,
    description,
    SUM(quantity) AS total_quantity
FROM sales
GROUP BY stock_code, description
ORDER BY total_quantity DESC
LIMIT :n;

-- 4. REVENUE_BY_COUNTRY — revenue and quantity by country
SELECT
    country,
    ROUND(SUM(line_revenue), 2) AS revenue,
    SUM(quantity)                AS total_quantity
FROM sales
GROUP BY country
ORDER BY revenue DESC;

-- 5. SLOW_VS_FAST_MOVERS — recent velocity vs historical average
-- "recent" = last 30 days of data present in the table;
-- "historical" = the 90 days before that. Flags > 50% swing either way.
WITH bounds AS (
    SELECT MAX(invoice_date) AS max_date FROM sales
),
recent AS (
    SELECT stock_code, description, SUM(quantity) AS recent_qty
    FROM sales, bounds
    WHERE invoice_date > bounds.max_date - INTERVAL '30' DAY
    GROUP BY stock_code, description
),
historical AS (
    SELECT stock_code, AVG(monthly_qty) AS avg_monthly_qty
    FROM (
        SELECT stock_code, TO_CHAR(invoice_date, 'YYYY-MM') AS ym, SUM(quantity) AS monthly_qty
        FROM sales, bounds
        WHERE invoice_date <= bounds.max_date - INTERVAL '30' DAY
          AND invoice_date >  bounds.max_date - INTERVAL '120' DAY
        GROUP BY stock_code, ym
    )
    GROUP BY stock_code
)
SELECT
    r.stock_code,
    r.description,
    r.recent_qty,
    ROUND(h.avg_monthly_qty, 1) AS avg_historical_monthly_qty,
    CASE
        WHEN h.avg_monthly_qty IS NULL OR h.avg_monthly_qty = 0 THEN 'NEW_OR_NO_HISTORY'
        WHEN r.recent_qty > h.avg_monthly_qty * 1.5 THEN 'FAST_MOVING'
        WHEN r.recent_qty < h.avg_monthly_qty * 0.5 THEN 'SLOW_MOVING'
        ELSE 'STEADY'
    END AS movement_flag
FROM recent r
LEFT JOIN historical h ON r.stock_code = h.stock_code
ORDER BY r.recent_qty DESC;

-- 6. RESTOCK_ALERTS — recent velocity > X% above historical avg
-- Reuses the same logic as #5, filtered to FAST_MOVING only —
-- these are the products at risk of stocking out.
WITH bounds AS (
    SELECT MAX(invoice_date) AS max_date FROM sales
),
recent AS (
    SELECT stock_code, description, SUM(quantity) AS recent_qty
    FROM sales, bounds
    WHERE invoice_date > bounds.max_date - INTERVAL '30' DAY
    GROUP BY stock_code, description
),
historical AS (
    SELECT stock_code, AVG(monthly_qty) AS avg_monthly_qty
    FROM (
        SELECT stock_code, TO_CHAR(invoice_date, 'YYYY-MM') AS ym, SUM(quantity) AS monthly_qty
        FROM sales, bounds
        WHERE invoice_date <= bounds.max_date - INTERVAL '30' DAY
          AND invoice_date >  bounds.max_date - INTERVAL '120' DAY
        GROUP BY stock_code, ym
    )
    GROUP BY stock_code
)
SELECT
    r.stock_code,
    r.description,
    r.recent_qty,
    ROUND(h.avg_monthly_qty, 1) AS avg_historical_monthly_qty,
    ROUND(100.0 * (r.recent_qty - h.avg_monthly_qty) / NULLIF(h.avg_monthly_qty, 0), 1) AS pct_above_avg
FROM recent r
JOIN historical h ON r.stock_code = h.stock_code
WHERE h.avg_monthly_qty > 0
  AND r.recent_qty > h.avg_monthly_qty * 1.5   -- 50%+ above historical avg
ORDER BY pct_above_avg DESC;

-- 7. AVG_ORDER_VALUE_TREND — average order value by month
SELECT
    TO_CHAR(invoice_date, 'YYYY-MM') AS month,
    ROUND(SUM(line_revenue) / COUNT(DISTINCT invoice_no), 2) AS avg_order_value
FROM sales
GROUP BY 1
ORDER BY 1;

-- 8. CUSTOMER_STATS — customer count and repeat-customer rate
WITH per_customer AS (
    SELECT customer_id, COUNT(DISTINCT invoice_no) AS n_orders
    FROM sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    COUNT(*)                                            AS total_customers,
    SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END)        AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct
FROM per_customer;

-- 9. FORECAST_NEXT_MONTH_BY_CATEGORY — simple linear trend forecast
-- Uses REGR_SLOPE/REGR_INTERCEPT (Exasol built-in linear regression
-- aggregates) over monthly revenue per category, no ML library needed.
WITH monthly AS (
    SELECT
        category,
        TO_CHAR(invoice_date, 'YYYY-MM') AS ym,
        -- month index (0,1,2,...) as the regression's x variable
        MONTHS_BETWEEN(invoice_date, (SELECT MIN(invoice_date) FROM sales)) AS month_idx,
        SUM(line_revenue) AS revenue
    FROM sales
    GROUP BY category, ym, month_idx
)
SELECT
    category,
    ROUND(REGR_INTERCEPT(revenue, month_idx) + REGR_SLOPE(revenue, month_idx) * (MAX(month_idx) + 1), 2)
        AS forecast_next_month_revenue
FROM monthly
GROUP BY category
ORDER BY forecast_next_month_revenue DESC;

-- 10. QUERY_SPEED_BENCHMARK — the live-demo "wow" moment.
-- Forces a full scan + aggregation over the whole table; measure
-- wall-clock time from the app side and display "X rows in Y ms".
SELECT
    COUNT(*)                     AS rows_scanned,
    COUNT(DISTINCT customer_id)  AS unique_customers,
    COUNT(DISTINCT stock_code)   AS unique_products,
    ROUND(SUM(line_revenue), 2)  AS total_revenue
FROM sales;
