# Gold Layer

Business-ready aggregations for analytics consumption.

> **Status:** Design finalized. **Implementation complete.**  
> **Runtime validation:** Complete — Gold tables verified in Databricks.

## Architecture

```
silver.customers  ──┐
silver.products   ──┼──► Gold (PySpark + Delta, is_valid = true)
silver.orders     ──┘         │
                              ├── gold.sales_by_product
                              ├── gold.revenue_by_customer
                              ├── gold.customer_segmentation
                              └── gold.daily_weekly_trends
                                        │
                                        ▼
                              Databricks SQL Dashboard
```

| Rule | Detail |
|------|--------|
| Source | Silver only — **never** Bronze |
| Valid rows | `is_valid = true` on Silver inputs |
| Qualifying orders | `is_valid = true` AND `order_status = 'Completed'` |
| DQ boundary | Gold does not re-implement Silver DQ or modify Silver |
| Write mode | Delta **overwrite** per run |
| APIs | PySpark/DataFrame + Delta (Spark Connect compatible) |

## Module structure

| File | Purpose |
|------|---------|
| `config.py` | Schema names, table names, constants, expected Silver row counts |
| `gold_utils.py` | Silver validation, shared loaders, Delta writes, output validation |
| `01_sales_by_product.py` | Product sales aggregation |
| `02_revenue_by_customer.py` | Customer revenue aggregation |
| `03_daily_weekly_trends.py` | Daily and weekly trends |
| `04_customer_segmentation.py` | Behavioral customer segmentation |
| `create_gold_tables.py` | Orchestrator |

## Source Silver tables

| Gold table | Silver sources |
|------------|----------------|
| `gold.sales_by_product` | `silver.orders`, `silver.products` |
| `gold.revenue_by_customer` | `silver.customers`, `silver.orders`, `silver.products` |
| `gold.customer_segmentation` | Derived from `revenue_by_customer` logic |
| `gold.daily_weekly_trends` | `silver.orders` |

## Valid-row contract

- Silver dimension tables: `is_valid = true`
- Qualifying orders: `is_valid = true` AND `order_status = 'Completed'`
- Gold never modifies Silver or re-runs DQ checks

## Gold tables

### `gold.sales_by_product`

| Column | Type | Notes |
|--------|------|-------|
| `product_id` | INT | |
| `product_name` | STRING | |
| `category` | STRING | |
| `total_orders` | BIGINT | `COUNT(DISTINCT order_id)` |
| `total_revenue` | DECIMAL(18,2) | `SUM(total_amount)` |
| `avg_order_value` | DECIMAL(18,2) | `total_revenue / total_orders` |

**Grain:** one row per `product_id` with ≥1 qualifying order (GD-01 omits zero-order products).

### `gold.revenue_by_customer`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `customer_id` | INT | No | |
| `customer_name` | STRING | No | |
| `customer_segment` | STRING | No | Marketing tier |
| `total_orders` | BIGINT | No | 0 when no qualifying orders |
| `total_revenue` | DECIMAL(18,2) | No | 0.00 when no orders |
| `avg_order_value` | DECIMAL(18,2) | Yes | NULL when `total_orders = 0` |
| `lifetime_value_actual` | DECIMAL(18,2) | No | Equals `total_revenue` |

**Grain:** one row per valid `customer_id` (LEFT JOIN qualifying orders; GD-11).

No `country` column (GD-07).

### `gold.customer_segmentation`

| Column | Type | Notes |
|--------|------|-------|
| `segment_type` | STRING | `High-Value`, `Repeat`, `One-Time`, `Inactive` |
| `customer_count` | BIGINT | |
| `avg_revenue` | DECIMAL(18,2) | |
| `total_revenue` | DECIMAL(18,2) | |

**Grain:** one row per non-empty `segment_type` (GD-03).

### `gold.daily_weekly_trends`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `order_date` | DATE | Yes | Set for `DAILY`; NULL for `WEEKLY` |
| `period_type` | STRING | No | `DAILY` or `WEEKLY` |
| `period_start` | DATE | No | Monday week anchor for `WEEKLY` |
| `total_orders` | BIGINT | No | |
| `total_revenue` | DECIMAL(18,2) | No | |

**Grain:** one row per `(period_type, period_start)` in a single table (GD-14).

## Revenue definitions

| Metric | Definition |
|--------|------------|
| `total_revenue` | `SUM(total_amount)` on qualifying orders |
| `total_orders` | `COUNT(DISTINCT order_id)` on qualifying orders |
| `avg_order_value` | `total_revenue / total_orders`, rounded `DECIMAL(18,2)` |
| `lifetime_value_actual` | Per-customer `total_revenue` |

## Customer segmentation rules

Derived from the complete valid-customer population (`revenue_by_customer`).

| `segment_type` | Rule |
|----------------|------|
| Inactive | `total_orders = 0` |
| One-Time | `total_orders = 1` |
| Repeat | `total_orders >= 2` AND `total_revenue < P75` |
| High-Value | `total_orders >= 2` AND `total_revenue >= P75` |

`P75` = 75th percentile of `total_revenue` among customers with `total_orders >= 1` (GD-09).

## Daily / weekly rules

- **DAILY:** `period_type = 'DAILY'`, `order_date = period_start = order_date`
- **WEEKLY:** `period_type = 'WEEKLY'`, `order_date = NULL`, `period_start` = Monday-start week (Spark `date_trunc('week', ...)`)

## Rerun behavior

Gold tables are fully overwritten each run from the current Silver snapshot. Re-run after any Silver reprocessing.

## Spark Connect restrictions

Do **not** use `spark._jvm`, `spark._jsc`, or Hadoop `FileSystem` APIs. Use DataFrame, SQL, and Delta only.

## Run in Databricks (notebook)

```python
import sys
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/gold")

from create_gold_tables import main

exit_code = main()
if exit_code != 0:
    raise RuntimeError("Gold processing failed")
```

**Prerequisites:** Silver tables with row counts 10,000 / 500 / 100,000.

## Validation checklist

- [x] Implementation modules created under `src/gold/`
- [x] Four Gold Delta tables written
- [x] Assignment §8.A–C columns and calculations correct
- [x] `daily_weekly_trends` with `DAILY` and `WEEKLY` rows (2,679 total)
- [x] Only `is_valid = true` Silver rows used
- [x] Only `Completed` orders in revenue metrics
- [x] No Silver mutation or DQ re-implementation in code
- [x] Spark Connect compatible (no JVM/Hadoop FS APIs in code)
- [x] Dashboard can query Gold without reading Silver

### Observed runtime row counts

| Table | Rows |
|-------|------|
| `gold.sales_by_product` | 500 |
| `gold.revenue_by_customer` | 9,940 |
| `gold.customer_segmentation` | 4 |
| `gold.daily_weekly_trends` | 2,679 |
