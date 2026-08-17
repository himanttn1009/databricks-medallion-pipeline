# Silver Layer

Data quality validation and flagging on Bronze tables — detect intentional defects, preserve all rows, produce row-level flags and aggregate DQ metrics. Silver does **not** silently delete or repair bad data.

> **Status:** Design finalized. **Implementation complete.**  
> **Runtime validation:** Complete — Silver tables and DQ metrics verified in Databricks (run_id `a147c198-45cf-456e-9343-8763d7a75945`).

## Overview

```
bronze.customers ──┐
bronze.products  ──┼──► Silver DQ pipeline
bronze.orders    ──┘         │
                             ├── silver.customers | silver.products | silver.orders
                             │     (all Bronze columns + quality columns)
                             └── silver.dq_metrics (10 rows per run)
                                      │
                                      ▼
                             Gold: silver.* WHERE is_valid = true
```

## Layer boundaries

| Silver does | Silver does not |
|-------------|-----------------|
| Read Bronze unchanged | Modify Bronze |
| Flag DQ issues per row | Delete, deduplicate, or repair rows |
| Write `silver.dq_metrics` | Run Gold aggregations or Dashboard |

## Silver tables

| Table | Source | Row count |
|-------|--------|-----------|
| `silver.customers` | `bronze.customers` | 10,000 |
| `silver.products` | `bronze.products` | 500 |
| `silver.orders` | `bronze.orders` | 100,000 |
| `silver.dq_metrics` | Derived | 10 per `run_id` |

Delta Lake, schema `silver`, no partitioning, entity tables **overwrite** per run.

## Schemas

### Preserved from Bronze

All business columns and metadata columns pass through unchanged:

- **Metadata:** `_ingest_timestamp`, `_source_file`, `_ingest_batch_id`
- **customers:** `customer_id`, `customer_name`, `email`, `country`, `signup_date`, `customer_segment`, `lifetime_value`
- **products:** `product_id`, `product_name`, `category`, `price`, `cost`, `stock_quantity`, `reorder_level`
- **orders:** `order_id`, `customer_id`, `order_date`, `product_id`, `quantity`, `unit_price`, `total_amount`, `order_status`, `payment_date`

### Silver quality columns (all entity tables)

| Column | Type | Meaning |
|--------|------|---------|
| `quality_check_result` | STRING | `PASS` or comma-separated failure codes |
| `is_valid` | BOOLEAN | `true` only when `quality_check_result = 'PASS'` |
| `_silver_processed_timestamp` | TIMESTAMP | Silver processing time for this row |

## DQ rules

Five scripts; five failure-code categories. Fourth mandatory assignment check = **type validation**.

| Script | Code | Applies to |
|--------|------|------------|
| `01_quality_completeness.py` | `COMPLETENESS` | customers.email; orders.customer_id, product_id |
| `02_quality_uniqueness.py` | `UNIQUENESS` | customers.customer_id; orders.order_id |
| `03_quality_type_validation.py` | `TYPE_VALIDATION` | All entities (enums, non-negative, dates) |
| `04_quality_referential_integrity.py` | `REFERENTIAL_INTEGRITY` | orders → Bronze parents |
| `05_quality_business_logic.py` | `BUSINESS_LOGIC` | products (margin); orders (amount, payment, signup) |

### Completeness

- **customers:** `email IS NOT NULL`
- **orders:** `customer_id IS NOT NULL AND product_id IS NOT NULL`
- One `COMPLETENESS` per failing row

### Uniqueness

- **customers:** `customer_id` unique within table
- **orders:** `order_id` unique within table
- `customer_id` on orders is **not** uniqueness-checked

### Type validation

Fixed **`REFERENCE_DATE = 2026-08-15`** (SD-06; matches data generation).

- Enums: `customer_segment`, `order_status`
- Non-negative: prices, costs, quantities, amounts
- Dates: `signup_date`, `order_date`, `payment_date` (if not null) `<= REFERENCE_DATE`

### Referential integrity

- **orders.customer_id** → must exist in distinct `bronze.customers.customer_id` when NOT NULL
- **orders.product_id** → must exist in distinct `bronze.products.product_id` when NOT NULL
- NULL FKs skip RI (SD-04: Bronze PK existence)

### Business rules

| Rule | Entity | FAIL when |
|------|--------|-----------|
| BR-01 | products | `price <= cost` |
| BR-02 | orders | `ABS(total_amount - quantity * unit_price) > 0.01` |
| BR-03 | orders | `Completed` and `payment_date IS NULL` |
| BR-04 | orders | `Pending`/`Cancelled` and `payment_date IS NOT NULL` |
| BR-05 | orders | `order_date < MIN(signup_date)` for customer (internal lookup; SD-01) |

## Intentional defects (expected counts)

| Defect | Count | Code |
|--------|-------|------|
| NULL `email` | 50 | `COMPLETENESS` |
| Duplicate `customer_id` participants | 10 | `UNIQUENESS` |
| NULL `customer_id` | 100 | `COMPLETENESS` |
| NULL `product_id` | 200 | `COMPLETENESS` |
| Orphan `customer_id` | 50 | `REFERENTIAL_INTEGRITY` |
| Orphan `product_id` | 30 | `REFERENTIAL_INTEGRITY` |
| Duplicate `order_id` participants | 20 | `UNIQUENESS` |

**Total explicit defect-participating rows: 460.** Products: no intentional defects.

## Duplicate-pair semantics

- **customers:** 5 duplicate `customer_id` keys × 2 rows = 10 flagged participants
- **orders:** 10 duplicate `order_id` keys × 2 rows = 20 flagged participants
- Flag **all** group members (SD-02); no deduplication before measuring

## NULL handling

- Preserve Bronze NULLs; no imputation
- NULL FKs → completeness, not RI
- Business rules skip when required inputs are NULL or orphan

## Multiple failures

Canonical code order (SD-09): `COMPLETENESS`, `UNIQUENESS`, `TYPE_VALIDATION`, `REFERENTIAL_INTEGRITY`, `BUSINESS_LOGIC`

Example: `COMPLETENESS,REFERENTIAL_INTEGRITY`

## `is_valid` semantics

- Silver contains **all** Bronze rows
- `is_valid = true` ⟺ `quality_check_result = 'PASS'`
- Gold reads only `is_valid = true`

## `silver.dq_metrics`

**Grain:** one row per **`(run_id, entity, check_name)`**.

**10 rows per complete run:**

| Entity | Checks | Rows |
|--------|--------|------|
| customers | COMPLETENESS, UNIQUENESS, TYPE_VALIDATION | 3 |
| products | TYPE_VALIDATION, BUSINESS_LOGIC | 2 |
| orders | COMPLETENESS, UNIQUENESS, TYPE_VALIDATION, REFERENTIAL_INTEGRITY, BUSINESS_LOGIC | 5 |

Schema: `run_id`, `check_name`, `entity`, `total_rows`, `passed_rows`, `failed_rows`, `pass_pct`, `threshold_pct`, `threshold_met`, `run_timestamp`.

**Write mode:** append per `run_id` (SD-03).

## Error handling

| Class | Behavior |
|-------|----------|
| Missing Bronze / row-count mismatch | Fatal — stop pipeline |
| Row-level DQ failure | Non-fatal — flag and continue all checks |
| Delta write failure | Fatal |

## Rerun / idempotency

- Entity tables: **overwrite** (full refresh from Bronze)
- `silver.dq_metrics`: **append** (historical runs preserved)
- Deterministic rules + fixed `REFERENCE_DATE`

## Spark Connect (Databricks Serverless)

Do **not** use `spark._jvm`, `spark._jsc`, or Hadoop `FileSystem` APIs. Use DataFrame, SQL, and Delta only.

## Databricks execution

- **Environment:** Free Edition, Serverless, Unity Catalog
- **Input:** `bronze.customers`, `bronze.products`, `bronze.orders`
- **Orchestrator:** `create_silver_tables.py`
- **Check order:** customers → products → orders (with RI using Bronze parent keys)

### Run in Databricks (notebook)

```python
import sys
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/silver")

from create_silver_tables import main

exit_code = main()
if exit_code != 0:
    raise RuntimeError("Silver processing failed")
```

## Module layout

| File | Purpose |
|------|---------|
| `config.py` | `REFERENCE_DATE`, thresholds, table names, metric configs |
| `schemas.py` | `silver.dq_metrics` Spark schema |
| `dq_utils.py` | Shared load, flag merge, metrics, Delta write |
| `01_quality_completeness.py` | Completeness |
| `02_quality_uniqueness.py` | Uniqueness |
| `03_quality_type_validation.py` | Type validation |
| `04_quality_referential_integrity.py` | Referential integrity |
| `05_quality_business_logic.py` | Business rules |
| `create_silver_tables.py` | Orchestrator |

## Design decisions (SD-01–SD-10)

| ID | Decision |
|----|----------|
| SD-01 | BR-05: `MIN(signup_date)` lookup per `customer_id` (internal) |
| SD-02 | Flag all duplicate PK group members |
| SD-03 | `dq_metrics` append per `run_id` |
| SD-04 | RI against Bronze distinct PKs |
| SD-05 | Fourth mandatory check = TYPE_VALIDATION |
| SD-06 | `REFERENCE_DATE = 2026-08-15` |
| SD-07 | No products completeness rule |
| SD-08 | `price > cost` = BUSINESS_LOGIC on products |
| SD-09 | Canonical failure-code order |
| SD-10 | 460 defect rows = acceptance criteria |

## Acceptance criteria (design)

- [x] Implementation modules created under `src/silver/`
- [x] All Bronze rows in Silver with preserved columns
- [x] Seven defect types detectable at minimum counts above
- [x] `quality_check_result` and `is_valid` on every row
- [x] Exactly 10 `silver.dq_metrics` rows per `run_id`
- [x] No silent row loss or deduplication
- [x] Spark Connect compatible (no JVM/Hadoop FS APIs in code)
- [x] Gold can filter `WHERE is_valid = true`

### Observed runtime metrics (sample run)

| `check_name` | `pass_pct` | `threshold_met` |
|--------------|------------|-----------------|
| `COMPLETENESS_CUSTOMERS` | 99.5% | MET |
| `UNIQUENESS_CUSTOMERS` | 99.9% | NOT MET (expected — duplicate keys) |
| `TYPE_VALIDATION_CUSTOMERS` | 100.0% | MET |
| `TYPE_VALIDATION_PRODUCTS` | 100.0% | MET |
| `BUSINESS_LOGIC_PRODUCTS` | 100.0% | MET |
| `COMPLETENESS_ORDERS` | 99.7% | MET |
| `UNIQUENESS_ORDERS` | 99.98% | NOT MET (expected — duplicate keys) |
| `TYPE_VALIDATION_ORDERS` | 100.0% | MET |
| `REFERENTIAL_INTEGRITY_ORDERS` | 99.92% | MET |
| `BUSINESS_LOGIC_ORDERS` | 100.0% | MET |

**Companion docs:** `design-notes.md` §4, `data-quality-strategy.md`, `data-model.md` §9.
