-- =============================================================================
-- Databricks SQL Dashboard Queries — Gold Layer Only
-- =============================================================================
--
-- Source tables (allowed):
--   gold.sales_by_product
--   gold.revenue_by_customer
--   gold.customer_segmentation
--   gold.daily_weekly_trends
--
-- Forbidden: bronze.*, silver.*, silver.dq_metrics, raw CSV paths
--
-- Dashboard parameters (create in Databricks SQL Dashboard UI):
--
--   :customer_segment   Multi-select. Marketing tier from
--                       gold.revenue_by_customer.customer_segment
--                       (Premium, Standard, Basic). Empty / unset = all.
--                       Used by: KPI-01, KPI-02, KPI-03, VIZ-02, TBL-01
--
--   :product_category    Multi-select. Product category from
--                       gold.sales_by_product.category. Empty / unset = all.
--                       Used by: KPI-04, VIZ-01
--
--   :period_type         Single-select. DAILY or WEEKLY.
--                       Default: DAILY. Used by: VIZ-04
--
--   :start_date          Date. Inclusive start of trend period_start.
--                       Used by: VIZ-04 only
--
--   :end_date            Date. Inclusive end of trend period_start.
--                       Used by: VIZ-04 only
--
-- Parameter syntax: Databricks SQL Dashboard query parameters (:name).
-- Configure each parameter in the dashboard UI and map to the queries below.
-- For multi-select filters, use an Array parameter type or a Query parameter
-- that returns allowed values; when no values are selected, leave unset so
-- the COALESCE/cardinality guard returns all rows.
--
-- =============================================================================


-- -----------------------------------------------------------------------------
-- KPI-01 — Total Revenue
-- Widget: Counter
-- Source: gold.revenue_by_customer
-- Filter: customer_segment (marketing tier)
-- -----------------------------------------------------------------------------

-- QUERY: KPI-01
SELECT
  ROUND(SUM(total_revenue), 2) AS total_revenue
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));


-- -----------------------------------------------------------------------------
-- KPI-02 — Total Orders
-- Widget: Counter
-- Source: gold.revenue_by_customer
-- Filter: customer_segment
-- -----------------------------------------------------------------------------

-- QUERY: KPI-02
SELECT
  SUM(total_orders) AS total_orders
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));


-- -----------------------------------------------------------------------------
-- KPI-03 — Customer Count
-- Widget: Counter
-- Source: gold.revenue_by_customer
-- Filter: customer_segment
-- -----------------------------------------------------------------------------

-- QUERY: KPI-03
SELECT
  COUNT(customer_id) AS customer_count
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));


-- -----------------------------------------------------------------------------
-- KPI-04 — Active Product Count
-- Widget: Counter
-- Source: gold.sales_by_product
-- Filter: product_category
-- -----------------------------------------------------------------------------

-- QUERY: KPI-04
SELECT
  COUNT(product_id) AS product_count
FROM gold.sales_by_product
WHERE
  COALESCE(cardinality(:product_category), 0) = 0
  OR category IN (SELECT EXPLODE(:product_category));


-- -----------------------------------------------------------------------------
-- VIZ-01 — Top 10 Products by Revenue
-- Widget: Bar chart (horizontal recommended)
-- Source: gold.sales_by_product
-- Filter: product_category
-- -----------------------------------------------------------------------------

-- QUERY: VIZ-01
SELECT
  product_name,
  category,
  total_revenue,
  total_orders
FROM gold.sales_by_product
WHERE
  COALESCE(cardinality(:product_category), 0) = 0
  OR category IN (SELECT EXPLODE(:product_category))
ORDER BY
  total_revenue DESC,
  product_name ASC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- VIZ-02 — Customer Revenue Distribution
-- Widget: Histogram (value column: total_revenue)
-- Source: gold.revenue_by_customer
-- Filter: customer_segment
-- Note: Include customers with total_revenue = 0.00 (Inactive)
-- -----------------------------------------------------------------------------

-- QUERY: VIZ-02
SELECT
  customer_id,
  customer_segment,
  total_revenue
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));


-- -----------------------------------------------------------------------------
-- VIZ-03 — Customer Segmentation (Behavioral)
-- Widget: Pie chart (slice size: customer_count)
-- Source: gold.customer_segmentation
-- Note: segment_type is behavioral (High-Value/Repeat/One-Time/Inactive).
--       Not the same as customer_segment (Premium/Standard/Basic).
-- Filter: none (pie is the segmentation view)
-- -----------------------------------------------------------------------------

-- QUERY: VIZ-03
SELECT
  segment_type,
  customer_count,
  total_revenue,
  avg_revenue
FROM gold.customer_segmentation
ORDER BY
  CASE segment_type
    WHEN 'High-Value' THEN 1
    WHEN 'Repeat' THEN 2
    WHEN 'One-Time' THEN 3
    WHEN 'Inactive' THEN 4
    ELSE 5
  END;


-- -----------------------------------------------------------------------------
-- VIZ-04 — Revenue Trend
-- Widget: Line chart
-- Source: gold.daily_weekly_trends
-- Filters: period_type, start_date, end_date (trends only — not KPIs)
-- Default period_type: DAILY
-- -----------------------------------------------------------------------------

-- QUERY: VIZ-04
SELECT
  period_start,
  period_type,
  total_revenue,
  total_orders
FROM gold.daily_weekly_trends
WHERE
  period_type = :period_type
  AND period_start BETWEEN :start_date AND :end_date
ORDER BY
  period_start ASC;


-- -----------------------------------------------------------------------------
-- TBL-01 — Customer Revenue & Order Detail
-- Widget: Table
-- Source: gold.revenue_by_customer
-- Filter: customer_segment
-- -----------------------------------------------------------------------------

-- QUERY: TBL-01
SELECT
  customer_id,
  customer_name,
  customer_segment,
  total_orders,
  total_revenue,
  avg_order_value,
  lifetime_value_actual
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment))
ORDER BY
  total_revenue DESC,
  customer_id ASC
LIMIT 500;


-- =============================================================================
-- Optional helper queries for dashboard parameter defaults (run once in SQL editor)
-- =============================================================================
--
-- Customer segment values:
--   SELECT DISTINCT customer_segment
--   FROM gold.revenue_by_customer
--   ORDER BY customer_segment;
--
-- Product category values:
--   SELECT DISTINCT category
--   FROM gold.sales_by_product
--   ORDER BY category;
--
-- Trend date range defaults:
--   SELECT
--     MIN(period_start) AS default_start_date,
--     MAX(period_start) AS default_end_date
--   FROM gold.daily_weekly_trends
--   WHERE period_type = 'DAILY';
--
-- Period type values: DAILY, WEEKLY
