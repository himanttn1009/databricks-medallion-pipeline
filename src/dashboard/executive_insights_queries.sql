-- =============================================================================
-- Executive Insights Dashboard Queries (Gold-only)
-- =============================================================================
--
-- Sources:
--   gold.sales_by_product
--   gold.revenue_by_customer
--   gold.customer_segmentation
--   gold.daily_weekly_trends
--
-- Parameters:
--   :customer_segment   (multi-select; optional)
--   :product_category   (multi-select; optional)
--   :period_type        (single-select; DAILY/WEEKLY)
--   :start_date         (date; optional, trend only)
--   :end_date           (date; optional, trend only)
--
-- NOTE:
-- These queries are designed as a second dashboard variant focused on
-- executive-level insights while remaining fully Gold-only.

-- -----------------------------------------------------------------------------
-- EX-KPI-01 — Revenue (Selected Segments)
-- -----------------------------------------------------------------------------
SELECT
  ROUND(SUM(total_revenue), 2) AS total_revenue
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));

-- -----------------------------------------------------------------------------
-- EX-KPI-02 — High-Value Customer Count
-- (alias as total_orders for compatibility with counter templates if reused)
-- -----------------------------------------------------------------------------
SELECT
  COUNT(*) AS total_orders
FROM gold.revenue_by_customer
WHERE
  total_orders >= 2
  AND total_revenue >= (
    SELECT percentile_approx(total_revenue, 0.75)
    FROM gold.revenue_by_customer
    WHERE total_orders >= 1
  )
  AND (
    COALESCE(cardinality(:customer_segment), 0) = 0
    OR customer_segment IN (SELECT EXPLODE(:customer_segment))
  );

-- -----------------------------------------------------------------------------
-- EX-KPI-03 — Inactive Customer Count
-- -----------------------------------------------------------------------------
SELECT
  COUNT(*) AS customer_count
FROM gold.revenue_by_customer
WHERE
  total_orders = 0
  AND (
    COALESCE(cardinality(:customer_segment), 0) = 0
    OR customer_segment IN (SELECT EXPLODE(:customer_segment))
  );

-- -----------------------------------------------------------------------------
-- EX-KPI-04 — Active Categories
-- -----------------------------------------------------------------------------
SELECT
  category,
  COUNT(product_id) AS product_count
FROM gold.sales_by_product
WHERE
  COALESCE(cardinality(:product_category), 0) = 0
  OR category IN (SELECT EXPLODE(:product_category))
GROUP BY category
ORDER BY category;

-- -----------------------------------------------------------------------------
-- EX-VIZ-01 — Top 10 Customers by Revenue
-- (aliases chosen for compatibility with bar templates if reused)
-- -----------------------------------------------------------------------------
SELECT
  customer_name AS product_name,
  customer_segment AS category,
  total_revenue,
  total_orders
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment))
ORDER BY
  total_revenue DESC,
  customer_name ASC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- EX-VIZ-02 — Average Order Value Distribution
-- -----------------------------------------------------------------------------
SELECT
  customer_id,
  customer_segment,
  COALESCE(avg_order_value, 0) AS total_revenue
FROM gold.revenue_by_customer
WHERE
  COALESCE(cardinality(:customer_segment), 0) = 0
  OR customer_segment IN (SELECT EXPLODE(:customer_segment));

-- -----------------------------------------------------------------------------
-- EX-VIZ-03 — Revenue Share by Behavioral Segment
-- -----------------------------------------------------------------------------
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
-- EX-VIZ-04 — Trend (Selected Granularity + Date Range)
-- -----------------------------------------------------------------------------
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
-- EX-TBL-01 — Customer Priority Table
-- -----------------------------------------------------------------------------
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
