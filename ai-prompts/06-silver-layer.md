# AI Prompts — Silver Layer

## Objective

Design the Silver layer for validating and flagging data quality on Bronze e-commerce tables — detect intentional defects, preserve all rows, produce row-level flags and aggregate DQ metrics. No cleansing or deletion.

**Stage status (as of this document):**

| Phase | Status |
|-------|--------|
| Design | Complete — Silver Layer Design Specification produced (Interaction 1) |
| Design clarification | Complete — REFERENCE_DATE and dq_metrics granularity (Interaction 2) |
| Implementation | **Not started** |
| Runtime validation | **Not performed** |

---

## Interaction 1 — Silver Design

### Objective

Design the Silver layer to consume `bronze.customers`, `bronze.products`, and `bronze.orders`; detect and flag intentional data-quality defects; preserve all rows and Bronze metadata; define DQ rules, schemas, metrics, orchestration, and acceptance criteria. Design only — no implementation.

### Exact Prompt Sent

```
We are now starting the Silver Layer of the Databricks Medallion Pipeline.

IMPORTANT:
This is a DESIGN-ONLY interaction.

DO NOT:
- write implementation code
- modify any project files
- modify Bronze
- modify Gold
- modify Dashboard
- modify the generated CSVs
- run Databricks jobs
- create tables

First inspect the existing repository and understand:
- requirement-analysis documents
- design-notes.md
- data-model.md
- data-quality-strategy.md
- DATA_GENERATION_NOTES.md
- Bronze implementation
- Bronze runtime validation results
- existing AI prompt history

The Bronze layer is complete and runtime-validated.

Design the Silver layer to consume:
- bronze.customers
- bronze.products
- bronze.orders

Silver must detect and explicitly flag the intentional data-quality defects preserved by Bronze.

Required DQ checks:

1. Completeness
   - customers.email
   - orders.customer_id
   - orders.product_id

2. Uniqueness
   - customers.customer_id
   - orders.order_id

3. Referential integrity
   - orders.customer_id → customers.customer_id
   - orders.product_id → products.product_id

4. Business-rule validation
   - product price > cost
   - order total_amount = quantity × unit_price
   - Completed orders have non-null payment_date
   - Pending/Cancelled orders have null payment_date
   - valid customer orders satisfy order_date >= customer.signup_date
   - dates must not be in the future

Use the actual finalized defect counts from DATA_GENERATION_NOTES.md.

Important:
- NULL and orphan records must remain traceable.
- Do not silently drop bad rows.
- Do not deduplicate away intentional defects before measuring them.
- Silver should add DQ/quality columns rather than destroying source evidence.
- Preserve Bronze business columns.
- Preserve Bronze metadata columns where appropriate.
- Clearly distinguish row-level flags from aggregate DQ metrics.
- Define how duplicate participants are identified.
- Define how orphan FKs are identified.
- Define how multiple DQ failures on the same row are represented.
- Define whether Silver contains all rows or only valid rows.
- Define the relationship between Silver and later Gold filtering.

Design the following:

1. Silver architecture
2. Silver table names
3. Silver schemas
4. DQ columns
5. DQ rules
6. Exact defect-count expectations
7. Duplicate detection strategy
8. Referential-integrity strategy
9. Business-rule strategy
10. NULL handling
11. Multiple-failure handling
12. Valid/invalid row semantics
13. Error handling
14. Rerun/idempotency
15. Validation strategy
16. Recommended src/silver/ structure
17. Databricks execution approach
18. Design ambiguities requiring explicit decisions
19. Acceptance criteria

Also provide a final Silver acceptance checklist.

Do not implement anything yet.
```

### AI Response Summary

Cursor produced a **Silver Layer Design Specification** (design-only; no code; no file changes). Summary:

**Architecture:** Read full Bronze tables → apply five check categories in order (completeness → uniqueness → type validation → referential integrity → business logic) → accumulate row-level failure codes → overwrite `silver.customers`, `silver.products`, `silver.orders` → append/ write `silver.dq_metrics`. Gold reads `silver.* WHERE is_valid = true`. Spark Connect compatible (no `_jvm`/`_jsc` per Bronze runtime lesson).

**Tables:** `silver.customers`, `silver.products`, `silver.orders`, `silver.dq_metrics` — Delta, schema `silver`, no partitioning.

**Schemas:** All Bronze business + metadata columns preserved; Silver adds `quality_check_result`, `is_valid`, `_silver_processed_timestamp`.

**DQ columns:** Row-level `quality_check_result` (comma-separated codes or `PASS`) and `is_valid`; aggregate metrics in `silver.dq_metrics`.

**DQ rules (five scripts):**

| Script | Code | Scope |
|--------|------|-------|
| `01_quality_completeness.py` | `COMPLETENESS` | customers.email; orders.customer_id, product_id |
| `02_quality_uniqueness.py` | `UNIQUENESS` | customers.customer_id; orders.order_id only |
| `03_quality_type_validation.py` | `TYPE_VALIDATION` | Enums, non-negative numerics, future-date checks *(4th mandatory assignment check)* |
| `04_quality_referential_integrity.py` | `REFERENTIAL_INTEGRITY` | orders FKs vs Bronze parent distinct keys |
| `05_quality_business_logic.py` | `BUSINESS_LOGIC` | price > cost; amount arithmetic; payment_date rules; order_date >= signup_date |

**Defect counts (from DATA_GENERATION_NOTES.md):** 50 NULL emails; 10 duplicate customer rows; 100 NULL order customer_id; 200 NULL order product_id; 50 orphan customer_id; 30 orphan product_id; 20 duplicate order rows — **460 total**. Products: no intentional defects.

**Duplicate strategy:** `GROUP BY pk HAVING COUNT(*) > 1`; flag **all** participants (5 customer pairs / 10 rows; 10 order pairs / 20 rows). No deduplication before measuring.

**RI strategy:** Orphan = non-null FK not in distinct Bronze parent PK set; NULL FKs skip RI (completeness owns NULLs). Ghost ranges 90,001–90,050 and 901–930.

**Business rules:** BR-01 price > cost (products); BR-02 amount tolerance 0.01; BR-03 Completed requires payment_date; BR-04 Pending/Cancelled require null payment_date; BR-05 order_date >= signup_date via internal `MIN(signup_date)` lookup for duplicate customer_id (SD-01).

**NULL handling:** No repair; true SQL NULLs from Bronze preserved.

**Multiple failures:** Canonical comma-separated code order: `COMPLETENESS`, `UNIQUENESS`, `TYPE_VALIDATION`, `REFERENTIAL_INTEGRITY`, `BUSINESS_LOGIC`.

**Valid/invalid semantics:** Silver contains **all** Bronze rows (same counts); invalid rows flagged in-place; Gold filters `is_valid = true`.

**Error handling:** Fatal on missing Bronze / row-count mismatch / Delta write failure; non-fatal row-level DQ — complete all checks in one run.

**Rerun:** Silver entity tables overwrite; `silver.dq_metrics` append with `run_id` (SD-03).

**Structure:** `config.py`, `dq_utils.py`, `01`–`05` quality scripts, `create_silver_tables.py`, `README.md`.

**Databricks:** Free Edition Serverless, Unity Catalog, notebook execution with `sys.path` to `src/silver`, Spark Connect-safe APIs.

**Ambiguities resolved (SD-01–SD-10):** Fourth check = type validation; RI against Bronze PK existence; duplicate signup lookup = MIN(signup_date); 460 vs ~700 = 460 is acceptance criteria.

**Deliverables:** 19 design sections + Silver acceptance checklist.

**Initial reference_date note (superseded in Interaction 2):** Type validation initially proposed `current_date()` at Silver run time.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Layer boundary | Silver flags only; no delete/dedup/repair; Gold aggregates valid rows |
| Row retention | All Bronze rows in Silver (10,000 / 500 / 100,000) |
| Quality columns | `quality_check_result`, `is_valid`, `_silver_processed_timestamp` |
| Fourth mandatory check | `TYPE_VALIDATION` |
| Fifth script | `BUSINESS_LOGIC` (repo structure; separate metrics) |
| Uniqueness scope | `customer_id` on customers only; `order_id` on orders only |
| Duplicate handling | Flag all group members |
| RI parent keys | Distinct Bronze parent PKs (existence-based) |
| Multiple failure codes | Comma-separated canonical order |
| Metrics table | `silver.dq_metrics` persisted Delta table |
| Write mode | Entity tables overwrite; metrics append per run |
| DQ run behavior | Complete all checks (not fail-fast on row failures) |
| Spark Connect | No JVM bridge APIs |
| Defect acceptance | 460 itemized rows from DATA_GENERATION_NOTES.md |

### Accepted

- Design-only deliverable; no implementation in this interaction.
- Bronze as validated input (`bronze.customers`, `bronze.products`, `bronze.orders`).
- Flag-only model per assignment (no silent deletion).
- Preserve Bronze business and metadata columns.
- Five check scripts + `create_silver_tables.py` per repo structure.
- Intentional defect counts and check mapping from `DATA_GENERATION_NOTES.md` and `data-quality-strategy.md`.
- Gold relationship: `WHERE is_valid = true`.
- User-specified business rules (price > cost, payment_date status rules, signup date ordering, future dates).

### Rejected

No implementation decisions were explicitly rejected during this interaction.

Design alternatives noted but not chosen as primary path: separate quarantine tables; deduplicate keeping first occurrence; global `customer_id` uniqueness across orders; stdout-only metrics report.

### Reasoning

Silver must detect the exact intentional defect populations Bronze preserved (460 rows) so assignment DQ thresholds and tests are meaningful. In-place flagging satisfies “flag bad rows — do not delete” with minimal complexity. Check ordering ensures completeness and uniqueness on parents before order RI. Type validation satisfies the fourth mandatory assignment check; business logic adds depth per repo filenames. Separating row-level flags from `silver.dq_metrics` supports traceability and aggregate reporting. Spark Connect compatibility follows Bronze runtime experience on Databricks Free Edition Serverless.

### Files Changed

**None.** The prompt explicitly required design only and stated: *"Do not modify any project files."*

No repository files were created or updated during this interaction.

### Validation Status

| Type | Status |
|------|--------|
| Design | Complete — Silver Layer Design Specification delivered in chat |
| Implementation | **Not started** — no `src/silver/` DQ code beyond placeholder README |
| Runtime validation | **Not performed** — no Silver tables created or DQ checks executed |

---

## Interaction 2 — Silver Design Clarification

### Objective

Clarify two design decisions in the Silver Layer Design Specification: use fixed project `REFERENCE_DATE` instead of `current_date()` for future-date validation, and define exact `silver.dq_metrics` granularity and per-run row count.

### Exact Prompt Sent

```
Update the current Silver Layer Design Specification only.

Do not implement any Silver code.
Do not create or modify project files.
Do not modify Bronze, Gold, Dashboard, data-generation, or tests.

Make only these two design clarifications:

1. Replace the Silver runtime reference_date decision of current_date() with the finalized project REFERENCE_DATE = 2026-08-15, matching the data-generation specification, so Silver future-date validation remains deterministic and reproducible across runs.

2. Clarify silver.dq_metrics granularity:
   one metric row per (run_id, entity, check_name) combination configured for that entity.

Explicitly document the expected metric rows for one run:
- customers: COMPLETENESS, UNIQUENESS, TYPE_VALIDATION
- products: TYPE_VALIDATION, BUSINESS_LOGIC
- orders: COMPLETENESS, UNIQUENESS, TYPE_VALIDATION, REFERENTIAL_INTEGRITY, BUSINESS_LOGIC

Therefore one complete Silver run produces 10? metric rows — verify the count from the listed combinations before documenting it.

Do not invent any other changes.

After making the design clarification, return:
- exact changes made
- decisions accepted
- decisions rejected
- reasoning
- confirmation that no implementation occurred
- confirmation that no runtime validation occurred
```

### AI Response Summary

Cursor applied two targeted clarifications to the Silver design specification (in chat only; no project files modified).

**Clarification 1 — REFERENCE_DATE:**

- Replaced `current_date()` at Silver run time with **`REFERENCE_DATE = 2026-08-15`** (fixed project constant matching `DATA_GENERATION_NOTES.md`).
- Type-validation future-date rules (`signup_date`, `order_date`, `payment_date` when not null) now use `<= REFERENCE_DATE`.
- Supersedes design decision SD-06 (`current_date()` at Silver run).
- Implementation note for future `src/silver/config.py`: expose `REFERENCE_DATE = date(2026, 8, 15)`.

**Clarification 2 — `silver.dq_metrics` granularity:**

- **Grain:** one metric row per **`(run_id, entity, check_name)`** for checks configured on that entity.
- **Per-run row count verified:** 3 + 2 + 5 = **10 rows** per complete Silver run.

| Entity | `check_name` values | Rows |
|--------|---------------------|------|
| `customers` | `COMPLETENESS_CUSTOMERS`, `UNIQUENESS_CUSTOMERS`, `TYPE_VALIDATION_CUSTOMERS` | 3 |
| `products` | `TYPE_VALIDATION_PRODUCTS`, `BUSINESS_LOGIC_PRODUCTS` | 2 |
| `orders` | `COMPLETENESS_ORDERS`, `UNIQUENESS_ORDERS`, `TYPE_VALIDATION_ORDERS`, `REFERENTIAL_INTEGRITY_ORDERS`, `BUSINESS_LOGIC_ORDERS` | 5 |
| **Total** | | **10** |

- Products: no completeness/uniqueness metrics (no applicable rules).
- Customers: no RI or business-logic metrics (no applicable rules on that entity).
- Post-condition updated: exactly **10** `silver.dq_metrics` rows per `run_id`.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Future-date validation | `REFERENCE_DATE = 2026-08-15` (not `current_date()`) |
| Metrics grain | One row per `(run_id, entity, check_name)` |
| Metrics per run | **10 rows** (3 customers + 2 products + 5 orders) |
| Entity-specific metrics | Only configured checks produce rows; no spurious entity/check combinations |

### Accepted

- Fixed `REFERENCE_DATE = 2026-08-15` for deterministic, reproducible Silver type-validation across runs.
- `silver.dq_metrics` keyed by `(run_id, entity, check_name)`.
- Exactly **10** metric rows per complete Silver run per the entity/check matrix above.
- Prior SD-06 (`current_date()`) superseded by fixed reference date.

### Rejected

No implementation decisions were explicitly rejected during this interaction.

### Reasoning

`current_date()` would make future-date check results depend on execution date, breaking alignment with data generated against `REFERENCE_DATE = 2026-08-15` and complicating test assertions. Fixed reference date matches the data-generation contract.

Explicit `(run_id, entity, check_name)` grain matches `data-quality-strategy.md` naming (`COMPLETENESS_CUSTOMERS`, etc.), avoids ambiguous global metrics, and yields a fixed **10-row** contract per run that is straightforward to validate in tests and notebooks.

### Files Changed

**None.** The prompt explicitly stated: *"Do not create or modify project files."*

Clarifications were applied to the in-chat design specification only. This interaction updated **`ai-prompts/06-silver-layer.md`** (this document) to record the workflow.

### Validation Status

| Type | Status |
|------|--------|
| Design clarification | Complete — REFERENCE_DATE and dq_metrics granularity documented |
| Implementation | **Not started** |
| Runtime validation | **Not performed** — no Silver DQ execution in Databricks |
