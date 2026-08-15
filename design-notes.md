# Design Notes

> **Status:** Architecture design complete; not yet implemented or tested.  
> **Inputs:** `assignment/assignment-requirements.md`, `requirements-analysis.md`, `.cursor/rules/project-engineering.mdc`  
> **Companion docs:** `data-model.md`, `data-quality-strategy.md`, `database/schema.sql`

---

## 1. Architecture Overview

### 1.1 Pattern

A **batch medallion pipeline** on Databricks integrating three e-commerce CSV sources into layered Delta tables, with a Databricks SQL Dashboard consuming Gold outputs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SOURCE (offline + landing zone)                                            │
│  generate_sample_data.py → data/*.csv → upload to DBFS                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BRONZE — raw landing (Delta)                                               │
│  bronze.customers | bronze.orders | bronze.products                         │
│  + ingestion metadata                                                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SILVER — validated / curated (Delta)                                       │
│  silver.customers | silver.orders | silver.products                         │
│  + quality_check_result, is_valid                                           │
│  + silver.dq_metrics (quality report)                                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GOLD — business aggregations (Delta)                                       │
│  gold.sales_by_product | gold.revenue_by_customer                           │
│  gold.customer_segmentation | gold.daily_weekly_trends                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DASHBOARD — Databricks SQL Dashboard (queries against Gold)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design principles applied

| Principle | Application |
|-----------|-------------|
| Layer separation | Each layer reads only from the layer above; Dashboard reads Gold only |
| Bronze fidelity | Source values unchanged; only ingestion metadata added |
| Silver owns quality | All DQ checks, flagging, and metrics reporting in Silver |
| Gold owns semantics | Business rules for revenue, segmentation, and trends in Gold |
| Traceability | Invalid records retained and flagged; metrics auditable |
| Simplicity | Single-batch, single-environment design suitable for CE and assessment scope |

### 1.3 Major architecture decision

| | |
|---|---|
| **Decision** | Three-tier medallion (Bronze / Silver / Gold) with a separate consumption layer (Dashboard), orchestrated by per-layer Python entry points |
| **Reason** | Matches assignment requirements and project rules; clear boundaries for testing and documentation |
| **Alternative considered** | Single-notebook monolith executing all layers sequentially |
| **Why chosen** | Modular scripts align with required repository structure, support incremental development, and make AI-assisted iteration auditable per layer |

---

## 2. Source Layer

### 2.1 Responsibilities

| Responsibility | Owner |
|----------------|-------|
| Generate synthetic CSV files with realistic distributions | `src/data_generation/generate_sample_data.py` |
| Inject intentional quality defects at specified counts | Data generation script |
| Store committed copies in repo | `data/` |
| Land files for Databricks ingestion | DBFS path (see Section 8) |

### 2.2 Source files

| File | Rows | Role |
|------|------|------|
| `customers.csv` | 10,000 | Customer dimension |
| `orders.csv` | 100,000 | Order fact |
| `products.csv` | 500 | Product dimension |

### 2.3 Data generation design

| | |
|---|---|
| **Decision** | Python script using `faker` (or similar) for realistic values; deterministic seed for reproducibility |
| **Reason** | Assignment requires realistic data; reproducibility supports testing and debugging |
| **Alternative considered** | Static hand-crafted CSVs |
| **Why chosen** | Generator is a required deliverable; supports re-generation and defect injection with documented counts |

### 2.4 Defect injection strategy

| | |
|---|---|
| **Decision** | Inject each specified defect on **distinct rows** where possible; allow **limited overlap** only for orphan FK rows that also have NULL FKs, to approach the assignment's ~700 problematic-row figure |
| **Reason** | Itemized counts sum to 460; assignment states ~700 total problematic rows |
| **Alternative considered** | Strictly mutually exclusive defects (460 total only) |
| **Why chosen** | Overlap on FK-related rows is realistic (e.g., NULL `customer_id` rows cannot also be orphan FKs); generator will document exact final counts in `DATA_GENERATION_NOTES.md` |

> **Assumption:** Final problematic-row count will be validated after generation and documented; target is assignment-specified defect counts per type, with total near ~700.

### 2.5 Source layer constraints

- No real customer PII — synthetic data only.
- No credentials in generator or CSV output.

---

## Bronze Layer Design

> **Status:** Design approved; not yet implemented or tested.  
> **Inputs:** Approved Bronze Layer Design Specification, `data-model.md`, `DATA_GENERATION_NOTES.md` (runtime validation results), assignment Bronze requirements.  
> **Implementation:** `src/bronze/` (planned)

### 1. Architecture

Bronze is the raw landing layer between offline CSV sources and Silver validation.

```
data/*.csv  ──upload──►  DBFS landing zone
                              │
                              ▼
              ┌───────────────────────────────────┐
              │  PySpark Bronze ingestion          │
              │  01_ingest_customers.py            │
              │  02_ingest_orders.py               │
              │  03_ingest_products.py             │
              │  ingest_all.py (orchestrator)      │
              └───────────────┬───────────────────┘
                              │
              ┌───────────────┴───────────────────┐
              ▼                                   ▼
     bronze.customers                    audit.ingestion_log
     bronze.products                    (append run events)
     bronze.orders
              │
              ▼
         Silver layer (reads bronze.*; adds DQ columns)
```

**Flow:** CSV → DBFS landing → PySpark ingestion → Bronze Delta tables → Silver.

Bronze performs **ingestion and persistence only**. Silver reads Bronze tables unchanged (plus metadata) and owns all data quality detection and flagging.

### 2. Bronze Responsibilities

**Bronze performs only:**

| Responsibility | Detail |
|----------------|--------|
| Source ingestion | Read CSV from configured DBFS paths |
| Explicit type parsing | Apply defined Spark `StructType` per entity |
| Empty CSV field → NULL | `nullValue=""` and nullable schema fields |
| Ingestion metadata | Add `_ingest_timestamp`, `_source_file`, `_ingest_batch_id` |
| Schema/header validation | Verify expected columns present; reject extra/missing headers |
| Row-count validation | Fatal check against expected entity row counts |
| Delta persistence | Write managed Delta tables in schema `bronze` |
| Ingestion audit logging | Append run events to `audit.ingestion_log` |

**Bronze does NOT perform:**

| Excluded | Owner |
|----------|-------|
| Deduplication | Silver (uniqueness checks) |
| NULL repair | Silver |
| Foreign-key validation | Silver (referential integrity) |
| Filtering bad records | Silver / Gold (`is_valid` filter) |
| Quality flags (`quality_check_result`, `is_valid`) | Silver |
| Business transformations | Silver / Gold |
| Aggregations | Gold |

### 3. Source Files

| Source CSV | Expected rows | Bronze table |
|------------|---------------|--------------|
| `customers.csv` | **10,000** | `bronze.customers` |
| `products.csv` | **500** | `bronze.products` |
| `orders.csv` | **100,000** | `bronze.orders` |

Local repo copies live in `data/`; files are uploaded to DBFS before Bronze ingestion. Row counts are validated at runtime against these expected values (confirmed by data generation runtime validation).

### 4. Storage

**Assessment DBFS landing path (default, configurable):**

```
dbfs:/FileStore/medallion_pipeline/data/
```

| File | Default path |
|------|--------------|
| `customers.csv` | `dbfs:/FileStore/medallion_pipeline/data/customers.csv` |
| `products.csv` | `dbfs:/FileStore/medallion_pipeline/data/products.csv` |
| `orders.csv` | `dbfs:/FileStore/medallion_pipeline/data/orders.csv` |

| | |
|---|---|
| **Decision** | DBFS as the assessment landing zone |
| **Reason** | Assignment allows S3/DBFS; no external credentials required; aligns with existing architecture notes |
| **Alternative considered** | Unity Catalog Volumes, external S3 |
| **Why chosen** | Lowest setup friction for the assessment workflow |

Paths are defined in a shared `config` module and **must be configurable** (constants with override via Spark config or environment variables). Do **not** hardcode paths in every ingest script.

> **Note:** DBFS is the chosen assessment pattern. **Community Edition or specific workspace feature availability is not guaranteed** — verify in your Databricks environment before running.

**Bronze table format:** Delta Lake, schema `bronze`, no partitioning at assessment scale.

### 5. Bronze Tables

| Table | Source | Logical primary key |
|-------|--------|---------------------|
| `bronze.customers` | `customers.csv` | `customer_id` |
| `bronze.products` | `products.csv` | `product_id` |
| `bronze.orders` | `orders.csv` | `order_id` |

Write mode: **overwrite** per table per full pipeline run (see Section 11).

### 6. Explicit Schemas

Bronze uses **explicit Spark schemas** — not `inferSchema=True` — for reliable typing and early structural drift detection. All business columns are nullable at the schema level to preserve raw fidelity (including intentional defects).

**`bronze.customers` — business columns**

| Column | Spark type |
|--------|------------|
| `customer_id` | `IntegerType` |
| `customer_name` | `StringType` |
| `email` | `StringType` (nullable) |
| `country` | `StringType` |
| `signup_date` | `DateType` |
| `customer_segment` | `StringType` |
| `lifetime_value` | `DecimalType(18, 2)` |

**`bronze.products` — business columns**

| Column | Spark type |
|--------|------------|
| `product_id` | `IntegerType` |
| `product_name` | `StringType` |
| `category` | `StringType` |
| `price` | `DecimalType(18, 2)` |
| `cost` | `DecimalType(18, 2)` |
| `stock_quantity` | `IntegerType` |
| `reorder_level` | `IntegerType` |

**`bronze.orders` — business columns**

| Column | Spark type |
|--------|------------|
| `order_id` | `IntegerType` |
| `customer_id` | `IntegerType` (nullable) |
| `order_date` | `DateType` |
| `product_id` | `IntegerType` (nullable) |
| `quantity` | `IntegerType` |
| `unit_price` | `DecimalType(18, 2)` |
| `total_amount` | `DecimalType(18, 2)` |
| `order_status` | `StringType` |
| `payment_date` | `DateType` (nullable) |

**Header validation:** Explicit `StructType` alone does not reject unexpected CSV columns. Bronze ingest **must explicitly validate the CSV header row** against the expected column list before or during read, and fail fast on missing or extra columns.

### 7. Metadata

**Row-level metadata** (appended to every Bronze entity table):

| Column | Spark type | Purpose |
|--------|------------|---------|
| `_ingest_timestamp` | `TimestampType` | When the entity was ingested (`current_timestamp()`) |
| `_source_file` | `StringType` | Configured source path (e.g. DBFS CSV path) |
| `_ingest_batch_id` | `StringType` | Shared run identifier for the Bronze pipeline execution |

**Run-level audit table:** `audit.ingestion_log` (append-only, intentionally simple)

| Column | Type | Purpose |
|--------|------|---------|
| `run_id` | STRING | Same value as `_ingest_batch_id` |
| `layer` | STRING | `bronze` |
| `entity` | STRING | `customers`, `orders`, `products` |
| `status` | STRING | `SUCCESS` or `FAILED` |
| `row_count` | BIGINT | Rows written for the entity |
| `source_path` | STRING | Input CSV path |
| `target_table` | STRING | e.g. `bronze.customers` |
| `message` | STRING | Summary or error detail |
| `run_timestamp` | TIMESTAMP | When the audit row was written |

One audit row per entity ingest per run. No additional production observability infrastructure is required for the assessment.

### 8. NULL Contract

Layer contract from data generation through Bronze:

```
Python None  →  empty CSV field  →  Spark NULL  →  Delta NULL
```

| Rule | Detail |
|------|--------|
| CSV read | `nullValue=""` maps empty fields to Spark NULL |
| Bronze write | Do **not** replace NULLs with empty strings, zeros, or sentinel values |
| Downstream | Silver completeness checks evaluate true SQL NULLs |

Bronze must not `coalesce` NULL FKs, emails, or payment dates to defaults.

### 9. Data Quality Preservation

Generated source CSVs contain **intentional defects** for Silver validation. Bronze must **preserve every defect row and value** — no silent filtering.

| Defect | Expected count | Bronze behavior |
|--------|----------------|-----------------|
| NULL `email` | 50 | Load as NULL |
| Duplicate `customer_id` participant rows | 10 (5 pairs) | Load all rows; no dedup |
| NULL order `customer_id` | 100 | Load as NULL |
| NULL order `product_id` | 200 | Load as NULL |
| Orphan `customer_id` | 50 | Load ghost IDs (90,001–90,050) as-is |
| Orphan `product_id` | 30 | Load ghost IDs (901–930) as-is |
| Duplicate `order_id` participant rows | 20 (10 pairs) | Load all rows; no dedup |

**Total explicit defect-participating rows: 460.** Bronze does not validate these counts — Silver owns defect detection and metrics.

### 10. Validation

Bronze validation is **structural and operational only**. Silver data quality checks are **not** performed in Bronze.

| Validation | When | On failure |
|------------|------|------------|
| Source existence | Pre-read | Fatal — missing CSV on configured path |
| Header/schema validation | Pre-read / read | Fatal — missing or extra columns vs expected schema |
| Row-count validation | Post-read, pre-write | Fatal — count ≠ expected |
| Parsing / malformed records | Read (`FAILFAST` or equivalent) | Fatal — corrupt row |
| Post-write row-count check | After Delta write | Fatal — written count ≠ expected |

**Expected row counts:**

| Entity | Expected |
|--------|----------|
| customers | **10,000** |
| products | **500** |
| orders | **100,000** |

Row-count mismatch indicates wrong file, incomplete upload, or ingest error — not a row-level DQ issue to absorb.

### 11. Rerun Strategy

| Aspect | Behavior |
|--------|----------|
| Bronze table write mode | **Overwrite** (`mode("overwrite")`) — full refresh per run |
| Batch identity | New `_ingest_batch_id` / `run_id` on every orchestrated run |
| Audit log | **Append** to `audit.ingestion_log` — run history preserved |
| Source CSV on DBFS | Unchanged unless operator re-uploads |

Rerunning `ingest_all.py` replaces Bronze table contents idempotently for assessment re-runs. Metadata timestamps will differ per run.

### 12. Error Handling

| Category | Examples | Handling |
|----------|----------|----------|
| **Fatal** | Missing source file; invalid header/schema; malformed CSV row; row-count mismatch; Delta write failure | Stop ingest; log `FAILED` to `audit.ingestion_log`; raise with actionable message; non-zero exit |
| **Non-fatal** | NULL values; duplicate IDs; orphan foreign keys | **Ingest the row unchanged** — Silver detects and flags |

Fail fast on infrastructure and contract errors; never stop ingestion because a row is "bad" from a DQ perspective.

### 13. Implementation Structure

```
src/bronze/
├── config.py              # paths, expected row counts, table names
├── schemas.py             # explicit StructType per entity
├── ingest_utils.py        # read, validate, metadata, write, audit helpers
├── 01_ingest_customers.py
├── 02_ingest_orders.py
├── 03_ingest_products.py
└── ingest_all.py          # orchestrator: batch ID, run all ingests, audit
```

| File | Role |
|------|------|
| `config.py` | Configurable DBFS paths, expected counts, schema/table constants |
| `schemas.py` | Spark schemas for customers, products, orders |
| `ingest_utils.py` | Shared ingest pipeline (no Silver DQ logic) |
| `01`–`03` | Thin entity entry points |
| `ingest_all.py` | Creates shared batch ID; runs ingests; fail-fast on error |

No implementation code in this document — structure only.

### 14. Engineering Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| **BD-01** | DBFS landing for assessment CSVs | Assignment allows DBFS; configurable paths; no external credentials |
| **BD-02** | Explicit schemas, not inference | Stable types; documents contract; catches drift |
| **BD-03** | Delta Bronze tables | Project standard; ACID overwrite for reruns |
| **BD-04** | Overwrite per run | Idempotent full refresh at assessment scale |
| **BD-05** | Separate entity scripts + `ingest_all.py` orchestrator | Matches assignment repo layout; supports incremental development and testing |
| **BD-06** | Bronze does not perform DQ | Preserves 460 intentional defects for Silver; clear layer boundary |
| **BD-07** | Explicit CSV header validation | StructType alone does not reject extra/missing columns |
| **BD-08** | Simple `audit.ingestion_log` | Meets assignment metadata requirement without extra infrastructure |
| **BD-09** | Configurable input paths | Avoid hardcoding; support environment differences |
| **BD-10** | Fatal row-count validation | Protects Silver tests that expect exact defect populations |

**Constraints applied:**

- Do not claim Community Edition availability as guaranteed.
- Input paths must be configurable.
- Header validation is explicit, not assumed from schema read alone.
- Audit design stays minimal — no production observability stack.
- No unnecessary production infrastructure (streaming, MERGE ingest, partitioning) at Bronze.

---

## 4. Silver Layer

### 4.1 Responsibilities

1. Read Bronze tables.
2. Apply four quality check dimensions (see Section 10).
3. Populate `quality_check_result` per row.
4. Derive `is_valid` boolean for downstream use.
5. Write full Silver tables (all rows retained).
6. Produce `silver.dq_metrics` quality report.

### 4.2 Silver tables

| Table | Source | Notes |
|-------|--------|-------|
| `silver.customers` | `bronze.customers` | All source columns + quality columns |
| `silver.orders` | `bronze.orders` | All source columns + quality columns |
| `silver.products` | `bronze.products` | All source columns + quality columns |
| `silver.dq_metrics` | Derived | One row per check per pipeline run |

### 4.3 Silver quality columns

| Column | Type | Purpose |
|--------|------|---------|
| `quality_check_result` | STRING | `PASS` or comma-separated failure codes (e.g., `COMPLETENESS,UNIQUENESS`) |
| `is_valid` | BOOLEAN | `true` if `quality_check_result = 'PASS'` |
| `_silver_processed_timestamp` | TIMESTAMP | When Silver processing ran |

| | |
|---|---|
| **Decision** | Comma-separated failure codes in a single `quality_check_result` column |
| **Reason** | Assignment mandates this column; simple string format supports multiple failures per row |
| **Alternative considered** | JSON array or one column per check |
| **Why chosen** | Readable in SQL dashboards and tests without JSON parsing; sufficient for assessment scope |

### 4.4 Four quality checks (design resolution)

The assignment acceptance criteria require **four** checks. Repository structure lists five scripts. Design resolution:

| # | Check | Script | Scope |
|---|-------|--------|-------|
| 1 | **Completeness** | `01_quality_completeness.py` | NULL checks on `email` (customers), `customer_id` & `product_id` (orders) |
| 2 | **Uniqueness** | `02_quality_uniqueness.py` | Duplicate `customer_id` in customers; duplicate `order_id` in orders |
| 3 | **Type validation** | `03_quality_type_validation.py` | Valid enums, non-negative numerics, parseable dates *(4th mandatory check)* |
| 4 | **Referential integrity** | `04_quality_referential_integrity.py` | `orders.customer_id` → customers; `orders.product_id` → products |
| 5 | **Business logic** | `05_quality_business_logic.py` | `total_amount ≈ quantity × unit_price`; `Completed` orders should have `payment_date` *(repo structure; supports DQ depth)* |

| | |
|---|---|
| **Decision** | Fourth mandatory check = **type validation**; fifth script = **business logic** (implemented but reported separately in metrics) |
| **Reason** | Resolves ambiguity between three narrative checks and four acceptance-criteria checks; aligns with repo filenames |
| **Alternative considered** | Business logic as the fourth check; skip type validation |
| **Why chosen** | Type validation catches realistic production issues (bad enums, negative prices); business logic is valuable but more opinionated — keeping both satisfies repo structure without conflating check categories |

### 4.5 Uniqueness scope

| | |
|---|---|
| **Decision** | `customer_id` uniqueness evaluated **only on `silver.customers`**; `order_id` uniqueness **only on `silver.orders`** |
| **Reason** | `customer_id` is FK on orders — many orders per customer is expected |
| **Alternative considered** | Global uniqueness on `customer_id` across all tables |
| **Why chosen** | Would incorrectly flag valid order history |

### 4.6 Duplicate row handling

| | |
|---|---|
| **Decision** | Flag **all rows** participating in a duplicate key group as invalid (not just the second occurrence) |
| **Reason** | Avoids silently choosing an arbitrary "survivor" row |
| **Alternative considered** | Keep first occurrence, flag duplicates only |
| **Why chosen** | Safer for audit; downstream Gold uses `is_valid = true` only |

### 4.7 Referential integrity

- Build distinct valid key sets from **Silver customers/products** where `is_valid = true` on PK checks, **or** from Bronze parents before child checks — see check execution order in Section 10.
- Orders with NULL `customer_id` / `product_id` fail completeness first; orphan checks apply only when FK is non-NULL.

| | |
|---|---|
| **Decision** | Referential integrity runs **after** completeness and uniqueness on parent tables |
| **Reason** | Parent duplicate PKs undermine FK validation |
| **Alternative considered** | RI against Bronze parents directly |
| **Why chosen** | Validates the curated Silver parent keys used by analytics |

### 4.8 Silver orchestration

`create_silver_tables.py` executes checks in order:

1. Load Bronze → staging DataFrames
2. Completeness → Uniqueness → Type validation → Referential integrity → Business logic
3. Merge failure codes into `quality_check_result`
4. Write Silver entity tables
5. Compute and write `silver.dq_metrics`

---

## 5. Gold Layer

### 5.1 Responsibilities

1. Read **valid Silver rows only** (`is_valid = true`).
2. Build business aggregations per assignment spec.
3. Apply business semantics (order status filter, segmentation rules).
4. Write Gold Delta tables.

### 5.2 Gold tables

| Table | Script | Required by |
|-------|--------|-------------|
| `gold.sales_by_product` | `01_sales_by_product.sql` | Core acceptance criteria |
| `gold.revenue_by_customer` | `02_revenue_by_customer.sql` | Core acceptance criteria |
| `gold.daily_weekly_trends` | `03_daily_weekly_trends.sql` | Repo structure + common technical requirements (4 aggregations) |
| `gold.customer_segmentation` | `04_customer_segmentation.sql` | Core acceptance criteria |

| | |
|---|---|
| **Decision** | Implement **four** Gold tables including `daily_weekly_trends` |
| **Reason** | Resolves three-vs-four aggregation ambiguity; matches repository structure |
| **Alternative considered** | Only three tables from core acceptance criteria |
| **Why chosen** | Common technical requirements and repo explicitly include fourth SQL file; trends support dashboard date filters |

### 5.3 `daily_weekly_trends` definition

| Column | Description |
|--------|-------------|
| `order_date` | Date grain |
| `period_type` | `DAILY` or `WEEKLY` |
| `period_start` | Start of week for weekly rows |
| `total_orders` | Count of completed orders |
| `total_revenue` | Sum of `total_amount` |

> **Assumption:** Weekly aggregation uses ISO week or calendar week starting Monday — to be stated in `data-model.md`.

### 5.4 Order status filter for Gold

| | |
|---|---|
| **Decision** | Gold revenue and order counts include **`order_status = 'Completed'`** orders only |
| **Reason** | Pending/Cancelled orders should not inflate revenue metrics; standard e-commerce practice |
| **Alternative considered** | Include all order statuses |
| **Why chosen** | Produces meaningful business metrics; assignment does not specify but implied by revenue analytics context |

> **Assumption:** Not explicitly stated in assignment — documented here for testability.

### 5.5 `lifetime_value_actual`

| | |
|---|---|
| **Decision** | `lifetime_value_actual = SUM(total_amount)` of **completed, valid** orders per customer |
| **Reason** | Computed from trusted Silver order data; comparable to source `lifetime_value` for analysis |
| **Alternative considered** | Copy source `lifetime_value` from customers table |
| **Why chosen** | Demonstrates derived metric from pipeline; divergence from source field is expected and documentable |

### 5.6 Customer segmentation rules

Behavioral segments (distinct from source `customer_segment` Premium/Standard/Basic):

| `segment_type` | Rule *(assumption)* |
|----------------|---------------------|
| **Inactive** | Zero completed valid orders |
| **One-Time** | Exactly one completed valid order |
| **Repeat** | Two or more completed valid orders, and `total_revenue < high_value_threshold` |
| **High-Value** | Two or more completed valid orders, and `total_revenue >= high_value_threshold` |

| | |
|---|---|
| **Decision** | High-value threshold = **75th percentile** of customer `total_revenue` among customers with ≥1 completed order |
| **Reason** | Data-driven threshold adapts to generated data; no magic dollar amount |
| **Alternative considered** | Fixed dollar cutoff (e.g., $1,000) |
| **Why chosen** | Works with synthetic data of unknown scale; simple to implement and test |

> **Assumption:** Segmentation rules are not defined in the assignment. These rules will be codified in `data-model.md` and validated with unit tests.

### 5.7 Aggregation definitions

**Sales by Product** (from valid completed orders joined to valid products):

- `total_orders` = `COUNT(DISTINCT order_id)`
- `total_revenue` = `SUM(total_amount)`
- `avg_order_value` = `total_revenue / total_orders`

**Revenue by Customer** (from valid completed orders joined to valid customers):

- Same metrics plus `lifetime_value_actual` as defined above
- `customer_segment` = source marketing segment from customers table

**Customer Segmentation** — aggregated from per-customer revenue totals using rules above.

### 5.8 Gold orchestration

`create_gold_tables.py` runs SQL scripts in order, reading from `silver.*` and writing to `gold.*` using Spark SQL.

---

## 6. Dashboard Layer

### 6.1 Responsibilities

- Provide business-facing visualizations via **Databricks SQL Dashboard**.
- Query **Gold tables only**.
- Ship SQL in `dashboard_queries.sql`; document manual UI steps in `DASHBOARD_GUIDE.md`.

### 6.2 Required tiles

| Tile | Type | Gold source |
|------|------|-------------|
| Top 10 products by revenue | Bar chart | `gold.sales_by_product` |
| Customer revenue distribution | Histogram | `gold.revenue_by_customer` |
| Customer segmentation | Pie chart | `gold.customer_segmentation` |

### 6.3 Optional fourth tile

| | |
|---|---|
| **Decision** | Add a **line chart** of daily revenue from `gold.daily_weekly_trends` where `period_type = 'DAILY'` |
| **Reason** | Satisfies 3+ tiles requirement with meaningful use of fourth Gold table |
| **Alternative considered** | Exactly three tiles only |
| **Why chosen** | Uses fourth aggregation; supports date filter demonstration |

### 6.4 Dashboard filters

| Filter | Applies to | Source |
|--------|--------------|--------|
| **Order date range** | Trends tile (and orders-backed logic if parameterized) | `gold.daily_weekly_trends` |
| **Product category** | Top products tile | `gold.sales_by_product.category` |
| **Customer segment** (Premium/Standard/Basic) | Revenue histogram | `gold.revenue_by_customer.customer_segment` |
| **Country** | Revenue histogram | Requires join or pre-compute — see below |

| | |
|---|---|
| **Decision** | Add `country` to `gold.revenue_by_customer` during Gold build |
| **Reason** | Assignment requires filters but not which dimensions; country filter is useful and available in source |
| **Alternative considered** | Parameterized join to Silver customers at query time |
| **Why chosen** | Denormalizing one dimension into Gold simplifies dashboard SQL for assessment scope |

> **Assumption:** Filter dimensions are not specified in assignment; above choices are design assumptions.

### 6.5 Dashboard build approach

| | |
|---|---|
| **Decision** | SQL queries versioned in repo; dashboard assembled **manually** in Databricks SQL UI |
| **Reason** | Assignment describes configuring visualizations; CE has limited dashboard-as-code support |
| **Alternative considered** | Terraform/API-driven dashboard deployment |
| **Why chosen** | Avoids over-engineering; README + DASHBOARD_GUIDE.md provide reproducibility |

---

## 7. Data Flow

### 7.1 End-to-end sequence

```
1. generate_sample_data.py
      ↓  writes
2. data/*.csv  →  upload  →  DBFS source path
      ↓  ingest_all.py
3. bronze.*  (+ audit.ingestion_log)
      ↓  create_silver_tables.py
4. silver.*  + silver.dq_metrics
      ↓  create_gold_tables.py
5. gold.*
      ↓  manual / SQL
6. Databricks SQL Dashboard
```

### 7.2 Layer read/write matrix

| Layer | Reads from | Writes to |
|-------|------------|-----------|
| Source gen | — | `data/*.csv` |
| Bronze | DBFS CSVs | `bronze.*`, `audit.ingestion_log` |
| Silver | `bronze.*` | `silver.*`, `silver.dq_metrics` |
| Gold | `silver.*` (valid rows) | `gold.*` |
| Dashboard | `gold.*` | — (read-only) |

### 7.3 Check execution data flow (Silver)

```
bronze.customers ──┬──► completeness ──► uniqueness ──► type ──► silver.customers
bronze.orders    ──┤                                      │
bronze.products  ──┴──► completeness ──► uniqueness ──► type ──► silver.products
                                                              │
                    silver.customers/products (keys) ◄────────┤
                              │                               │
                              ▼                               ▼
                         RI check on orders ──► business logic ──► silver.orders
                                              │
                                              ▼
                                       silver.dq_metrics
```

No backwards flow. Gold never reads Bronze.

---

## 8. Storage Approach

### 8.1 Platform

| | |
|---|---|
| **Decision** | **Databricks DBFS** as primary landing and table storage for Community Edition |
| **Reason** | Assignment allows S3/DBFS; CE workflow is simplest with DBFS |
| **Alternative considered** | External S3 bucket |
| **Why chosen** | No AWS credentials required for assessment; README stays reproducible on CE |

> **Assumption:** Production would use S3 + Unity Catalog; assessment uses DBFS paths.

### 8.2 Path layout

| Purpose | Path *(configurable default)* |
|---------|-------------------------------|
| Source CSVs | `dbfs:/FileStore/medallion_pipeline/data/` |
| Local repo copies | `data/` (for generation and git) |

| | |
|---|---|
| **Decision** | Central `config` module with path constants; environment overrides via Spark config or env vars |
| **Reason** | Supports CE without hardcoding paths in every script |
| **Alternative considered** | Hardcoded paths in each script |
| **Why chosen** | Single place to update for README setup; no secrets required |

### 8.3 Table format

| | |
|---|---|
| **Decision** | **Delta Lake** for all Bronze, Silver, Gold, and audit tables |
| **Reason** | Project rules specify Delta Lake; ACID supports overwrite re-runs and time travel for debugging |
| **Alternative considered** | Parquet or managed Hive tables |
| **Why chosen** | Databricks-native, simple `saveAsTable` / SQL CTAS patterns |

### 8.4 Catalog and schema naming

| | |
|---|---|
| **Decision** | Hive metastore default catalog with schemas: `bronze`, `silver`, `gold`, `audit` |
| **Reason** | CE-compatible without Unity Catalog setup |
| **Alternative considered** | Unity Catalog `main.bronze.*` three-level names |
| **Why chosen** | Lower setup friction for assessment; documented in `database/setup-notes.md` |

> **Assumption:** CE cluster uses Hive metastore. If Unity Catalog is available, schemas map to `main.bronze` etc. via config toggle.

---

## 9. Table Strategy

### 9.1 Schema inventory

| Schema | Tables |
|--------|--------|
| `bronze` | `customers`, `orders`, `products` |
| `silver` | `customers`, `orders`, `products`, `dq_metrics` |
| `gold` | `sales_by_product`, `revenue_by_customer`, `daily_weekly_trends`, `customer_segmentation` |
| `audit` | `ingestion_log` |

### 9.2 Write strategy

| Layer | Strategy | Rationale |
|-------|----------|-----------|
| Bronze | Full overwrite per run | Simple assessment re-runs |
| Silver | Full overwrite per run | Derived entirely from Bronze |
| Gold | Full overwrite per run | Derived entirely from Silver |
| audit.ingestion_log | Append | Preserve history of ingest runs |

### 9.3 Partitioning

| | |
|---|---|
| **Decision** | **No partitioning** for assessment table sizes (~110K rows) |
| **Reason** | Partitioning adds complexity without benefit at this scale |
| **Alternative considered** | Partition Gold trends by `order_date` |
| **Why chosen** | Assignment discourages unnecessary complexity; full scans are fast enough |

### 9.4 Views

| View | Definition | Consumer |
|------|------------|----------|
| None required | `is_valid` column on Silver tables instead of separate views | Gold scripts filter `WHERE is_valid = true` |

| | |
|---|---|
| **Decision** | Use `is_valid` column rather than separate `silver_*_valid` views |
| **Reason** | Simpler object model; one table per entity with flags for audit |
| **Alternative considered** | Separate quarantine tables + valid views |
| **Why chosen** | Satisfies flag-only requirement with less object proliferation; invalid rows remain in same table |

---

## 10. Data Quality Architecture

### 10.1 Check summary

| Check | Entity | Rule | Failure code | Threshold |
|-------|--------|------|--------------|-----------|
| Completeness | customers | `email IS NOT NULL` | `COMPLETENESS` | >99% pass |
| Completeness | orders | `customer_id`, `product_id IS NOT NULL` | `COMPLETENESS` | >99% pass |
| Uniqueness | customers | `customer_id` unique | `UNIQUENESS` | 100% pass |
| Uniqueness | orders | `order_id` unique | `UNIQUENESS` | 100% pass |
| Type validation | all | Valid enums; dates parseable; prices/quantities ≥ 0 | `TYPE_VALIDATION` | >99% pass *(assumption, aligned with completeness tier)* |
| Referential integrity | orders | FK exists in valid parent keys | `REFERENTIAL_INTEGRITY` | >99.9% pass |
| Business logic | orders | `abs(total_amount - quantity*unit_price) < 0.01`; Completed → payment_date NOT NULL | `BUSINESS_LOGIC` | >99% pass *(assumption)* |

### 10.2 Type validation detail

| Field | Rule |
|-------|------|
| `customer_segment` | IN (`Premium`, `Standard`, `Basic`) |
| `order_status` | IN (`Pending`, `Completed`, `Cancelled`) |
| `quantity`, `unit_price`, `total_amount`, `price`, `cost` | `>= 0` |
| `signup_date`, `order_date`, `payment_date` | Not in future *(assumption)* |

### 10.3 Metrics report (`silver.dq_metrics`)

| Column | Description |
|--------|-------------|
| `run_id` | Pipeline run identifier |
| `check_name` | e.g., `COMPLETENESS_CUSTOMERS` |
| `entity` | `customers`, `orders`, `products` |
| `total_rows` | Rows evaluated |
| `passed_rows` | Rows passing check |
| `failed_rows` | Rows failing check |
| `pass_pct` | `passed_rows / total_rows * 100` |
| `threshold_pct` | Expected threshold |
| `threshold_met` | Boolean |
| `run_timestamp` | When metrics computed |

| | |
|---|---|
| **Decision** | Persist metrics as a Delta table, not stdout-only |
| **Reason** | Assignment requires quality reporting; table is queryable for tests and dashboard |
| **Alternative considered** | Print report to notebook output only |
| **Why chosen** | Auditable, testable, supports evidence in debugging notes |

### 10.4 Check ordering

1. Completeness (row-level, no dependencies)
2. Uniqueness (within-entity)
3. Type validation (row-level)
4. Referential integrity (cross-entity, uses parent keys)
5. Business logic (row-level, orders)

Failures accumulate into `quality_check_result`; `is_valid = true` only when result is `PASS`.

---

## 11. Invalid-Record Handling

### 11.1 Policy

| Rule | Implementation |
|------|----------------|
| Never silently delete | All rows written to Silver tables |
| Flag invalid rows | `quality_check_result`, `is_valid = false` |
| Preserve for audit | Full dataset queryable in Silver |
| Exclude from Gold | Gold filters `is_valid = true` |
| Report counts | `silver.dq_metrics` |

### 11.2 Major decision

| | |
|---|---|
| **Decision** | **In-place flagging** on Silver tables; no separate quarantine tables |
| **Reason** | Meets assignment flag requirement with minimal complexity |
| **Alternative considered** | Split into `silver.customers_valid` and `silver.customers_quarantine` |
| **Why chosen** | Single table per entity simplifies schema; `is_valid` provides clean Gold input. Quarantine pattern can be added in production if volume warrants. |

### 11.3 "Cleaning" interpretation

Silver **cleans** analytically (identifies and excludes invalid data from Gold) but does **not** physically remove rows. This reconciles business context ("clean and validate") with technical requirements ("flag, don't delete").

---

## 12. Error Handling

### 12.1 Error categories

| Category | Example | Handling |
|----------|---------|----------|
| **Fatal — pipeline stop** | Missing CSV; unreadable path; Bronze table write failure | Raise exception with context; non-zero exit; log to audit |
| **Fatal — schema mismatch** | Missing required column in CSV | Fail ingest with descriptive message listing expected vs actual columns |
| **Row-level — data quality** | NULL email; orphan FK | Flag in Silver; do not stop pipeline |
| **Warning** | Empty optional field within threshold | Log; continue |

### 12.2 Input validation (pre-ingest)

- Verify source path exists and is readable.
- Verify expected filename and non-zero file size.
- Validate required columns present before write.

### 12.3 Major decision

| | |
|---|---|
| **Decision** | Fail fast on **infrastructure and schema errors**; continue on **row-level DQ failures** |
| **Reason** | Infrastructure failures make the pipeline meaningless; DQ failures are the exercise focus |
| **Alternative considered** | Stop pipeline on first DQ failure |
| **Why chosen** | Produces full quality report in one run; matches production batch DQ patterns |

### 12.4 Error messaging standard

Errors include: layer name, script name, entity, path, and actionable detail. No secrets in error output.

---

## 13. Logging and Ingestion Metadata

### 13.1 Row-level metadata (Bronze)

See Section 3.3: `_ingest_timestamp`, `_source_file`, `_ingest_batch_id`.

### 13.2 Run-level audit table (`audit.ingestion_log`)

| Column | Description |
|--------|-------------|
| `run_id` | Unique run identifier |
| `layer` | `bronze`, `silver`, `gold` |
| `entity` | `customers`, `orders`, `products`, `pipeline` |
| `status` | `SUCCESS`, `FAILED` |
| `row_count` | Rows written or processed |
| `source_path` | Input path (Bronze) |
| `target_table` | Fully qualified table name |
| `message` | Status detail or error summary |
| `run_timestamp` | UTC timestamp |

| | |
|---|---|
| **Decision** | Append-only `audit.ingestion_log` for run-level events across all layers |
| **Reason** | Assignment requires ingestion metadata logging; single audit trail supports debugging |
| **Alternative considered** | Per-layer log files on DBFS |
| **Why chosen** | Queryable in Databricks; supports integration tests on row counts |

### 13.3 Logging mechanism

| | |
|---|---|
| **Decision** | Python `logging` module to driver stdout **plus** structured rows in `audit.ingestion_log` |
| **Reason** | Visible in notebook/job output and persisted for audit |
| **Alternative considered** | Log4j only / external observability platform |
| **Why chosen** | Zero extra infrastructure; sufficient for assessment |

---

## 14. Testing Architecture

### 14.1 Test tiers

| Tier | Scope | Framework *(assumption)* | Location |
|------|-------|--------------------------|----------|
| **Data quality tests** | Silver checks detect intentional defects | `pytest` + Spark local or Databricks connect | `tests/test_data_quality.py` |
| **Integration tests** | Bronze → Silver → Gold produces expected tables and row counts | `pytest` | `tests/test_pipeline_integration.py` |
| **Unit tests** | Segmentation rules; metric calculations | `pytest` | `tests/test_gold_logic.py` |

> **Assumption:** `pytest` chosen as standard Python test runner; not mandated by assignment.

### 14.2 DQ test design

Assert approximate flagged counts per failure type against generator-documented totals:

| Defect | Expected order of magnitude |
|--------|----------------------------|
| NULL emails | 50 |
| Duplicate customer_id | 10 |
| NULL customer_id (orders) | 100 |
| NULL product_id | 200 |
| Orphan customer_id | 50 |
| Orphan product_id | 30 |
| Duplicate order_id | 20 |

Tests verify **checks fire**, not that pass_pct meets thresholds on first run (intentional defects ensure thresholds may fail — report still required).

### 14.3 Integration test design

| Assertion | Purpose |
|-----------|---------|
| Bronze row counts match CSV line counts | Ingest completeness |
| Silver tables exist with `quality_check_result` populated | Silver ran |
| `silver.dq_metrics` has rows for each check | Report generated |
| Gold tables exist with expected columns | Gold ran |
| `gold.sales_by_product` row count ≤ valid product count | Sanity |

### 14.4 Test execution

| | |
|---|---|
| **Decision** | Tests runnable locally with Spark in local mode **or** against CE cluster via documented setup |
| **Reason** | CE may be only environment; local Spark speeds iteration |
| **Alternative considered** | Databricks-only tests |
| **Why chosen** | Flexibility for development; integration tests against CE before submission |

### 14.5 Current status

**No tests implemented or executed yet.** Strategy defined here for implementation phase.

---

## 15. Configuration Approach

### 15.1 Configuration module

Single shared module (e.g., `src/config.py` or `src/common/config.py`):

| Parameter | Example default |
|-----------|-----------------|
| `SOURCE_CSV_PATH` | `dbfs:/FileStore/medallion_pipeline/data` |
| `BRONZE_SCHEMA` | `bronze` |
| `SILVER_SCHEMA` | `silver` |
| `GOLD_SCHEMA` | `gold` |
| `AUDIT_SCHEMA` | `audit` |
| `INGEST_BATCH_ID` | Generated per run |

| | |
|---|---|
| **Decision** | Single Python config module with constants; optional override via environment variables |
| **Reason** | DRY path/schema references; no secrets needed |
| **Alternative considered** | YAML/JSON config files |
| **Why chosen** | Minimal files for assessment; avoids config parsing complexity |

### 15.2 Secrets

No credentials in config or repo. If S3 were used in production, secrets would come from Databricks secrets scope — not needed for CE DBFS design.

### 15.3 Schema definitions

Explicit Spark `StructType` schemas for CSV ingest co-located in config or `src/common/schemas.py`.

---

## 16. Deployment/Execution Approach

### 16.1 Execution model

| Step | Entry point | Environment |
|------|-------------|-------------|
| 0. Generate data | `python src/data_generation/generate_sample_data.py` | Local |
| 0b. Upload CSVs | Manual DBFS upload or notebook `%fs cp` | Databricks CE |
| 1. Setup schemas | `database/schema.sql` in SQL warehouse | Databricks CE |
| 2. Bronze | `ingest_all.py` as notebook or `spark-submit` | Databricks CE |
| 3. Silver | `create_silver_tables.py` | Databricks CE |
| 4. Gold | `create_gold_tables.py` | Databricks CE |
| 5. Dashboard | Manual per `DASHBOARD_GUIDE.md` | Databricks SQL |

### 16.2 Major decision

| | |
|---|---|
| **Decision** | **Databricks notebooks or `%run` orchestration** wrapping the Python modules — not a production job scheduler |
| **Reason** | Assignment does not require CI/CD or scheduled jobs; CE is the target |
| **Alternative considered** | Databricks Jobs with task dependencies |
| **Why chosen** | Simpler setup in README; Jobs can be noted as production consideration |

### 16.3 Run order (strict)

```
schema setup → ingest_all → create_silver_tables → create_gold_tables → dashboard queries
```

Each step is idempotent via Delta overwrite (except audit append).

### 16.4 Repository vs runtime

- Code and SQL live in Git.
- Data files generated locally, uploaded to DBFS.
- Delta tables exist only in Databricks metastore after execution.

---

## 17. Design Trade-offs

| Trade-off | Choice | Sacrifice | Benefit |
|-----------|--------|-----------|---------|
| **Overwrite vs incremental** | Full overwrite | Historical Bronze versions per run | Simple idempotent re-runs |
| **Flag vs quarantine tables** | In-place flag | Slightly wider Silver tables | Fewer objects; easier audit queries |
| **Explicit schema vs inference** | Explicit schema | Upfront schema maintenance | Reliable types; early drift detection |
| **DBFS vs S3** | DBFS for CE | Production parity | Zero credential setup for assessment |
| **Four Gold tables vs three** | Four (incl. trends) | Extra implementation time | Matches repo; richer dashboard |
| **Completed-only revenue** | Filter order status | Pending pipeline visibility | Meaningful revenue metrics |
| **Percentile-based High-Value** | P75 threshold | Fixed business rule clarity | Adapts to synthetic data scale |
| **Manual dashboard** | UI configuration | Dashboard-as-code automation | Appropriate for CE and scope |
| **No partitioning** | Unpartitioned Delta | Scale beyond ~110K rows | Minimal complexity |
| **Comma-separated DQ codes** | Simple string | Rich structured failure metadata | Easy SQL filtering and testing |

---

## 18. Production Considerations

Not required for assessment submission but inform design choices:

| Area | Assessment design | Production evolution |
|------|-------------------|---------------------|
| **Ingestion** | Full overwrite batch | Incremental append; CDC from source systems |
| **Storage** | DBFS | S3 + Unity Catalog; external locations |
| **Orchestration** | Manual/notebook run order | Databricks Jobs, Airflow, or Lakeflow |
| **DQ** | Batch flags + metrics table | DLT expectations; Great Expectations; alerting on threshold breach |
| **Secrets** | None | Databricks secret scopes; IAM roles |
| **Monitoring** | `audit.ingestion_log` | Datadog/Observability; data freshness SLAs |
| **Testing** | pytest suite | CI pipeline running tests on PR; environment promotion |
| **Dashboard** | Manual SQL dashboard | Lakeview dashboards as code; row-level security |
| **Data retention** | Full overwrite | Time-travel policies; Bronze retention vs Gold TTL |
| **PII** | Synthetic only | Masking/tokenization in Silver; column-level security |

### 18.1 What we intentionally defer

- Streaming / real-time ingestion
- MERGE-based slowly changing dimensions
- Multi-environment promotion (dev/staging/prod)
- Cost optimization and cluster autoscaling policies
- Row-level security on dashboard

Deferring these aligns with assignment guidance: **do not expand pipeline complexity at the expense of artifacts.**

---

## Appendix A — Design Assumptions Summary

| ID | Assumption |
|----|------------|
| DA-01 | Batch full-refresh pipeline, not incremental |
| DA-02 | Databricks Community Edition + DBFS as primary runtime |
| DA-03 | Delta Lake for all persistent tables |
| DA-04 | Hive metastore schemas: `bronze`, `silver`, `gold`, `audit` |
| DA-05 | Fourth DQ check = type validation; fifth script = business logic |
| DA-06 | Fourth Gold table = `daily_weekly_trends` |
| DA-07 | Gold metrics use `order_status = 'Completed'` only |
| DA-08 | `lifetime_value_actual` = sum of completed valid order amounts |
| DA-09 | Segmentation rules per Section 5.6 (not assignment-defined) |
| DA-10 | High-value threshold = P75 of customer revenue |
| DA-11 | Dashboard filters: date range, category, customer segment, country |
| DA-12 | `country` denormalized into `gold.revenue_by_customer` |
| DA-13 | Defect overlap allowed on FK-related rows to approach ~700 total |
| DA-14 | `pytest` for test execution |
| DA-15 | Code review notes live in `debugging-notes.md` |

---

## Appendix B — Related Documents

| Document | Purpose |
|----------|---------|
| `requirements-analysis.md` | Requirements and ambiguities |
| `data-model.md` | Detailed schemas *(to be updated to match this design)* |
| `data-quality-strategy.md` | DQ rules, thresholds, metrics *(to be updated)* |
| `database/schema.sql` | DDL for schemas and tables |
| `tool-specific/cursor-workflow/spec.md` | Cursor-facing specification summary |

---

*Document version: 1.0 — architecture design; implementation and testing not started.*
