-- ============================================================
-- schema.sql
-- Creates the `sales` table used by the whole project.
-- Run this once per teammate's schema (agree on ONE schema name
-- as a team before anyone runs this against the shared trial!).
-- ============================================================

-- Create a dedicated schema so we don't collide with teammates
-- who might spin up their own test tables in the default schema.
CREATE SCHEMA IF NOT EXISTS RETAIL;
OPEN SCHEMA RETAIL;

CREATE TABLE IF NOT EXISTS sales (
    invoice_no      VARCHAR(20),
    stock_code      VARCHAR(20),
    description     VARCHAR(500),
    quantity        DECIMAL(10,0),
    invoice_date    TIMESTAMP,
    unit_price      DECIMAL(10,2),
    customer_id     VARCHAR(20),
    country         VARCHAR(100),
    category        VARCHAR(100),
    -- computed at load time to save every downstream query from
    -- re-multiplying quantity * unit_price
    line_revenue    DECIMAL(14,2)
);

-- Helpful for the "top products" / "by country" / "trend" queries.
CREATE INDEX IF NOT EXISTS idx_sales_invoice_date ON sales (invoice_date);
CREATE INDEX IF NOT EXISTS idx_sales_stock_code ON sales (stock_code);
CREATE INDEX IF NOT EXISTS idx_sales_country ON sales (country);

-- Note: Exasol auto-manages statistics/indices internally in most
-- editions; explicit indices above are harmless if ignored by your
-- trial tier, and free documentation if a judge asks about design.
CREATE TABLE sales (
    product_id INTEGER,
    product_name VARCHAR(100),
    country VARCHAR(50),
    quantity INTEGER,
    sales DECIMAL(12,2),
    category VARCHAR(100),
    customer_id INTEGER,
    order_date DATE,
    profit DECIMAL(12,2),
    discount DECIMAL(5,2)
);
ALTER TABLE sales ADD COLUMN category VARCHAR(100);
ALTER TABLE sales ADD COLUMN customer_id INTEGER;
ALTER TABLE sales ADD COLUMN order_date DATE;
ALTER TABLE sales ADD COLUMN profit DECIMAL(12,2);
ALTER TABLE sales ADD COLUMN discount DECIMAL(5,2);
CREATE TABLE customers (
    customer_id INTEGER,
    customer_name VARCHAR(200),
    country VARCHAR(100),
    customer_type VARCHAR(50)
);

CREATE TABLE products (
    product_id INTEGER,
    product_name VARCHAR(200),
    category VARCHAR(100),
    price DECIMAL(12,2)
);

CREATE TABLE orders (
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    order_date DATE,
    quantity INTEGER,
    total_amount DECIMAL(12,2)
);