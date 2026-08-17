# Database Setup Notes

## Environment

| Setting | Value |
|---------|-------|
| Platform | Databricks Free Edition |
| Compute | Serverless / cluster with PySpark + Delta Lake |
| Catalog | Unity Catalog (`workspace` catalog) |
| Schemas | `bronze`, `silver`, `gold`, `audit` |

Schemas and tables are created automatically by pipeline scripts — no manual DDL is required before the first run.

## Setup Steps

### 1. Create Unity Catalog volume for source CSVs

Path used by Bronze ingestion:

```
/Volumes/workspace/default/medallion_data/
```

Upload `customers.csv`, `products.csv`, `orders.csv` from the repository `data/` directory.

### 2. Clone repository to Databricks Repos

```
/Workspace/Repos/<user>/databricks-medallion-pipeline/
```

### 3. Run pipeline layers in order

| Step | Script | Creates |
|------|--------|---------|
| 1 | `src/bronze/ingest_all.py` | `bronze.*`, `audit.ingestion_log` |
| 2 | `src/silver/create_silver_tables.py` | `silver.*`, `silver.dq_metrics` |
| 3 | `src/gold/create_gold_tables.py` | `gold.*` |
| 4 | Manual | Databricks SQL Dashboard from `src/dashboard/` |

### 4. Optional — review schema reference

See `database/schema.sql` and `data-model.md` for table and column definitions.

## Path Configuration

| Purpose | Path |
|---------|------|
| Source CSVs | `/Volumes/workspace/default/medallion_data/` |
| Bronze tables | `bronze.customers`, `bronze.products`, `bronze.orders` |
| Silver tables | `silver.customers`, `silver.products`, `silver.orders`, `silver.dq_metrics` |
| Gold tables | `gold.sales_by_product`, `gold.revenue_by_customer`, `gold.customer_segmentation`, `gold.daily_weekly_trends` |
| Audit log | `audit.ingestion_log` |

Override CSV base path via environment variable:

```python
import os
os.environ["MEDALLION_DBFS_INPUT_BASE"] = "/Volumes/workspace/default/medallion_data"
```

## Verification

After each layer, confirm row counts:

```sql
-- Bronze / Silver entity tables
SELECT 'customers' AS t, COUNT(*) FROM bronze.customers
UNION ALL SELECT 'products', COUNT(*) FROM bronze.products
UNION ALL SELECT 'orders', COUNT(*) FROM bronze.orders;

-- Gold
SELECT 'sales_by_product' AS t, COUNT(*) FROM gold.sales_by_product
UNION ALL SELECT 'revenue_by_customer', COUNT(*) FROM gold.revenue_by_customer
UNION ALL SELECT 'customer_segmentation', COUNT(*) FROM gold.customer_segmentation
UNION ALL SELECT 'daily_weekly_trends', COUNT(*) FROM gold.daily_weekly_trends;

-- Silver DQ metrics (latest run)
SELECT * FROM silver.dq_metrics ORDER BY run_timestamp DESC LIMIT 10;
```

Expected: customers 10,000; products 500; orders 100,000; Gold rows per `src/gold/README.md`.
