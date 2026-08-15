# Data Quality Strategy

> **Status:** Silver design **finalized** (see `design-notes.md` §4). Silver DQ checks **not yet implemented or executed**. Silver runtime validation **not performed**.  
> **Inputs:** `assignment/assignment-requirements.md`, `requirements-analysis.md`, `design-notes.md`, `data-model.md`  
> **Implementation owner:** `src/silver/` (scripts `01`–`05`, `create_silver_tables.py`)

---

## 1. Purpose and Scope

This document defines the **data quality framework** for the Silver layer of the Databricks medallion pipeline. It specifies five check categories, how failures are flagged, how metrics are reported, and how each check will be tested against **intentional defects** in sample data.

### 1.1 Principles

| Principle | Implementation |
|-----------|----------------|
| Flag, never silently delete | All rows retained in Silver; `quality_check_result` and `is_valid` columns |
| Preserve traceability | Invalid rows queryable; failure codes identify which checks failed |
| Fail fast on infrastructure errors | Missing files, schema mismatch → stop pipeline |
| Continue on row-level DQ failures | Full quality report produced in one run |
| Gold consumes valid data only | `WHERE is_valid = true` in Gold aggregations |

### 1.2 Check execution order

Checks run in dependency order during `create_silver_tables.py`:

```
1. Completeness
2. Uniqueness
3. Type validation
4. Referential integrity
5. Business-rule validation
```

Failure codes **accumulate** per row. `is_valid = true` only when `quality_check_result = 'PASS'`.

### 1.3 Failure codes

| Code | Check category |
|------|----------------|
| `COMPLETENESS` | Section 2 |
| `UNIQUENESS` | Section 3 |
| `TYPE_VALIDATION` | Section 4 |
| `REFERENTIAL_INTEGRITY` | Section 5 |
| `BUSINESS_LOGIC` | Section 6 |

Multiple failures are stored as comma-separated codes in **canonical order**: `COMPLETENESS`, `UNIQUENESS`, `TYPE_VALIDATION`, `REFERENTIAL_INTEGRITY`, `BUSINESS_LOGIC` (SD-09). Example: `COMPLETENESS,UNIQUENESS`.

---

## 2. Completeness

### 2.1 Check definition

| Attribute | Value |
|-----------|-------|
| **Rule** | Critical fields must not be NULL |
| **Applicable table** | `silver.customers`, `silver.orders` |
| **Applicable columns** | `silver.customers.email`; `silver.orders.customer_id`, `silver.orders.product_id` |
| **Script** | `01_quality_completeness.py` |
| **Report name** | `COMPLETENESS_CUSTOMERS`, `COMPLETENESS_ORDERS` |

### 2.2 Detection logic

For each applicable table, evaluate every row:

| Table | Condition for PASS | Condition for FAIL |
|-------|-------------------|-------------------|
| `silver.customers` | `email IS NOT NULL` | `email IS NULL` |
| `silver.orders` | `customer_id IS NOT NULL AND product_id IS NOT NULL` | `customer_id IS NULL OR product_id IS NULL` |

Rows are evaluated independently per table. A NULL `customer_id` and NULL `product_id` on the same order row counts as **one completeness failure** on that row (single `COMPLETENESS` code, not two).

**Metric calculation:**

- `total_rows` = row count of the Silver entity table
- `passed_rows` = rows where completeness condition is true
- `failed_rows` = `total_rows - passed_rows`
- `pass_pct` = `(passed_rows / total_rows) × 100`

### 2.3 Expected failure cases

#### Intentional defects (assignment-specified)

| Table | Column | Defect | Expected count |
|-------|--------|--------|----------------|
| `customers` | `email` | NULL | **50** |
| `orders` | `customer_id` | NULL | **100** |
| `orders` | `product_id` | NULL | **200** |

**Expected minimum failed rows:**

| Report row | Minimum `failed_rows` |
|------------|----------------------|
| `COMPLETENESS_CUSTOMERS` | ≥ **50** |
| `COMPLETENESS_ORDERS` | ≥ **300** *(100 + 200; NULL FKs on distinct rows)* |

#### Additional failure cases (not intentionally injected)

| Case | Handling |
|------|----------|
| NULL in non-critical columns (e.g., `payment_date`) | **Not flagged** by completeness — `payment_date` is nullable by assignment |
| Empty string `""` vs NULL | Treat empty string as **non-NULL** unless generator uses NULL; if empty strings appear, type/business rules may apply separately |

### 2.4 Expected threshold

| Report row | Threshold | Source |
|------------|-----------|--------|
| `COMPLETENESS_CUSTOMERS` | **>99%** pass | Assignment template |
| `COMPLETENESS_ORDERS` | **>99%** pass | Assignment template |

With intentional defects, thresholds **may not be met** on first run. The report must still be produced; `threshold_met` will reflect actual vs required.

**Sanity bounds (customers):** 50 NULL emails / 10,000 rows = 99.5% pass → threshold **met**.  
**Sanity bounds (orders):** 300 NULL FKs / 100,000 rows = 99.7% pass → threshold **met**.

> These sanity calculations are **expected outcomes**, not verified results. No checks have been executed yet.

### 2.5 How the record is flagged

| Step | Action |
|------|--------|
| 1 | If completeness condition fails, append `COMPLETENESS` to `quality_check_result` |
| 2 | If `quality_check_result` was `PASS`, replace with `COMPLETENESS` |
| 3 | Set `is_valid = false` when any failure code is present |

### 2.6 What happens after failure

| Action | Detail |
|--------|--------|
| Row retained | Row remains in `silver.customers` or `silver.orders` |
| Excluded from Gold | Row excluded when `is_valid = false` |
| No imputation | NULL values are **not** filled or defaulted |
| Downstream RI | Orders with NULL `customer_id` or `product_id` skip referential integrity evaluation *(FK check applies only when FK IS NOT NULL)* |

### 2.7 How the check will be tested

| Test | Assertion |
|------|-----------|
| `test_completeness_customers_null_email` | Count of `email IS NULL AND quality_check_result LIKE '%COMPLETENESS%'` ≥ **50** |
| `test_completeness_orders_null_customer_id` | Count of `customer_id IS NULL` rows flagged with `COMPLETENESS` ≥ **100** |
| `test_completeness_orders_null_product_id` | Count of `product_id IS NULL` rows flagged with `COMPLETENESS` ≥ **200** |
| `test_completeness_valid_rows_pass` | Rows with non-null critical fields do not have `COMPLETENESS` as sole failure *(unless other checks fail)* |

Tests will run after Silver implementation against generated sample data. **No test results exist yet.**

### 2.8 Contribution to quality report

One row per entity in `silver.dq_metrics`:

| `check_name` | `entity` | `threshold_pct` |
|--------------|----------|-----------------|
| `COMPLETENESS_CUSTOMERS` | `customers` | 99.00 |
| `COMPLETENESS_ORDERS` | `orders` | 99.00 |

---

## 3. Uniqueness

### 3.1 Check definition

| Attribute | Value |
|-----------|-------|
| **Rule** | Primary key values must be unique within their entity table |
| **Applicable table** | `silver.customers`, `silver.orders` |
| **Applicable columns** | `silver.customers.customer_id`; `silver.orders.order_id` |
| **Script** | `02_quality_uniqueness.py` |
| **Report name** | `UNIQUENESS_CUSTOMERS`, `UNIQUENESS_ORDERS` |

> **Scope note:** `customer_id` uniqueness applies to the **customers table only**. `customer_id` on orders is a foreign key and is expected to repeat across many rows.

### 3.2 Detection logic

1. Identify key values that appear more than once: `GROUP BY key HAVING COUNT(*) > 1`
2. Flag **all rows** whose key value belongs to a duplicate group

| Table | Key column | PASS condition |
|-------|------------|----------------|
| `silver.customers` | `customer_id` | Key appears exactly once |
| `silver.orders` | `order_id` | Key appears exactly once |

**Metric calculation:** Same pattern as completeness — one pass/fail per row.

### 3.3 Expected failure cases

#### Intentional defects (assignment-specified)

| Table | Column | Defect | Expected count of duplicate key values | Expected minimum flagged rows |
|-------|--------|--------|----------------------------------------|------------------------------|
| `customers` | `customer_id` | Duplicate PK | **10** rows involved | ≥ **10** *(all rows in duplicate groups)* |
| `orders` | `order_id` | Duplicate PK | **20** rows involved | ≥ **20** |

If duplicates are injected as **5 duplicate pairs** (10 rows) and **10 duplicate pairs** (20 rows), flagged row counts match row counts above. Exact duplicate group sizes depend on generator implementation — documented in `DATA_GENERATION_NOTES.md`.

#### Additional failure cases (not intentionally injected)

| Case | Handling |
|------|----------|
| `product_id` duplicates in products | Flagged if generator or source introduces them; **not** an assignment intentional defect |
| Exact duplicate rows (all columns identical) | Caught by PK uniqueness if `order_id` / `customer_id` duplicates |

### 3.4 Expected threshold

| Report row | Threshold | Source |
|------------|-----------|--------|
| `UNIQUENESS_CUSTOMERS` | **100%** pass | Assignment template |
| `UNIQUENESS_ORDERS` | **100%** pass | Assignment template |

With intentional duplicates, thresholds **will not be met**. This is expected and demonstrates the check is working.

**Expected pass rate (customers):** (10,000 − 10) / 10,000 = **99.9%** — threshold **not met**.  
**Expected pass rate (orders):** (100,000 − 20) / 100,000 = **99.98%** — threshold **not met**.

> Expected outcomes only — not verified by execution.

### 3.5 How the record is flagged

Append `UNIQUENESS` to `quality_check_result` for every row in a duplicate key group. All participants in the group are flagged, not just the second occurrence.

### 3.6 What happens after failure

| Action | Detail |
|--------|--------|
| Row retained | Duplicate rows remain in Silver |
| Excluded from Gold | Duplicate-key rows excluded via `is_valid = false` |
| No deduplication | No "survivor" row is chosen |
| RI impact | Duplicate `customer_id` in customers weakens parent key set; RI uses keys from customers after uniqueness is evaluated |

### 3.7 How the check will be tested

| Test | Assertion |
|------|-----------|
| `test_uniqueness_customers_duplicates` | Rows with duplicate `customer_id` flagged `UNIQUENESS` ≥ **10** rows |
| `test_uniqueness_orders_duplicates` | Rows with duplicate `order_id` flagged `UNIQUENESS` ≥ **20** rows |
| `test_uniqueness_all_group_members_flagged` | For each duplicate key, **all** rows in group have `UNIQUENESS` in result |
| `test_uniqueness_customer_id_not_checked_on_orders` | Repeating `customer_id` on orders does **not** trigger `UNIQUENESS` |

**No test results exist yet.**

### 3.8 Contribution to quality report

| `check_name` | `entity` | `threshold_pct` |
|--------------|----------|-----------------|
| `UNIQUENESS_CUSTOMERS` | `customers` | 100.00 |
| `UNIQUENESS_ORDERS` | `orders` | 100.00 |

---

## 4. Type Validation

### 4.1 Check definition

| Attribute | Value |
|-----------|-------|
| **Rule** | Values must conform to expected data types, allowed enumerations, and basic value-range constraints |
| **Applicable table** | `silver.customers`, `silver.orders`, `silver.products` |
| **Applicable columns** | See Section 4.2 |
| **Script** | `03_quality_type_validation.py` |
| **Report name** | `TYPE_VALIDATION_CUSTOMERS`, `TYPE_VALIDATION_ORDERS`, `TYPE_VALIDATION_PRODUCTS` |

> This is the **fourth mandatory check** per acceptance criteria (design decision DA-05).

### 4.2 Detection logic

| Table | Column | Validation rule | FAIL when |
|-------|--------|-----------------|-----------|
| `customers` | `customer_segment` | Enum | Not in (`Premium`, `Standard`, `Basic`) |
| `customers` | `signup_date` | Date range | `signup_date > REFERENCE_DATE` where **`REFERENCE_DATE = 2026-08-15`** (fixed; SD-06 — do not use `current_date()`) |
| `customers` | `lifetime_value` | Non-negative | `< 0` |
| `orders` | `order_status` | Enum | Not in (`Pending`, `Completed`, `Cancelled`) |
| `orders` | `order_date` | Date range | `order_date > REFERENCE_DATE` |
| `orders` | `payment_date` | Date range | `payment_date > REFERENCE_DATE` when not null |
| `orders` | `quantity` | Non-negative integer | `< 0` |
| `orders` | `unit_price`, `total_amount` | Non-negative | `< 0` |
| `products` | `price`, `cost` | Non-negative | `< 0` |
| `products` | `stock_quantity`, `reorder_level` | Non-negative integer | `< 0` |

A row fails if **any** type rule on that row fails. One `TYPE_VALIDATION` code per row regardless of how many columns fail.

> **Design decision (SD-06):** Future-date checks use fixed **`REFERENCE_DATE = 2026-08-15`**, matching `DATA_GENERATION_NOTES.md`. This supersedes any prior use of `current_date()` for Silver type validation.

### 4.3 Expected failure cases

#### Intentional defects (assignment-specified)

**None.** The assignment does not inject type validation defects. Intentional bad data targets completeness, uniqueness, and referential integrity only.

#### Expected behavior on sample data

| Expectation | Detail |
|-------------|--------|
| Primary dataset | Type validation should **pass** for the vast majority of rows if generator produces valid enums and dates |
| `pass_pct` | Expected near **100%** on clean generated data |
| Threshold | **>99%** *(assumption, aligned with completeness tier)* |

Type validation tests will include **unit fixtures** with invalid enums and negative values to prove detection logic independent of the main CSV defects.

### 4.4 Expected threshold

| Report row | Threshold |
|------------|-----------|
| `TYPE_VALIDATION_CUSTOMERS` | **>99%** *(assumption)* |
| `TYPE_VALIDATION_ORDERS` | **>99%** *(assumption)* |
| `TYPE_VALIDATION_PRODUCTS` | **>99%** *(assumption)* |

### 4.5 How the record is flagged

Append `TYPE_VALIDATION` to `quality_check_result` when any type rule fails on the row.

### 4.6 What happens after failure

| Action | Detail |
|--------|--------|
| Row retained | Row stays in Silver |
| Excluded from Gold | `is_valid = false` |
| No type coercion | Invalid values are not cast or corrected in Silver |

### 4.7 How the check will be tested

| Test | Approach |
|------|----------|
| `test_type_validation_enum_customer_segment` | Fixture row with invalid segment → flagged `TYPE_VALIDATION` |
| `test_type_validation_enum_order_status` | Fixture row with invalid status → flagged |
| `test_type_validation_negative_price` | Fixture product with negative `price` → flagged |
| `test_type_validation_sample_data_pass_rate` | On full sample data, `pass_pct` ≥ 99% for each entity |

**No test results exist yet.**

### 4.8 Contribution to quality report

| `check_name` | `entity` | `threshold_pct` |
|--------------|----------|-----------------|
| `TYPE_VALIDATION_CUSTOMERS` | `customers` | 99.00 |
| `TYPE_VALIDATION_ORDERS` | `orders` | 99.00 |
| `TYPE_VALIDATION_PRODUCTS` | `products` | 99.00 |

---

## 5. Referential Integrity

### 5.1 Check definition

| Attribute | Value |
|-----------|-------|
| **Rule** | Foreign key values in orders must exist in the corresponding parent table |
| **Applicable table** | `silver.orders` |
| **Applicable columns** | `customer_id` → `bronze.customers.customer_id`; `product_id` → `bronze.products.product_id` |
| **Script** | `04_quality_referential_integrity.py` |
| **Report name** | `REFERENTIAL_INTEGRITY_ORDERS` |

### 5.2 Detection logic

For each row in `silver.orders`:

| Condition | Result |
|-----------|--------|
| `customer_id IS NULL` | Skip customer FK check *(completeness already flagged)* |
| `customer_id IS NOT NULL` AND not in parent `customer_id` set | FAIL → `REFERENTIAL_INTEGRITY` |
| `product_id IS NULL` | Skip product FK check |
| `product_id IS NOT NULL` AND not in parent `product_id` set | FAIL → `REFERENTIAL_INTEGRITY` |

**Parent key set (SD-04):** Distinct `customer_id` / `product_id` values from **`bronze.customers`** and **`bronze.products`** respectively (existence-based; not filtered by parent `is_valid`).

A row fails if **either** FK is orphan when non-null. One `REFERENTIAL_INTEGRITY` code per row.

**Metric calculation:** Evaluated only on `silver.orders` rows where at least one FK is non-null and checked.

### 5.3 Expected failure cases

#### Intentional defects (assignment-specified)

| Table | Column | Defect | Expected count |
|-------|--------|--------|----------------|
| `orders` | `customer_id` | Value not in `customers` table | **50** |
| `orders` | `product_id` | Value not in `products` table | **30** |

**Expected minimum flagged rows:** ≥ **80** orphan FK rows *(50 + 30 on distinct rows, assuming no overlap with NULL FK rows)*.

> NULL `customer_id` / `product_id` rows are **not** orphan FK failures — they are completeness failures. The 50 orphan `customer_id` and 30 orphan `product_id` defects are on rows with **non-null** invalid FK values.

#### Additional failure cases

| Case | Handling |
|------|----------|
| FK references duplicate parent PK | Parent row may itself be invalid; RI still evaluates key existence in parent table |
| FK references invalid but existing parent row | RI passes if key exists, even if parent `is_valid = false` |

### 5.4 Expected threshold

| Report row | Threshold | Source |
|------------|-----------|--------|
| `REFERENTIAL_INTEGRITY_ORDERS` | **>99.9%** pass | Assignment template |

**Sanity bound:** 80 orphan rows / 100,000 = 99.92% pass → threshold **met** *(expected, not verified)*.

### 5.5 How the record is flagged

Append `REFERENTIAL_INTEGRITY` to `quality_check_result` when a non-null FK does not exist in the parent table.

### 5.6 What happens after failure

| Action | Detail |
|--------|--------|
| Row retained | Orphan order rows remain in `silver.orders` |
| Excluded from Gold | Cannot join to valid dimensions in Gold |
| No FK repair | Orphan IDs are not nulled or remapped |

### 5.7 How the check will be tested

| Test | Assertion |
|------|-----------|
| `test_ri_orphan_customer_id` | Orphan `customer_id` rows flagged ≥ **50** |
| `test_ri_orphan_product_id` | Orphan `product_id` rows flagged ≥ **30** |
| `test_ri_null_fk_not_flagged_ri` | NULL FK rows have `COMPLETENESS` but not `REFERENTIAL_INTEGRITY` alone for that null |
| `test_ri_valid_fk_passes` | Orders with valid FKs to existing parents pass RI |

**No test results exist yet.**

### 5.8 Contribution to quality report

| `check_name` | `entity` | `threshold_pct` |
|--------------|----------|-----------------|
| `REFERENTIAL_INTEGRITY_ORDERS` | `orders` | 99.90 |

---

## 6. Business-Rule Validation

### 6.1 Check definition

| Attribute | Value |
|-----------|-------|
| **Rule** | Entity records must satisfy domain business rules beyond type and referential constraints |
| **Applicable table** | `silver.products`, `silver.orders` |
| **Script** | `05_quality_business_logic.py` |
| **Report name** | `BUSINESS_LOGIC_PRODUCTS`, `BUSINESS_LOGIC_ORDERS` |

> Implemented per repository structure. Reported separately in `silver.dq_metrics`.

### 6.2 Detection logic

| Rule ID | Entity | Business rule | FAIL when |
|---------|--------|---------------|-----------|
| BR-01 | products | Margin | `price <= cost` |
| BR-02 | orders | Order total consistency | `ABS(total_amount - (quantity * unit_price)) > 0.01` |
| BR-03 | orders | Completed orders require payment date | `order_status = 'Completed' AND payment_date IS NULL` |
| BR-04 | orders | Pending/Cancelled payment | `order_status IN ('Pending','Cancelled') AND payment_date IS NOT NULL` |
| BR-05 | orders | Order after signup | Resolvable customer AND `order_date < customer_signup_date` *(lookup: `MIN(signup_date)` per `customer_id` from Bronze; SD-01)* |

BR-05 uses an internal validation lookup only; Silver entity tables are not deduplicated. Skipped when `customer_id` IS NULL or orphan.

A row fails if **any** business rule on that entity fails. One `BUSINESS_LOGIC` code per row.

### 6.3 Expected failure cases

#### Intentional defects (assignment-specified)

**None.** The assignment does not inject business-logic defects (e.g., mismatched `total_amount`).

#### Expected behavior on sample data

| Expectation | Detail |
|-------------|--------|
| Generator | Should produce `total_amount = quantity × unit_price` for realistic rows |
| `pass_pct` | Expected near **100%** if generator is consistent |
| Threshold | **>99%** *(assumption)* |

Business-rule tests will use **unit fixtures** with deliberate arithmetic mismatch and completed orders without `payment_date`.

### 6.4 Expected threshold

| Report row | Threshold |
|------------|-----------|
| `BUSINESS_LOGIC_ORDERS` | **>99%** *(assumption)* |

### 6.5 How the record is flagged

Append `BUSINESS_LOGIC` to `quality_check_result` when any business rule fails.

### 6.6 What happens after failure

| Action | Detail |
|--------|--------|
| Row retained | Row stays in Silver |
| Excluded from Gold | Revenue aggregations exclude invalid orders |
| No recalculation | `total_amount` is not auto-corrected |

### 6.7 How the check will be tested

| Test | Approach |
|------|----------|
| `test_business_logic_amount_mismatch` | Fixture: `total_amount ≠ quantity × unit_price` → flagged |
| `test_business_logic_completed_without_payment` | Fixture: `Completed` + NULL `payment_date` → flagged |
| `test_business_logic_sample_data_pass_rate` | On full sample data, `pass_pct` ≥ 99% |

**No test results exist yet.**

### 6.8 Contribution to quality report

| `check_name` | `entity` | `threshold_pct` |
|--------------|----------|-----------------|
| `BUSINESS_LOGIC_PRODUCTS` | products | 99.00 |
| `BUSINESS_LOGIC_ORDERS` | orders | 99.00 |

---

## 7. Intentional Bad Data — Complete Reference

All defects specified in the assignment. These **must** be present in generated sample data and **must** be detected by the corresponding Silver checks.

### 7.1 `customers.csv`

| # | Column | Defect type | Check | Count | Expected failure code |
|---|--------|-------------|-------|-------|----------------------|
| 1 | `email` | NULL | Completeness | **50** | `COMPLETENESS` |
| 2 | `customer_id` | Duplicate PK | Uniqueness | **10** rows in duplicate groups | `UNIQUENESS` |

### 7.2 `orders.csv`

| # | Column | Defect type | Check | Count | Expected failure code |
|---|--------|-------------|-------|-------|----------------------|
| 3 | `customer_id` | NULL | Completeness | **100** | `COMPLETENESS` |
| 4 | `product_id` | NULL | Completeness | **200** | `COMPLETENESS` |
| 5 | `customer_id` | Orphan FK | Referential integrity | **50** | `REFERENTIAL_INTEGRITY` |
| 6 | `product_id` | Orphan FK | Referential integrity | **30** | `REFERENTIAL_INTEGRITY` |
| 7 | `order_id` | Duplicate PK | Uniqueness | **20** rows in duplicate groups | `UNIQUENESS` |

### 7.3 `products.csv`

**No intentional defects** specified in the assignment.

### 7.4 Totals and overlap

| Metric | Value |
|--------|-------|
| Itemized defect rows (if mutually exclusive) | **460** (50+10+100+200+50+30+20) |
| Assignment stated total | **~700** problematic rows (~0.7%) |
| Overlap strategy | Generator may allow limited overlap on unrelated defects; NULL FK rows cannot also be orphan FK rows. Final counts documented in `DATA_GENERATION_NOTES.md` after generation. |

### 7.5 Defect-to-check mapping summary

```
customers.email NULL (50)           → COMPLETENESS
customers.customer_id duplicate (10) → UNIQUENESS
orders.customer_id NULL (100)       → COMPLETENESS
orders.product_id NULL (200)      → COMPLETENESS
orders.customer_id orphan (50)      → REFERENTIAL_INTEGRITY
orders.product_id orphan (30)       → REFERENTIAL_INTEGRITY
orders.order_id duplicate (20)      → UNIQUENESS
```

---

## 8. Flagging and Invalid-Record Handling

### 8.1 Row-level flagging model

| Column | Type | Set when |
|--------|------|----------|
| `quality_check_result` | STRING | After all checks: `PASS` or comma-separated failure codes |
| `is_valid` | BOOLEAN | `true` iff `quality_check_result = 'PASS'` |
| `_silver_processed_timestamp` | TIMESTAMP | End of Silver processing |

### 8.2 Flagging rules

| Rule | Detail |
|------|--------|
| Accumulation | Each failed check appends its code in canonical order: `COMPLETENESS`, `UNIQUENESS`, `TYPE_VALIDATION`, `REFERENTIAL_INTEGRITY`, `BUSINESS_LOGIC` (SD-09) |
| Initial value | Before checks: treat as empty; after all pass: `PASS` |
| Multiple failures | e.g. duplicate `customer_id` with NULL `email` → `COMPLETENESS,UNIQUENESS` |
| No silent drop | Row count in Silver entity tables = row count in Bronze entity tables |

### 8.3 Post-failure data flow

```
Invalid row (is_valid = false)
    ├── Remains in silver.* for audit and debugging
    ├── Appears in silver.dq_metrics failed_row counts
    ├── Excluded from Gold aggregations
    └── Available for manual investigation via SQL
```

### 8.4 What we do NOT do

- Delete or filter rows out of Silver
- Auto-correct NULLs, duplicates, or orphan FKs
- Impute missing values
- Choose a "winning" row among duplicates

---

## 9. Quality Metrics Report

### 9.1 Output table: `silver.dq_metrics`

Persisted Delta table; **append** mode per `run_id` (SD-03). Entity tables use **overwrite** per run.

**Grain:** one metric row per **`(run_id, entity, check_name)`** for checks configured on that entity.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | STRING | Pipeline run identifier (matches `_ingest_batch_id`) |
| `check_name` | STRING | Unique check identifier (see Section 9.2) |
| `entity` | STRING | `customers`, `orders`, or `products` |
| `total_rows` | BIGINT | Rows evaluated |
| `passed_rows` | BIGINT | Rows passing this check |
| `failed_rows` | BIGINT | Rows failing this check |
| `pass_pct` | DECIMAL(5,2) | `(passed_rows / total_rows) × 100` |
| `threshold_pct` | DECIMAL(5,2) | Required threshold for this check |
| `threshold_met` | BOOLEAN | `pass_pct` meets threshold *(per check comparison rules below)* |
| `run_timestamp` | TIMESTAMP | UTC timestamp when metrics computed |

### 9.2 Report rows (one per `(run_id, entity, check_name)` per run)

| `check_name` | `entity` | `threshold_pct` | `threshold_met` comparison |
|--------------|----------|-----------------|---------------------------|
| `COMPLETENESS_CUSTOMERS` | customers | 99.00 | `pass_pct > 99` |
| `UNIQUENESS_CUSTOMERS` | customers | 100.00 | `pass_pct = 100` |
| `TYPE_VALIDATION_CUSTOMERS` | customers | 99.00 | `pass_pct > 99` |
| `TYPE_VALIDATION_PRODUCTS` | products | 99.00 | `pass_pct > 99` |
| `BUSINESS_LOGIC_PRODUCTS` | products | 99.00 | `pass_pct > 99` |
| `COMPLETENESS_ORDERS` | orders | 99.00 | `pass_pct > 99` |
| `UNIQUENESS_ORDERS` | orders | 100.00 | `pass_pct = 100` |
| `TYPE_VALIDATION_ORDERS` | orders | 99.00 | `pass_pct > 99` |
| `REFERENTIAL_INTEGRITY_ORDERS` | orders | 99.90 | `pass_pct > 99.9` |
| `BUSINESS_LOGIC_ORDERS` | orders | 99.00 | `pass_pct > 99` |

**Total: 10 metric rows per complete Silver run** (customers = 3, products = 2, orders = 5).

### 9.3 How each check contributes

| Check category | `total_rows` basis | `failed_rows` meaning |
|----------------|-------------------|---------------------|
| Completeness | All rows in entity table | Rows with NULL critical field(s) |
| Uniqueness | All rows in entity table | Rows participating in duplicate key groups |
| Type validation | All rows in entity table | Rows failing any type rule |
| Referential integrity | All rows in `orders` | Rows with non-null orphan FK |
| Business logic | All rows in `products` or `orders` | Rows failing any business rule on that entity |

### 9.4 Presentation

| Output | Purpose |
|--------|---------|
| `silver.dq_metrics` table | Queryable, testable, persistent report |
| Notebook / log summary | Human-readable pass/fail summary printed after Silver run |
| `debugging-notes.md` | Manual capture of unexpected metric results during development |

### 9.5 Expected report behavior on intentional data

| Check | `threshold_met` expectation *(not verified)* |
|-------|-----------------------------------------------|
| `COMPLETENESS_*` | **true** — defect rate below 1% |
| `UNIQUENESS_*` | **false** — intentional duplicates prevent 100% |
| `TYPE_VALIDATION_*` | **true** — no intentional type defects |
| `REFERENTIAL_INTEGRITY_ORDERS` | **true** — 80 orphans / 100K below 0.1% failure |
| `BUSINESS_LOGIC_PRODUCTS` | **true** — no intentional business-rule defects on products |
| `BUSINESS_LOGIC_ORDERS` | **true** — no intentional business-rule defects |

> A report showing `UNIQUENESS threshold_met = false` **proves the framework is working**, not that the pipeline is broken.

---

## 10. Testing Strategy Summary

### 10.1 Test location

`tests/test_data_quality.py` (and unit fixtures in `tests/test_gold_logic.py` where applicable).

### 10.2 Test categories

| Category | Purpose |
|----------|---------|
| **Defect detection tests** | Verify each intentional defect type is flagged with correct code and minimum count |
| **Negative tests** | Verify valid rows are not falsely flagged for that check |
| **Scope tests** | Verify `customer_id` uniqueness not applied to orders |
| **Metrics tests** | Verify `silver.dq_metrics` has **10** rows per `run_id` with correct columns |
| **Fixture tests** | Type and business-rule checks proven with small synthetic inputs |

### 10.3 Success criteria for DQ tests

| Criterion | Detail |
|-----------|--------|
| Detection | Each assignment intentional defect type detected ≥ expected count |
| No false scope | Orders not flagged for `customer_id` uniqueness |
| Report populated | `silver.dq_metrics` contains all **10** check rows per `run_id` |
| Pipeline continues | Silver completes even when thresholds not met |

### 10.4 Current status

| Item | Status |
|------|--------|
| Silver design | **Finalized** (`design-notes.md` §4) |
| Silver DQ scripts | Not implemented |
| Sample data with defects | Generated and validated (`DATA_GENERATION_NOTES.md`) |
| Bronze layer | Implemented and runtime-validated |
| DQ tests | Not written |
| Silver runtime validation | **Not performed** |
| Any Silver check executed | **No** |
| Any Silver threshold verified | **No** |

### 10.5 Spark Connect compatibility (Databricks Serverless)

Silver implementation must not use `spark._jvm`, `spark._jsc`, or Hadoop `FileSystem` APIs. Use DataFrame, SQL, and Delta APIs only (see `design-notes.md` §4.15).

---

## 11. Related Documents

| Document | Relationship |
|----------|--------------|
| `data-model.md` | Silver/Gold schemas, `quality_check_result`, `is_valid` |
| `design-notes.md` | DQ architecture, check ordering, invalid-record policy |
| `requirements-analysis.md` | Requirements and ambiguities |
| `DATA_GENERATION_NOTES.md` | Actual defect counts after generation |
| `debugging-notes.md` | Runtime DQ investigation record |

---

*Document version: 1.0 — aligned with design-notes.md and data-model.md v1.0; no checks executed.*
