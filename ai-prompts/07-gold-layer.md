# AI Prompts — Gold Layer

## Objective

Design the Gold layer to consume validated Silver tables and produce business-ready analytical aggregations required by the assignment for Dashboard consumption.

**Stage status (as of this document):**

| Phase | Status |
|-------|--------|
| Design | Complete |
| Engineering decisions (GD-01–GD-14) | Finalized and persisted |
| Implementation | Complete |
| Runtime validation | Complete |

---

## Interaction 1 — Gold Design

### Objective

Design the Gold layer to consume validated Silver tables (`silver.customers`, `silver.products`, `silver.orders`); produce assignment-required business aggregations; define schemas, filtering, segmentation, orchestration, and acceptance criteria. Design only — no implementation.

### Exact Prompt Sent

```
We are now starting the Gold Layer of the Databricks Medallion Pipeline.

IMPORTANT:
This is a DESIGN-ONLY interaction.

DO NOT:
- write implementation code
- modify any project files
- modify Bronze
- modify Silver
- modify Dashboard
- modify generated CSVs
- modify tests
- run Databricks jobs
- create Gold tables
- create Dashboard artifacts

First inspect the existing repository and understand:

- assignment/assignment-requirements.md
- requirements-analysis.md
- design-notes.md
- data-model.md
- data-quality-strategy.md
- DATA_GENERATION_NOTES.md
- Bronze implementation and runtime validation
- Silver implementation and runtime validation
- existing Gold placeholder/documentation
- existing AI prompt history

IMPORTANT PROJECT STATE:

Bronze:
- Design complete
- Implementation complete
- Static review complete
- Databricks runtime validated
- bronze.customers = 10,000
- bronze.products = 500
- bronze.orders = 100,000

Silver:
- Design complete
- Design clarification complete
- Implementation complete
- Static review complete
- Databricks runtime validated
- silver.customers = 10,000
- silver.products = 500
- silver.orders = 100,000
- silver.dq_metrics produces exactly 10 rows per run
- Invalid rows are preserved and flagged
- Gold must consume Silver and should use is_valid = true for business analytics

Now design the Gold layer.

The Gold layer must consume the validated Silver layer and provide the business-facing analytical outputs required by the assignment.

Inspect the assignment and existing documentation carefully to identify the EXACT required Gold aggregations, metrics, tables, columns, and business questions.

Do not invent additional assignment requirements.

The design must explicitly define:

1. Gold architecture
2. Gold table names
3. Source Silver tables for each Gold output
4. Exact Gold schemas
5. Valid-row filtering strategy
6. Required Gold aggregations
7. Customer-level analytics, if required by the assignment
8. Product-level analytics, if required by the assignment
9. Order-level / sales analytics, if required by the assignment
10. Revenue / sales calculations
11. Handling of NULLs and invalid records
12. Referential-integrity implications
13. Aggregation grain
14. Rerun / idempotency behavior
15. Error handling
16. Databricks / Spark Connect compatibility
17. Recommended src/gold/ structure
18. Orchestration approach
19. Validation strategy
20. Expected row counts / sanity checks where they can be derived from the assignment
21. Design ambiguities requiring explicit engineering decisions
22. Acceptance criteria

Also provide a final Gold acceptance checklist.

IMPORTANT:

- Preserve Silver as the source of truth for DQ status.
- Do not modify Silver data.
- Do not duplicate Silver DQ logic in Gold.
- Do not perform cleansing in Gold.
- Do not silently drop records except through the explicitly designed valid-row filtering required for analytics.
- Do not invent metrics or tables that are not supported by the assignment.
- Clearly distinguish business-facing Gold aggregates from Silver DQ metrics.
- Use the exact finalized requirements from the repository.

This interaction is DESIGN ONLY.

Do not implement anything yet.
Do not modify any files.
Do not execute anything in Databricks.

At the end, explicitly identify every design ambiguity that requires an engineering decision before implementation.
```

### AI Response Summary

Cursor produced a **Gold Layer Design Specification** (design-only; no code; no file changes). Summary:

**Architecture:** Read only from `silver.customers`, `silver.products`, `silver.orders` with `is_valid = true`; apply qualifying-order filter (`order_status = 'Completed'`); compute four Gold aggregations; Delta overwrite to schema `gold`; Dashboard reads Gold only. Gold never reads Bronze and does not re-implement Silver DQ.

**Assignment-required tables (three):**

| Table | Purpose | Key measures |
|-------|---------|--------------|
| `gold.sales_by_product` | Product performance | `total_orders`, `total_revenue`, `avg_order_value` |
| `gold.revenue_by_customer` | Customer value | Above + `lifetime_value_actual` |
| `gold.customer_segmentation` | Behavioral segments | `customer_count`, `avg_revenue`, `total_revenue` by `segment_type` |

**Fourth table (repo / technical requirements):** `gold.daily_weekly_trends` — daily and weekly revenue trends in one table with `period_type`.

**Revenue contract:** Qualifying order = `is_valid = true` AND `Completed`; `total_revenue = SUM(total_amount)`; `total_orders = COUNT(DISTINCT order_id)`; `avg_order_value = total_revenue / total_orders`; `lifetime_value_actual = total_revenue`.

**Valid-row filtering:** Silver retains all rows with DQ flags; Gold excludes `is_valid = false` for analytics (explicit filter, not silent deletion).

**Customer segmentation:** Derived from complete valid-customer population via valid customers LEFT JOIN qualifying orders; rules for Inactive / One-Time / Repeat / High-Value with P75 threshold among customers with ≥1 order.

**Join strategy:** Order-backed aggregates inner-join valid Silver dimensions; orders excluded when required customer or product dimension invalid.

**Orchestration:** `create_gold_tables.py` validates Silver prerequisites, builds shared bases, writes four tables, prints summary.

**Spark Connect:** DataFrame/SQL/Delta only; no JVM/Hadoop FS APIs.

**Ambiguities identified:** GD-01–GD-14 — finalized in post-design documentation persistence (see Key Decisions).

### Key Decisions

| ID | Decision |
|----|----------|
| **GD-01** | Omit products with zero qualifying completed-valid orders from `gold.sales_by_product` |
| **GD-02** | Order-backed aggregates: qualifying orders + inner joins to valid Silver dimensions |
| **GD-03** | Omit empty customer segmentation buckets |
| **GD-04** | Weekly trends: `order_date = NULL`; `period_start` = Monday week anchor |
| **GD-05** | Monday-start weeks via Spark calendar-week semantics |
| **GD-06** | Implement all four Gold tables (3 assignment + `daily_weekly_trends`) |
| **GD-07** | Do **not** add `country` to `gold.revenue_by_customer` — assignment-aligned schema |
| **GD-08** | `avg_order_value` as `DECIMAL(18,2)`, rounded to two decimal places |
| **GD-09** | `total_revenue >= P75` → High-Value; `< P75` → Repeat (among ≥2 orders) |
| **GD-10** | PySpark/DataFrame implementation (Spark Connect compatible), not separate SQL files |
| **GD-11** | Zero-order customers: `total_orders=0`, `total_revenue=0.00`, `avg_order_value=NULL`, `lifetime_value_actual=0.00` |
| **GD-12** | No Gold metadata columns unless assignment/data-model explicitly requires |
| **GD-13** | Exclude orders from aggregates when required valid customer or product dimension unavailable |
| **GD-14** | Daily and weekly trends in one table via `period_type` |
| **Layer** | Gold reads Silver only; `is_valid = true`; never Bronze |
| **Revenue filter** | `order_status = 'Completed'` only (DA-07) |
| **Write mode** | Delta overwrite per run |
| **Segmentation base** | Valid customers LEFT JOIN qualifying orders (retains Inactive) |

### Accepted

- Gold consumes Silver with `is_valid = true` for business analytics.
- Three assignment aggregation tables with exact §8 columns and calculations.
- Fourth table `daily_weekly_trends` per repo/common technical requirements (GD-06).
- Qualifying-order revenue contract as specified.
- Behavioral segmentation from complete valid-customer population including zero-order customers.
- P75 threshold for High-Value vs Repeat among customers with ≥1 order.
- Inner joins to valid dimensions for order-backed product/customer aggregates (GD-02, GD-13).
- PySpark/DataFrame Gold implementation (GD-10).
- Assignment-aligned `revenue_by_customer` schema without `country` (GD-07).
- Spark Connect-compatible APIs only.
- Engineering decisions GD-01–GD-14 persisted to `design-notes.md` §5, `data-model.md` §10, `src/gold/README.md`.

### Rejected

- Denormalizing `country` into `gold.revenue_by_customer` (prior DA-12 — superseded by GD-07).
- Separate `.sql` file implementation as primary Gold approach (GD-10).
- Including products with zero qualifying orders in `gold.sales_by_product` (GD-01).
- Including empty segmentation buckets with zero counts (GD-03).
- Adding Gold metadata columns such as `_gold_processed_timestamp` (GD-12).
- Gold reading Bronze or re-implementing Silver DQ logic.
- Cleansing, deduplicating, or mutating Silver data in Gold.

### Reasoning

Gold sits between validated Silver and the Dashboard: Silver preserves traceability and flags defects; Gold produces trusted business metrics for analytics. The assignment defines three core aggregation tables with explicit columns; the repository and common technical requirements add a fourth trends table. Filtering `is_valid = true` and `Completed` orders produces meaningful revenue without duplicating Silver checks. Customer segmentation requires the full valid-customer population (LEFT JOIN) so Inactive customers are counted. Finalized GD decisions resolve pre-implementation ambiguities without expanding assignment scope.

### Files Changed

**Design interaction:** None. The prompt required design only and stated *"Do not modify any project files."*

**Documentation persistence (post-design review):** `design-notes.md` §5, `data-model.md` §10–11, `src/gold/README.md`, `requirements-analysis.md` §17.2–17.4, `docs/README.md`, and this file (`ai-prompts/07-gold-layer.md`).

### Validation Status

| Type | Status |
|------|--------|
| Design | **Complete** — Gold Layer Design Specification delivered; GD-01–GD-14 finalized |
| Implementation | **Not started** — no `src/gold/` implementation code |
| Databricks runtime validation | **Not performed** — no Gold tables created |
| Gold runtime success | **Not claimed** — no observed Gold metrics or row counts |

---

## Interaction 2 — Gold Implementation

### Objective

Implement the Gold layer per finalized design (GD-01–GD-14): four aggregation tables, PySpark/DataFrame + Delta, Spark Connect compatible.

### Exact Prompt Sent

Gold implementation interaction following Silver runtime validation — implement `src/gold/` modules and `create_gold_tables.py` per design spec. Do not modify Bronze or Silver.

### AI Response Summary

Implemented Gold layer under `src/gold/`:

| File | Purpose |
|------|---------|
| `config.py` | Schema names, constants, expected Silver row counts |
| `gold_utils.py` | Silver validation, loaders, Delta writes, output validation |
| `01_sales_by_product.py` | Product sales aggregation |
| `02_revenue_by_customer.py` | Customer revenue (LEFT JOIN for zero-order customers) |
| `03_daily_weekly_trends.py` | Daily + weekly trends in one table |
| `04_customer_segmentation.py` | Behavioral segmentation (P75 threshold) |
| `create_gold_tables.py` | Orchestrator |

### Files Changed

- `src/gold/*` — all implementation modules
- `src/gold/README.md` — module documentation

### Validation Status

| Type | Status |
|------|--------|
| Implementation | **Complete** (static verification) |
| Runtime validation | **Not performed** at time of Interaction 2 |

---

## Interaction 3 — Gold Runtime Validation

### Objective

Execute Gold pipeline in Databricks and validate four Gold tables against acceptance criteria.

### Exact Prompt Sent

No separate Cursor prompt — Gold processing executed in Databricks by user after Silver validation.

### AI Response Summary

Gold processing completed successfully. Observed row counts:

| Table | Rows |
|-------|------|
| `gold.sales_by_product` | 500 |
| `gold.revenue_by_customer` | 9,940 |
| `gold.customer_segmentation` | 4 |
| `gold.daily_weekly_trends` | 2,679 |

All Gold validation checks PASS. Dashboard KPI baseline aligns: Active Products = 500, Customer Count = 9.94K.

### What I Accepted

- Four Gold tables with expected row counts.
- Qualifying-order filter (`is_valid = true`, `Completed`) producing consistent revenue metrics.
- Customer segmentation with four behavioral segments.

### Files Changed

None — runtime validation only. Status updated in `src/gold/README.md` and planning docs.

### Validation Status

| Type | Status |
|------|--------|
| Design | **Complete** |
| Implementation | **Complete** |
| Databricks runtime execution | **Complete** |
| Runtime validation | **Complete** |
| Gold runtime success | **Validated** |

---

## Overall Stage Status

| Phase | Status |
|-------|--------|
| Design | Complete |
| Engineering decisions (GD-01–GD-14) | Finalized |
| Implementation | Complete |
| Runtime validation | Complete |
| Gold runtime success | Validated |
