# Data Model

> **Status:** Model defined. All layers implemented and runtime-validated. Dashboard consumes Gold only.  
> **Inputs:** `assignment/assignment-requirements.md`, `requirements-analysis.md`, `design-notes.md`  
> **Companion docs:** `data-quality-strategy.md`, `database/schema.sql`, `src/silver/README.md`

---

## Overview

This pipeline models a minimal e-commerce domain with three source entities — **customers**, **products**, and **orders** — flowing through medallion layers (`bronze` → `silver` → `gold`) into four Gold aggregation tables. A separate **audit** schema supports ingestion logging; **silver.dq_metrics** stores data quality reporting.

**Legend for field origin:**

| Tag | Meaning |
|-----|---------|
| *(source)* | Present in CSV / assignment schema |
| *(Bronze derived)* | Added during Bronze ingestion |
| *(Silver derived)* | Added during Silver processing |
| *(Gold derived)* | Computed during Gold aggregation |
| *(assumption)* | Design decision not explicitly defined in assignment |

---

## 1. Customers Entity

### 1.1 Business meaning

Represents a registered e-commerce customer. Used as the parent dimension for order transactions and as the basis for customer-level revenue and segmentation analytics in Gold.

### 1.2 Grain

One row per customer.

### 1.3 Expected volume

**10,000** rows in `customers.csv` (~500 KB).

### 1.4 Attributes

| Column | Data type | Nullable | Origin | Business meaning |
|--------|-----------|----------|--------|------------------|
| `customer_id` | INT | No *(ideal)*; nulls possible in corrupt source | *(source)* | Unique identifier for the customer; primary key |
| `customer_name` | STRING | No *(ideal)* | *(source)* | Display name of the customer |
| `email` | STRING | No *(ideal)*; **50 intentional NULLs** in sample data | *(source)* | Customer contact email; completeness check target |
| `country` | STRING | No *(ideal)* | *(source)* | Country of registration; used for dashboard filtering in Gold |
| `signup_date` | DATE | No *(ideal)* | *(source)* | Date the customer registered |
| `customer_segment` | STRING | No *(ideal)* | *(source)* | Marketing tier: `Premium`, `Standard`, or `Basic` |
| `lifetime_value` | DECIMAL(18,2) | No *(ideal)* | *(source)* | Lifetime value from source customer database *(may differ from pipeline-computed value)* |

---

## 2. Products Entity

### 2.1 Business meaning

Represents a product in the e-commerce catalog. Used as the parent dimension for order line items and product-level sales analytics in Gold.

### 2.2 Grain

One row per product.

### 2.3 Expected volume

**500** rows in `products.csv` (~50 KB).

### 2.4 Attributes

| Column | Data type | Nullable | Origin | Business meaning |
|--------|-----------|----------|--------|------------------|
| `product_id` | INT | No *(ideal)* | *(source)* | Unique identifier for the product; primary key |
| `product_name` | STRING | No *(ideal)* | *(source)* | Name of the product |
| `category` | STRING | No *(ideal)* | *(source)* | Product category for grouping and dashboard filters |
| `price` | DECIMAL(18,2) | No *(ideal)* | *(source)* | Listed unit price in the catalog |
| `cost` | DECIMAL(18,2) | No *(ideal)* | *(source)* | Unit cost for margin analysis *(not used in Gold aggregations per assignment)* |
| `stock_quantity` | INT | No *(ideal)* | *(source)* | Current inventory on hand |
| `reorder_level` | INT | No *(ideal)* | *(source)* | Inventory threshold triggering reorder |

---

## 3. Orders Entity

### 3.1 Business meaning

Represents a sales transaction linking a customer to a product. This is the central **fact** entity driving revenue metrics, trends, and customer behavior segmentation in Gold.

### 3.2 Grain

One row per order *(assignment treats `order_id` as primary key — one row per order, not order line item)*.

### 3.3 Expected volume

**100,000** rows in `orders.csv` (~2–3 MB).

### 3.4 Attributes

| Column | Data type | Nullable | Origin | Business meaning |
|--------|-----------|----------|--------|------------------|
| `order_id` | INT | No *(ideal)*; duplicates injected in sample data | *(source)* | Unique identifier for the order; primary key |
| `customer_id` | INT | No *(ideal)*; **100 intentional NULLs** | *(source)* | Foreign key to `customers.customer_id` |
| `order_date` | DATE | No *(ideal)* | *(source)* | Date the order was placed |
| `product_id` | INT | No *(ideal)*; **200 intentional NULLs** | *(source)* | Foreign key to `products.product_id` |
| `quantity` | INT | No *(ideal)* | *(source)* | Number of units ordered |
| `unit_price` | DECIMAL(18,2) | No *(ideal)* | *(source)* | Price per unit at time of order |
| `total_amount` | DECIMAL(18,2) | No *(ideal)* | *(source)* | Total order value; subject to business logic check vs `quantity × unit_price` |
| `order_status` | STRING | No *(ideal)* | *(source)* | `Pending`, `Completed`, or `Cancelled` |
| `payment_date` | DATE | **Yes** *(assignment)* | *(source)* | Date payment was received; required for `Completed` orders per business logic check *(assumption)* |

---

## 4. Primary Keys

| Entity | Table(s) | Primary key column | Enforced in Silver |
|--------|----------|-------------------|-------------------|
| Customers | `bronze.customers`, `silver.customers` | `customer_id` | Uniqueness check on `silver.customers` |
| Products | `bronze.products`, `silver.products` | `product_id` | Uniqueness check on `silver.products` *(no duplicate defects injected; check still applied)* |
| Orders | `bronze.orders`, `silver.orders` | `order_id` | Uniqueness check on `silver.orders` |
| DQ metrics | `silver.dq_metrics` | `run_id` + `check_name` *(logical)* | N/A — derived reporting table |
| Ingestion log | `audit.ingestion_log` | `run_id` + `layer` + `entity` + `run_timestamp` *(logical)* | N/A — append-only audit |

Gold tables are **aggregated** and keyed by their grain columns (see Section 10); no surrogate keys required.

---

## 5. Foreign Keys

| Child table | Foreign key column | Parent table | Parent key | Validated in Silver |
|-------------|-------------------|--------------|------------|---------------------|
| `orders` | `customer_id` | `customers` | `customer_id` | Referential integrity check *(when `customer_id` IS NOT NULL)* |
| `orders` | `product_id` | `products` | `product_id` | Referential integrity check *(when `product_id` IS NOT NULL)* |

**Note:** Referential integrity is evaluated against parent keys in Silver after parent uniqueness checks. Orphan FK values are an intentional defect in sample data (50 + 30 rows).

---

## 6. Relationships

### 6.1 Cardinality

```
customers (1) ──────< orders (many)
products  (1) ──────< orders (many)
```

- One customer can place **many** orders.
- One product can appear in **many** orders.
- Orders reference exactly one customer and one product per row *(at the assignment grain)*.
- There is **no direct relationship** between customers and products except through orders.

### 6.2 Textual relationship diagram

```
                    ┌─────────────────────┐
                    │     customers       │
                    │  PK: customer_id    │
                    │  marketing segment  │
                    │  lifetime_value     │
                    └──────────┬──────────┘
                               │
                               │ 1
                               │
                               │ customer_id (FK)
                               │
                               ▼ *
                    ┌─────────────────────┐         * ┌─────────────────────┐
                    │       orders        │───────────│      products       │
                    │  PK: order_id       │ product_id│  PK: product_id     │
                    │  FK: customer_id    │   (FK)    │  category, price    │
                    │  FK: product_id     │     1     └─────────────────────┘
                    │  total_amount       │
                    │  order_status       │
                    └──────────┬──────────┘
                               │
                               │ valid completed orders
                               │ (Silver is_valid = true,
                               │  order_status = 'Completed')
                               ▼
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
 ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
 │ sales_by_product│  │revenue_by_customer│ │customer_segmentation │
 │  (by product)   │  │  (by customer)   │  │  (by segment_type)   │
 └─────────────────┘  └─────────────────┘  └──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ daily_weekly_trends │
                    │   (by date/period)  │
                    └─────────────────────┘
```

### 6.3 Layer relationships

| From | To | Join / filter |
|------|-----|---------------|
| `bronze.orders` | `bronze.customers` | No join in Bronze — stored independently |
| `silver.orders` | `silver.customers` | RI check: `customer_id` exists in valid parent set |
| `silver.orders` | `silver.products` | RI check: `product_id` exists in valid parent set |
| Gold aggregations | `silver.orders` + dimensions | Join on FKs; filter `is_valid = true` and `order_status = 'Completed'` (DA-07) |

---

## 7. Source Schema

Physical format: **CSV** files on S3/DBFS (and `data/` in repository).

### 7.1 `customers.csv`

| Column | Spark / SQL type | PK/FK | Allowed values | Nullable in source contract |
|--------|------------------|-------|----------------|------------------------------|
| `customer_id` | INT | PK | — | Required |
| `customer_name` | STRING | — | — | Required |
| `email` | STRING | — | — | Required *(completeness target)* |
| `country` | STRING | — | — | Required |
| `signup_date` | DATE | — | — | Required |
| `customer_segment` | STRING | — | `Premium`, `Standard`, `Basic` | Required |
| `lifetime_value` | DECIMAL(18,2) | — | ≥ 0 *(type check)* | Required |

### 7.2 `products.csv`

| Column | Spark / SQL type | PK/FK | Allowed values | Nullable in source contract |
|--------|------------------|-------|----------------|------------------------------|
| `product_id` | INT | PK | — | Required |
| `product_name` | STRING | — | — | Required |
| `category` | STRING | — | — | Required |
| `price` | DECIMAL(18,2) | — | ≥ 0 | Required |
| `cost` | DECIMAL(18,2) | — | ≥ 0 | Required |
| `stock_quantity` | INT | — | ≥ 0 | Required |
| `reorder_level` | INT | — | ≥ 0 | Required |

### 7.3 `orders.csv`

| Column | Spark / SQL type | PK/FK | Allowed values | Nullable in source contract |
|--------|------------------|-------|----------------|------------------------------|
| `order_id` | INT | PK | — | Required |
| `customer_id` | INT | FK → customers | — | Required *(completeness target)* |
| `order_date` | DATE | — | — | Required |
| `product_id` | INT | FK → products | — | Required *(completeness target)* |
| `quantity` | INT | — | ≥ 0 | Required |
| `unit_price` | DECIMAL(18,2) | — | ≥ 0 | Required |
| `total_amount` | DECIMAL(18,2) | — | ≥ 0 | Required |
| `order_status` | STRING | — | `Pending`, `Completed`, `Cancelled` | Required |
| `payment_date` | DATE | — | — | **Nullable** *(assignment)* |

---

## 8. Bronze Schema

Bronze tables mirror source columns **unchanged**, plus ingestion metadata. Format: **Delta Lake** in schema `bronze`.

### 8.1 `bronze.customers`

| Column | Type | Origin | Nullable |
|--------|------|--------|----------|
| `customer_id` | INT | *(source)* | Yes *(raw fidelity — defects preserved)* |
| `customer_name` | STRING | *(source)* | Yes |
| `email` | STRING | *(source)* | Yes |
| `country` | STRING | *(source)* | Yes |
| `signup_date` | DATE | *(source)* | Yes |
| `customer_segment` | STRING | *(source)* | Yes |
| `lifetime_value` | DECIMAL(18,2) | *(source)* | Yes |
| `_ingest_timestamp` | TIMESTAMP | *(Bronze derived)* | No |
| `_source_file` | STRING | *(Bronze derived)* | No |
| `_ingest_batch_id` | STRING | *(Bronze derived)* | No |

### 8.2 `bronze.products`

| Column | Type | Origin | Nullable |
|--------|------|--------|----------|
| `product_id` | INT | *(source)* | Yes |
| `product_name` | STRING | *(source)* | Yes |
| `category` | STRING | *(source)* | Yes |
| `price` | DECIMAL(18,2) | *(source)* | Yes |
| `cost` | DECIMAL(18,2) | *(source)* | Yes |
| `stock_quantity` | INT | *(source)* | Yes |
| `reorder_level` | INT | *(source)* | Yes |
| `_ingest_timestamp` | TIMESTAMP | *(Bronze derived)* | No |
| `_source_file` | STRING | *(Bronze derived)* | No |
| `_ingest_batch_id` | STRING | *(Bronze derived)* | No |

### 8.3 `bronze.orders`

| Column | Type | Origin | Nullable |
|--------|------|--------|----------|
| `order_id` | INT | *(source)* | Yes |
| `customer_id` | INT | *(source)* | Yes |
| `order_date` | DATE | *(source)* | Yes |
| `product_id` | INT | *(source)* | Yes |
| `quantity` | INT | *(source)* | Yes |
| `unit_price` | DECIMAL(18,2) | *(source)* | Yes |
| `total_amount` | DECIMAL(18,2) | *(source)* | Yes |
| `order_status` | STRING | *(source)* | Yes |
| `payment_date` | DATE | *(source)* | Yes |
| `_ingest_timestamp` | TIMESTAMP | *(Bronze derived)* | No |
| `_source_file` | STRING | *(Bronze derived)* | No |
| `_ingest_batch_id` | STRING | *(Bronze derived)* | No |

### 8.4 `audit.ingestion_log`

Run-level ingestion metadata *(not entity-specific)*.

| Column | Type | Origin | Nullable |
|--------|------|--------|----------|
| `run_id` | STRING | *(Bronze derived)* | No |
| `layer` | STRING | *(Bronze derived)* | No |
| `entity` | STRING | *(Bronze derived)* | No |
| `status` | STRING | *(Bronze derived)* | No |
| `row_count` | BIGINT | *(Bronze derived)* | Yes |
| `source_path` | STRING | *(Bronze derived)* | Yes |
| `target_table` | STRING | *(Bronze derived)* | No |
| `message` | STRING | *(Bronze derived)* | Yes |
| `run_timestamp` | TIMESTAMP | *(Bronze derived)* | No |

---

## 9. Silver Schema

Silver entity tables contain **all Bronze business columns + Bronze metadata + Silver quality columns**. Format: **Delta Lake** in schema `silver`.

### 9.1 Silver columns added to all entity tables

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `quality_check_result` | STRING | *(Silver derived)* | No | `PASS` or comma-separated failure codes in canonical order: `COMPLETENESS`, `UNIQUENESS`, `TYPE_VALIDATION`, `REFERENTIAL_INTEGRITY`, `BUSINESS_LOGIC` |
| `is_valid` | BOOLEAN | *(Silver derived)* | No | `true` when `quality_check_result = 'PASS'`; Gold reads only valid rows |
| `_silver_processed_timestamp` | TIMESTAMP | *(Silver derived)* | No | When Silver processing completed for this row |

### 9.2 `silver.customers`

All columns from `bronze.customers` plus Silver columns in Section 9.1.

### 9.3 `silver.products`

All columns from `bronze.products` plus Silver columns in Section 9.1.

### 9.4 `silver.orders`

All columns from `bronze.orders` plus Silver columns in Section 9.1.

### 9.5 `silver.dq_metrics`

Quality reporting table — **one row per `(run_id, entity, check_name)`** per Silver run. A complete run produces **exactly 10 metric rows** (customers = 3, products = 2, orders = 5). Written in **append** mode per `run_id`; Silver entity tables use **overwrite** per run.

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `run_id` | STRING | *(Silver derived)* | No | Pipeline run identifier |
| `check_name` | STRING | *(Silver derived)* | No | e.g. `COMPLETENESS_CUSTOMERS`, `UNIQUENESS_ORDERS` |
| `entity` | STRING | *(Silver derived)* | No | `customers`, `orders`, or `products` |
| `total_rows` | BIGINT | *(Silver derived)* | No | Rows evaluated |
| `passed_rows` | BIGINT | *(Silver derived)* | No | Rows passing the check |
| `failed_rows` | BIGINT | *(Silver derived)* | No | Rows failing the check |
| `pass_pct` | DECIMAL(5,2) | *(Silver derived)* | No | Percentage passed |
| `threshold_pct` | DECIMAL(5,2) | *(Silver derived)* | No | Required threshold for the check |
| `threshold_met` | BOOLEAN | *(Silver derived)* | No | Whether `pass_pct` meets threshold |
| `run_timestamp` | TIMESTAMP | *(Silver derived)* | No | When metrics were computed |

**Configured checks per entity (10 rows per run):**

| Entity | `check_name` values |
|--------|---------------------|
| customers | `COMPLETENESS_CUSTOMERS`, `UNIQUENESS_CUSTOMERS`, `TYPE_VALIDATION_CUSTOMERS` |
| products | `TYPE_VALIDATION_PRODUCTS`, `BUSINESS_LOGIC_PRODUCTS` |
| orders | `COMPLETENESS_ORDERS`, `UNIQUENESS_ORDERS`, `TYPE_VALIDATION_ORDERS`, `REFERENTIAL_INTEGRITY_ORDERS`, `BUSINESS_LOGIC_ORDERS` |

Type-validation future-date rules use fixed **`REFERENCE_DATE = 2026-08-15`** (not `current_date()`). See `design-notes.md` §4.6 and SD-06.

---

## 10. Gold Schema

Gold tables are **aggregated** datasets built from valid Silver data (`is_valid = true`). Format: **Delta Lake** in schema `gold`. Write mode: **overwrite** per run.

**Qualifying order filter (finalized):** `silver.orders.is_valid = true` AND `order_status = 'Completed'` for all revenue and order-count metrics (DA-07).

**Implementation:** PySpark/DataFrame APIs (GD-10); Spark Connect compatible.

### 10.1 `gold.sales_by_product`

**Grain:** One row per `product_id` with at least one qualifying completed-valid order (GD-01 — products with zero qualifying orders omitted).

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `product_id` | INT | *(source via Silver)* | No | Product identifier |
| `product_name` | STRING | *(source via Silver)* | No | Product name |
| `category` | STRING | *(source via Silver)* | No | Product category |
| `total_orders` | BIGINT | *(Gold derived)* | No | `COUNT(DISTINCT order_id)` for qualifying orders |
| `total_revenue` | DECIMAL(18,2) | *(Gold derived)* | No | `SUM(total_amount)` for qualifying orders |
| `avg_order_value` | DECIMAL(18,2) | *(Gold derived)* | No | `total_revenue / total_orders`, rounded to 2 dp (GD-08) |

**Join rule:** Qualifying orders inner-joined to valid `silver.products` (GD-02, GD-13).

### 10.2 `gold.revenue_by_customer`

**Grain:** One row per valid `customer_id` in `silver.customers` (includes customers with zero qualifying orders — required for Inactive segmentation).

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `customer_id` | INT | *(source via Silver)* | No | Customer identifier |
| `customer_name` | STRING | *(source via Silver)* | No | Customer name |
| `customer_segment` | STRING | *(source via Silver)* | No | Marketing segment: `Premium`, `Standard`, `Basic` |
| `total_orders` | BIGINT | *(Gold derived)* | No | `COUNT(DISTINCT order_id)`; 0 when no qualifying orders (GD-11) |
| `total_revenue` | DECIMAL(18,2) | *(Gold derived)* | No | `SUM(total_amount)`; 0.00 when no qualifying orders (GD-11) |
| `avg_order_value` | DECIMAL(18,2) | *(Gold derived)* | Yes | `total_revenue / total_orders`, rounded 2 dp; **null** when `total_orders = 0` (GD-11) |
| `lifetime_value_actual` | DECIMAL(18,2) | *(Gold derived)* | No | Equals `total_revenue`; 0.00 when no qualifying orders (GD-11) |

**Customer revenue base:** valid `silver.customers` LEFT JOIN qualifying orders (with valid product when attributing order revenue).

> **GD-07:** `country` is **not** a Gold column. Assignment §8.B does not require it.

### 10.3 `gold.customer_segmentation`

**Grain:** One row per non-empty behavioral `segment_type` (GD-03 — empty buckets omitted).

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `segment_type` | STRING | *(Gold derived)* | No | `High-Value`, `Repeat`, `One-Time`, or `Inactive` |
| `customer_count` | BIGINT | *(Gold derived)* | No | Number of customers in the segment |
| `avg_revenue` | DECIMAL(18,2) | *(Gold derived)* | No | Average per-customer `total_revenue` in segment |
| `total_revenue` | DECIMAL(18,2) | *(Gold derived)* | No | Sum of per-customer `total_revenue` in segment |

Derived from the **complete valid-customer population** (including zero-order customers).

### 10.4 `gold.daily_weekly_trends`

**Grain:** One row per `(period_type, period_start)` in a single table (GD-14).

| Column | Type | Origin | Nullable | Business meaning |
|--------|------|--------|----------|------------------|
| `order_date` | DATE | *(Gold derived)* | Yes | Populated for `DAILY` rows; **NULL** for `WEEKLY` rows (GD-04) |
| `period_type` | STRING | *(Gold derived)* | No | `DAILY` or `WEEKLY` |
| `period_start` | DATE | *(Gold derived)* | No | Period anchor; Monday-start week for `WEEKLY` (GD-05) |
| `total_orders` | BIGINT | *(Gold derived)* | No | Count of qualifying orders in period |
| `total_revenue` | DECIMAL(18,2) | *(Gold derived)* | No | Sum of `total_amount` for qualifying orders in period |

---

## 11. Derived Fields

### 11.1 Bronze-derived fields

| Field | Table(s) | Derivation |
|-------|----------|------------|
| `_ingest_timestamp` | All Bronze entity tables | Current timestamp at ingest |
| `_source_file` | All Bronze entity tables | Path/name of source CSV |
| `_ingest_batch_id` | All Bronze entity tables | Pipeline run identifier |
| `audit.ingestion_log.*` | `audit.ingestion_log` | Aggregated run-level ingest events |

### 11.2 Silver-derived fields

| Field | Table(s) | Derivation |
|-------|----------|------------|
| `quality_check_result` | `silver.customers`, `silver.orders`, `silver.products` | Merged result of completeness, uniqueness, type validation, referential integrity, and business logic checks |
| `is_valid` | Silver entity tables | `quality_check_result = 'PASS'` |
| `_silver_processed_timestamp` | Silver entity tables | Timestamp when Silver processing completed |
| `silver.dq_metrics.*` | `silver.dq_metrics` | Aggregated pass/fail counts and percentages per check |

### 11.3 Gold-derived fields

| Field | Table | Derivation |
|-------|-------|------------|
| `total_orders` | `sales_by_product`, `revenue_by_customer` | `COUNT(DISTINCT order_id)` on qualifying orders |
| `total_revenue` | All Gold tables | `SUM(total_amount)` on qualifying orders |
| `avg_order_value` | `sales_by_product`, `revenue_by_customer` | `total_revenue / total_orders`, `DECIMAL(18,2)` rounded (GD-08) |
| `lifetime_value_actual` | `revenue_by_customer` | Equals per-customer `total_revenue` from qualifying orders (GD-11) |
| `segment_type` | `customer_segmentation` | Behavioral classification (finalized): |
| | | **Inactive** — `total_orders = 0` |
| | | **One-Time** — `total_orders = 1` |
| | | **Repeat** — `total_orders >= 2` AND `total_revenue < P75` |
| | | **High-Value** — `total_orders >= 2` AND `total_revenue >= P75` |
| `customer_count` | `customer_segmentation` | `COUNT(customer_id)` per `segment_type`; empty buckets omitted (GD-03) |
| `avg_revenue` | `customer_segmentation` | `AVG(total_revenue)` per `segment_type` |
| `period_type`, `period_start`, `order_date` | `daily_weekly_trends` | Single table; `DAILY`/`WEEKLY`; weekly `order_date` NULL (GD-04, GD-14) |

### 11.4 Fields that are NOT derived (passed through)

| Field | Passed from → to |
|-------|------------------|
| `customer_id`, `customer_name`, `email`, `country`, `signup_date`, `customer_segment`, `lifetime_value` | Source → Bronze → Silver |
| `product_id`, `product_name`, `category`, `price`, `cost`, `stock_quantity`, `reorder_level` | Source → Bronze → Silver |
| `order_id`, `customer_id`, `product_id`, `order_date`, `quantity`, `unit_price`, `total_amount`, `order_status`, `payment_date` | Source → Bronze → Silver |
| `product_id`, `product_name`, `category` | Silver products → Gold `sales_by_product` |
| `customer_id`, `customer_name`, `customer_segment` | Silver customers → Gold `revenue_by_customer` |

---

## 12. Data Types

### 12.1 Type mapping (source → Delta)

| Logical type | Spark / Delta type | Used for |
|--------------|-------------------|----------|
| Integer identifiers and counts | `INT` or `BIGINT` | IDs, `quantity`, `stock_quantity`, `reorder_level`, counts in Gold |
| Text | `STRING` | Names, emails, categories, statuses, segments, failure codes |
| Dates | `DATE` | `signup_date`, `order_date`, `payment_date`, trend dates |
| Timestamps | `TIMESTAMP` | Ingest and processing metadata |
| Monetary values | `DECIMAL(18,2)` | `lifetime_value`, `price`, `cost`, `unit_price`, `total_amount`, revenue metrics |
| Boolean | `BOOLEAN` | `is_valid`, `threshold_met` |
| Percentage | `DECIMAL(5,2)` | `pass_pct`, `threshold_pct` in `dq_metrics` |

### 12.2 Enum constraints (enforced in Silver type validation)

| Column | Allowed values |
|--------|----------------|
| `customer_segment` | `Premium`, `Standard`, `Basic` |
| `order_status` | `Pending`, `Completed`, `Cancelled` |
| `segment_type` *(Gold)* | `High-Value`, `Repeat`, `One-Time`, `Inactive` |
| `period_type` *(Gold)* | `DAILY`, `WEEKLY` |
| `quality_check_result` | `PASS` or comma-separated subset of failure codes |

---

## 13. Nullable Fields

### 13.1 By layer

| Layer | Nullable by design | Notes |
|-------|---------------------|-------|
| **Source** | `orders.payment_date` only *(assignment)* | All other columns are required in the source contract but may contain intentional defects |
| **Bronze** | All source columns nullable | Raw fidelity — no enforcement at landing |
| **Bronze metadata** | Non-null | `_ingest_timestamp`, `_source_file`, `_ingest_batch_id` always populated |
| **Silver** | Source columns remain nullable | Invalid values preserved; `quality_check_result`, `is_valid`, `_silver_processed_timestamp` are non-null |
| **Gold** | `revenue_by_customer.avg_order_value` when `total_orders = 0`; `daily_weekly_trends.order_date` may be null for weekly rows *(implementation choice)* | All other Gold columns non-null at their grain |

### 13.2 Completeness check targets (must not be NULL in valid Silver rows)

| Table | Column | Check |
|-------|--------|-------|
| `silver.customers` | `email` | Completeness |
| `silver.orders` | `customer_id` | Completeness |
| `silver.orders` | `product_id` | Completeness |

Rows with NULL in these fields remain in Silver with `is_valid = false`.

### 13.3 Conditionally nullable

| Column | Condition |
|--------|-----------|
| `orders.payment_date` | Nullable in source; business logic requires NOT NULL when `order_status = 'Completed'` *(assumption)* |

---

## 14. Business Meaning

### 14.1 Entity summary

| Entity | Role in business | Analytical use |
|--------|-----------------|----------------|
| **Customers** | Who buys | Segmentation, LTV, geographic filters |
| **Products** | What is sold | Revenue by product/category, top-N rankings |
| **Orders** | Transaction events | Revenue, order counts, trends over time |

### 14.2 Column semantics — customers

| Column | Business meaning |
|--------|------------------|
| `customer_segment` | **Marketing classification** assigned at registration (`Premium` / `Standard` / `Basic`); distinct from behavioral `segment_type` in Gold |
| `lifetime_value` | **Source-system estimate** of customer value; may not match pipeline-computed `lifetime_value_actual` due to data quality issues and different calculation methods |
| `email` | Primary contact; completeness is a data quality gate |
| `country` | Geographic attribute for regional analysis |

### 14.3 Column semantics — products

| Column | Business meaning |
|--------|------------------|
| `price` | Current catalog list price |
| `cost` | Unit cost; available for future margin analysis but not required in Gold per assignment |
| `stock_quantity` / `reorder_level` | Inventory management attributes; carried through pipeline but not used in Gold aggregations |

### 14.4 Column semantics — orders

| Column | Business meaning |
|--------|------------------|
| `order_status` | Lifecycle state; Gold revenue metrics use `Completed` only *(assumption)* |
| `total_amount` | Revenue attributed to this order; should equal `quantity × unit_price` within tolerance |
| `payment_date` | When payment was received; expected for completed orders |

### 14.5 Gold metrics semantics

| Metric | Business meaning |
|--------|------------------|
| `total_revenue` | Recognized revenue from completed, quality-validated orders |
| `total_orders` | Distinct completed order count |
| `avg_order_value` | Average revenue per order |
| `lifetime_value_actual` | Actual cumulative spend computed from order history in the pipeline |
| `segment_type` | **Behavioral** customer grouping for strategic analysis — not the same as `customer_segment` |

### 14.6 Distinction: `customer_segment` vs `segment_type`

| Field | Layer | Type | Meaning |
|-------|-------|------|---------|
| `customer_segment` | Source / Silver / Gold `revenue_by_customer` | Marketing tier | How the customer is classified in the CRM (`Premium`, `Standard`, `Basic`) |
| `segment_type` | Gold `customer_segmentation` only | Behavioral segment | How the customer behaves based on order history (`High-Value`, `Repeat`, `One-Time`, `Inactive`) *(assumption)* |

---

## Appendix A — Intentional data quality defects (source)

For test and validation reference. See `data-quality-strategy.md` for check mapping.

| Entity | Defect | Count |
|--------|--------|-------|
| customers | NULL `email` | 50 |
| customers | Duplicate `customer_id` | 10 |
| orders | NULL `customer_id` | 100 |
| orders | NULL `product_id` | 200 |
| orders | Orphan `customer_id` | 50 |
| orders | Orphan `product_id` | 30 |
| orders | Duplicate `order_id` | 20 |

---

## Appendix B — Schema inventory

| Schema | Table | Type |
|--------|-------|------|
| `bronze` | `customers` | Entity (raw) |
| `bronze` | `orders` | Entity (raw) |
| `bronze` | `products` | Entity (raw) |
| `silver` | `customers` | Entity (validated) |
| `silver` | `orders` | Entity (validated) |
| `silver` | `products` | Entity (validated) |
| `silver` | `dq_metrics` | Reporting |
| `gold` | `sales_by_product` | Aggregation |
| `gold` | `revenue_by_customer` | Aggregation |
| `gold` | `customer_segmentation` | Aggregation |
| `gold` | `daily_weekly_trends` | Aggregation |
| `audit` | `ingestion_log` | Audit |

---

## Appendix C — Design assumptions affecting this model

| ID | Assumption | Impact on model |
|----|------------|-----------------|
| DA-07 | Gold uses `Completed` orders only | Revenue metrics exclude Pending/Cancelled |
| DA-08 | `lifetime_value_actual` = per-customer `total_revenue` from qualifying orders | Gold field definition (GD-11) |
| DA-09 | Behavioral segmentation rules | `segment_type` values and logic (§11.3) |
| DA-10 | High-Value threshold = P75 of customer revenue among `total_orders >= 1` | `High-Value` vs `Repeat` boundary (GD-09) |
| GD-01–GD-14 | Finalized Gold engineering decisions | See `design-notes.md` §5.5 |

---

*Document version: 1.1 — Gold schemas finalized (GD-01–GD-14); aligned with design-notes.md §5.*
