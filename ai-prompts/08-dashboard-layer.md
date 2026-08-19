# AI Prompts — Dashboard Layer

## Objective

Design and implement a Databricks SQL Dashboard that consumes Gold-layer analytics only — KPIs, required visualizations, trends, and customer detail for business stakeholders.

**Stage status (as of this document):**

| Phase | Status |
|-------|--------|
| Design | Complete |
| SQL / documentation implementation | Complete |
| Databricks Dashboard UI | **Complete** (manual) |
| Runtime validation | **Complete** (manual) |

---

## Interaction 1 — Dashboard Design

### Objective

Design the Databricks SQL Dashboard using Gold tables only; define KPIs, visualizations, SQL logic, filters, layout, and acceptance criteria. Design only — no implementation.

### Exact Prompt Sent

```
We are now starting the Dashboard layer.

IMPORTANT:
THIS INTERACTION IS DESIGN ONLY.

DO NOT:
- write Dashboard implementation code
- modify Bronze
- modify Silver
- modify Gold
- modify generated CSVs
- modify Gold schemas
- create Databricks dashboards
- execute Databricks queries
- create visualizations yet

First inspect:
- assignment/assignment-requirements.md
- requirements-analysis.md
- design-notes.md
- data-model.md
- data-quality-strategy.md
- src/gold/README.md
- existing dashboard documentation
- existing AI prompt history

Design the Databricks SQL Dashboard using GOLD TABLES ONLY.

The Dashboard must never read Bronze or Silver.

Define:

1. Dashboard objective
2. Dashboard audience/use case
3. KPI cards
4. Required visualizations
5. Gold source table for every visualization
6. Exact columns used by every visualization
7. SQL query logic for every visualization
8. Visualization type
9. X-axis / Y-axis / dimensions / measures
10. Sorting requirements
11. Filters
12. Filter-to-chart behavior
13. Dashboard layout
14. Revenue calculation consistency
15. Customer segmentation visualization
16. Product performance visualization
17. Revenue trend visualization
18. Customer revenue distribution
19. Dashboard-level validation strategy
20. Acceptance criteria
21. Recommended dashboard documentation structure

Required analytics:

1. Total Revenue
2. Total Orders
3. Customer count
4. Product count
5. Top 10 products by revenue
6. Daily/weekly revenue trend
7. Customer segmentation
8. Customer revenue distribution
9. Customer-level revenue/order analysis

Important business rules:

- Dashboard reads Gold only.
- Revenue uses Gold revenue values.
- Do not recalculate Silver DQ logic.
- Do not access Bronze.
- Do not access Silver.
- Do not repair or cleanse data.
- Do not create additional Gold tables.
- customer_segment (Premium/Standard/Basic) is different from behavioral segment_type (High-Value/Repeat/One-Time/Inactive).
- Do not change Gold schemas.

Resolve any dashboard ambiguities explicitly.

At the end provide:
- complete Dashboard Design Specification
- exact chart/table/KPI inventory
- exact Gold source mapping
- SQL query inventory
- layout
- filters
- acceptance checklist

Do not implement anything yet.
```

### AI Response Summary

Cursor produced a **Dashboard Design Specification** (design-only; no code; no file changes). Summary:

**Architecture:** Gold-only consumption — four Gold tables, no Bronze/Silver, no new Gold tables.

**Widgets (9):** 4 KPI counters + 4 visualizations + 1 customer detail table.

| Widget | Type | Gold source |
|--------|------|-------------|
| KPI-01–03 | Counter | `gold.revenue_by_customer` |
| KPI-04 | Counter | `gold.sales_by_product` |
| VIZ-01 | Bar (assignment) | `gold.sales_by_product` |
| VIZ-02 | Histogram (assignment) | `gold.revenue_by_customer` |
| VIZ-03 | Pie (assignment) | `gold.customer_segmentation` |
| VIZ-04 | Line | `gold.daily_weekly_trends` |
| TBL-01 | Table | `gold.revenue_by_customer` |

**Filters (5):** `product_category`, `customer_segment` (marketing), `period_type`, `start_date`, `end_date`. Country filter rejected (GD-07 / Gold-only). Date filters apply **only** to VIZ-04 (DD-01).

**Layout:** KPI row → products + trend → histogram + pie → customer table.

**Ambiguities resolved:** DD-01 through DD-12 (date scope, no country filter, KPI sources, histogram binning, pie measure = `customer_count`, etc.).

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Data source | Gold tables only |
| Widget count | 9 (4 KPI + 4 viz + 1 table) |
| Assignment minimum | Bar + histogram + pie included |
| KPI revenue | `SUM(gold.revenue_by_customer.total_revenue)` |
| Pie measure | `customer_count` (behavioral `segment_type`) |
| Date filter scope | VIZ-04 only (lifetime KPIs) |
| Country filter | Not implemented (not in Gold) |
| Build approach | SQL in repo; manual Databricks UI assembly |
| Segment distinction | `customer_segment` ≠ `segment_type` |

### Accepted

- Gold-only dashboard contract.
- Nine-widget inventory covering all required analytics.
- Five dashboard parameters with filter-to-query matrix.
- Manual UI build per `design-notes.md` §6.5.
- Revenue from Gold columns only; no DQ re-implementation.

### Rejected

- Country filter via Silver join (Gold-only constraint).
- Behavioral `segment_type` as global dashboard filter (pie is the segmentation view).
- Date filters on lifetime KPI/customer/product aggregates.
- Automatic dashboard-as-code deployment.

### Reasoning

Gold is the trusted analytics surface after Silver DQ. The dashboard displays pre-aggregated Gold metrics without re-reading raw orders or Silver flags. Assignment requires three visualization types; design extends with KPIs, trends, and customer table using the fourth Gold table. Filter scope respects Gold schema (no `country`, no order-date on customer/product aggregates).

### Files Changed

**None.** Design interaction required no project file modifications.

### Validation Status

| Type | Status |
|------|--------|
| Design | **Complete** — Dashboard Design Specification delivered in chat |
| Implementation | **Not started** |
| Runtime validation | **Not performed** |

---

## Interaction 2 — Dashboard Implementation

### Objective

Implement the Dashboard SQL query layer and documentation (`dashboard_queries.sql`, `DASHBOARD_GUIDE.md`, `README.md`) per the finalized design. No Databricks UI creation or query execution.

### Exact Prompt Sent

```
We are now implementing the Dashboard layer.

IMPORTANT:
The Dashboard design has already been finalized and documented.

Bronze: IMPLEMENTED + RUNTIME VALIDATED
Silver: IMPLEMENTED + RUNTIME VALIDATED
Gold: IMPLEMENTED + RUNTIME VALIDATED
Dashboard: DESIGN COMPLETE, IMPLEMENTATION NOT STARTED

Validated Gold runtime:
- gold.sales_by_product = 500 rows
- gold.revenue_by_customer = 9,940 rows
- gold.customer_segmentation = 4 rows
- gold.daily_weekly_trends = 2,679 rows
- All Gold validation checks PASS

Implement ONLY the Dashboard documentation and SQL query layer.

DO NOT:
- modify Bronze
- modify Silver
- modify Gold
- modify Gold schemas
- create new Gold tables
- create new Silver tables
- modify generated CSVs
- modify existing Gold aggregation logic
- create the Databricks Dashboard UI automatically
- execute Databricks queries
- claim runtime validation
- use Bronze or Silver as Dashboard sources

Create/update ONLY:

src/dashboard/
├── dashboard_queries.sql
├── DASHBOARD_GUIDE.md
└── README.md

Also update ai-prompts/08-dashboard-layer.md with this implementation interaction and its status.

[... full SQL, guide, README, and static validation requirements ...]
```

### AI Response Summary

Cursor implemented the Dashboard **SQL and documentation layer** under `src/dashboard/`:

**`dashboard_queries.sql`:** Nine widget queries — KPI-01 through KPI-04, VIZ-01 through VIZ-04, TBL-01. All read Gold tables only. Dashboard parameters `:customer_segment`, `:product_category`, `:period_type`, `:start_date`, `:end_date` documented with Databricks SQL `:param` syntax and optional multi-select guards via `cardinality` / `EXPLODE`.

**`DASHBOARD_GUIDE.md`:** Complete manual setup guide (20 sections): objective, prerequisites, Gold tables, dashboard creation steps, query-to-viz mapping, per-viz configuration, layout wireframe, parameter creation and mapping, date-filter scope note, validation checklist, troubleshooting, Gold-only rule.

**`README.md`:** Dashboard overview, architecture, widget/filter inventory, segment terminology, setup instructions, validation status.

**Databricks UI:** Not created. **Queries:** Not executed. **Runtime validation:** Not performed.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Parameter syntax | Databricks SQL dashboard `:parameter_name` with Array multi-select |
| Optional filters | `COALESCE(cardinality(:param), 0) = 0 OR ... IN (SELECT EXPLODE(:param))` |
| Pie measure | `customer_count` on `gold.customer_segmentation` |
| Histogram | Raw `total_revenue` rows for UI-native binning |
| Customer table | `LIMIT 500` |
| UI build | Documented manual steps only |

### Accepted

- All 9 queries implemented per design specification.
- Gold-only source contract in SQL and documentation.
- Manual dashboard assembly documented in `DASHBOARD_GUIDE.md`.
- No Bronze/Silver/Gold code changes.

### Rejected

- Creating Databricks Dashboard UI in this interaction.
- Executing SQL against Databricks.
- Country filter (not in Gold).
- Claiming runtime or dashboard validation success.

### Reasoning

The assignment deliverable includes versioned SQL queries and a setup guide; Databricks CE requires manual dashboard UI configuration. Implementing queries and documentation unblocks the final pipeline step without modifying upstream layers or claiming unverified runtime results.

### Files Changed

| File | Change |
|------|--------|
| `src/dashboard/dashboard_queries.sql` | Created |
| `src/dashboard/DASHBOARD_GUIDE.md` | Replaced placeholder with complete guide |
| `src/dashboard/README.md` | Replaced placeholder with complete overview |
| `ai-prompts/08-dashboard-layer.md` | Created (this document) |

No files outside `src/dashboard/` and `ai-prompts/08-dashboard-layer.md` were modified.

### SQL query inventory

| Query ID | Gold table(s) |
|----------|---------------|
| KPI-01 | `gold.revenue_by_customer` |
| KPI-02 | `gold.revenue_by_customer` |
| KPI-03 | `gold.revenue_by_customer` |
| KPI-04 | `gold.sales_by_product` |
| VIZ-01 | `gold.sales_by_product` |
| VIZ-02 | `gold.revenue_by_customer` |
| VIZ-03 | `gold.customer_segmentation` |
| VIZ-04 | `gold.daily_weekly_trends` |
| TBL-01 | `gold.revenue_by_customer` |

### Validation Status

| Type | Status |
|------|--------|
| Design | **Complete** |
| SQL / documentation implementation | **Complete** |
| Static verification | **Complete** (file presence, Gold references, no forbidden sources) |
| Databricks Dashboard UI | **Not created** |
| Databricks query execution | **Not performed** |
| Dashboard runtime validation | **Not performed** |
| Dashboard runtime success | **Not claimed** |

---

## Interaction 3 — Manual Databricks SQL Dashboard Implementation

### Objective

Implement the finalized dashboard design manually in the Databricks SQL Dashboard UI using the already-created Gold-only SQL datasets.

No dashboard code generation was performed for the UI itself. The dashboard was assembled manually in Databricks according to the finalized Interaction 1 design and Interaction 2 SQL implementation.

### Exact Prompt Sent

Manual implementation performed outside Cursor — no AI prompt was sent for UI assembly. This interaction records the actual manual Databricks SQL Dashboard build, configuration decisions, issues encountered, resolutions, and runtime validation results.

### Implementation Method

The dashboard was created manually in the Databricks SQL Dashboard UI.

The following previously created SQL datasets were used:

1. KPI-01 — Total Revenue
2. KPI-02 — Total Orders
3. KPI-03 — Customer Count
4. KPI-04 — Active Products
5. VIZ-01 — Top 10 Products by Revenue
6. VIZ-02 — Customer Revenue Distribution
7. VIZ-03 — Customer Segmentation
8. VIZ-04 — Revenue Trend
9. TBL-01 — Customer Revenue Detail

All datasets read exclusively from Gold tables. No Bronze or Silver tables were used by the dashboard.

### Dashboard Widgets Created

**KPI cards**

| ID | Title | Visualization |
|----|-------|---------------|
| KPI-01 | Total Revenue | Counter |
| KPI-02 | Total Orders | Counter |
| KPI-03 | Customer Count | Counter |
| KPI-04 | Active Products | Counter |

**Required visualizations**

| ID | Title | Visualization |
|----|-------|---------------|
| VIZ-01 | Top 10 Products by Revenue | Bar Chart |
| VIZ-02 | Customer Revenue Distribution | Histogram |
| VIZ-03 | Customer Segmentation | Pie Chart |
| VIZ-04 | Revenue Trend | Line Chart |

**Detail table**

| ID | Title | Visualization |
|----|-------|---------------|
| TBL-01 | Customer Revenue & Order Detail | Table |

**Total:** 4 KPI cards + 4 visualizations + 1 customer detail table = **9 widgets**.

### Manual Dashboard Configuration

**KPI-01 — Total Revenue**

- Visualization: Counter
- Source dataset: `KPI-01 Total Revenue`
- Value: `total_revenue`
- Final unfiltered value: `40.03M`

**KPI-02 — Total Orders**

- Visualization: Counter
- Source dataset: `KPI-02 Total Orders`
- Value: `total_orders`
- Final unfiltered value: `69.58K`

**KPI-03 — Customer Count**

- Visualization: Counter
- Source dataset: `KPI-03 Customer Count`
- Value: `customer_count`
- Final unfiltered value: `9.94K`

**KPI-04 — Active Products**

- Visualization: Counter
- Source dataset: `KPI-04 Active Products`
- Value: `product_count`
- Final unfiltered value: `500`

**VIZ-01 — Top 10 Products by Revenue**

- Visualization: Bar Chart
- Source: `VIZ-01 Top 10 Products`
- X-axis: `total_revenue`
- Y-axis: `product_name`
- Category/color: `category`
- Sort: `total_revenue DESC`
- Limit: 10

**VIZ-02 — Customer Revenue Distribution**

- Visualization: Histogram
- Source: `VIZ-02 Customer Revenue Distribution`
- X-axis: `BIN(total_revenue)`
- Revenue column: `total_revenue`
- Include zero-revenue customers
- Native Databricks histogram used

**VIZ-03 — Customer Segmentation**

- Visualization: Pie Chart
- Source: `VIZ-03 Customer Segmentation`
- Dimension: `segment_type`
- Measure: `customer_count`
- Behavioral segments: High-Value, Repeat, One-Time, Inactive
- `segment_type` (behavioral) is intentionally different from `customer_segment` (marketing tier)
- Pie uses `customer_count`, not revenue, to show customer population distribution

**VIZ-04 — Revenue Trend**

- Visualization: Line Chart
- Source: `VIZ-04 Revenue Trend`
- X-axis: `period_start`
- Y-axis: `total_revenue`
- Period type parameter: `DAILY` / `WEEKLY`
- Date range controlled using Start Date and End Date

**TBL-01 — Customer Revenue & Order Detail**

- Visualization: Table
- Source: `TBL-01 Customer Revenue Detail`
- Columns: `customer_id`, `customer_name`, `customer_segment`, `total_orders`, `total_revenue`, `avg_order_value`, `lifetime_value_actual`
- Sort: `total_revenue DESC`
- Limit: `500`

### Dashboard Filters

| ID | Filter | Type | Source / Field | Purpose |
|----|--------|------|----------------|---------|
| F-01 | Product Category | Multiple values | `VIZ-01 Top 10 Products` → `category` | Filters product-related content |
| F-02 | Customer Segment | Multiple values | Customer-related datasets → `customer_segment` (Premium, Standard, Basic) | Filters customer KPIs, histogram, detail table |
| F-03 | Period Type | Single value | `DAILY`, `WEEKLY` | Controls Revenue Trend granularity (default: `DAILY`) |
| F-04 | Start Date | Date | `gold.daily_weekly_trends` | Controls Revenue Trend date range |
| F-05 | End Date | Date | `gold.daily_weekly_trends` | Controls Revenue Trend date range |

### Filter Behavior Validation

Manually tested in the Databricks UI:

| Filter | Verified behavior |
|--------|-------------------|
| Product Category | Changes Active Products KPI and Top 10 Products visualization |
| Customer Segment | Changes Total Revenue, Total Orders, Customer Count, Customer Revenue Distribution, Customer Revenue Detail |
| Period Type | Switching `DAILY` / `WEEKLY` changes Revenue Trend granularity |
| Start / End Date | Affects Revenue Trend only; lifetime KPIs and customer/product aggregates are not date-sliced |

### Issues Encountered and Resolutions

**Issue 1 — Counter visualization initially showed `COUNT(*)`**

Databricks defaulted Counter measure to `COUNT(*)`. Manually changed to correct Gold output fields: `total_revenue`, `total_orders`, `customer_count`, `product_count`.

**Issue 2 — Customer Count temporarily showed `500` instead of `9.94K`**

An active dashboard filter caused the incorrect count. Resolved by resetting filters (`Reset all to default`); baseline restored to `9.94K`.

**Issue 3 — Dashboard parameter error: `Missing selection for parameter: product_category`**

Product Category filter lacked a valid default. Resolved by configuring multiple-value filter with `All` as default selection.

**Issue 4 — Customer Segmentation pie chart misconfiguration**

Initial Pie Chart config did not produce desired segmentation. Corrected by using `segment_type` as dimension and `customer_count` as measure. Final chart shows four behavioral segments: Repeat, High-Value, One-Time, Inactive.

### Final Dashboard Runtime Result

Dashboard successfully created and tested in Databricks.

**Final KPI values (default filters):**

| KPI | Result |
|-----|--------|
| Total Revenue | 40.03M |
| Total Orders | 69.58K |
| Active Products | 500 |
| Customer Count | 9.94K |

**Component validation:**

| Component | Status |
|-----------|--------|
| KPI cards | PASS |
| Top 10 Products | PASS |
| Customer Revenue Histogram | PASS |
| Customer Segmentation | PASS |
| Revenue Trend | PASS |
| Customer Detail Table | PASS |
| Product Category filter | PASS |
| Customer Segment filter | PASS |
| Period Type filter | PASS |
| Start Date filter | PASS |
| End Date filter | PASS |

### Dashboard Runtime Validation

Manually validated against Gold runtime results.

**Gold baseline:**

| Gold table | Rows |
|------------|------|
| `gold.sales_by_product` | 500 |
| `gold.revenue_by_customer` | 9,940 |
| `gold.customer_segmentation` | 4 |
| `gold.daily_weekly_trends` | 2,679 |

**Dashboard baseline (default filters):**

| KPI | Value |
|-----|-------|
| Total Revenue | 40.03M |
| Total Orders | 69.58K |
| Customer Count | 9.94K |
| Active Products | 500 |

Customer Count (`9.94K`) aligns with `gold.revenue_by_customer` row count (`9,940`). Active Products (`500`) aligns with `gold.sales_by_product` row count (`500`).

### Files Changed

**None.** UI was configured manually in Databricks; no repository files were modified in this interaction.

### Important Implementation Note

The Databricks SQL Dashboard UI was configured manually rather than generated through an automated API or code-based dashboard deployment. This interaction records the actual manual implementation process — not an AI-generated UI implementation.

### Validation Status

| Type | Status |
|------|--------|
| Design | **Complete** |
| SQL / documentation implementation | **Complete** |
| Databricks Dashboard UI | **Complete** (manual) |
| KPI configuration | **Complete** |
| Visualization configuration | **Complete** |
| Filter configuration | **Complete** |
| Manual filter testing | **Complete** |
| Dashboard runtime validation | **Complete** |
| Final dashboard | **Complete** |

---

## Overall Stage Status

| Phase | Status |
|-------|--------|
| Design | Complete |
| SQL / documentation implementation | Complete |
| Databricks Dashboard UI | Complete (manual) |
| Dashboard export artifact (`.lvdash.json`) | Complete |
| Full pipeline automation notebook | Complete |
| KPI / visualization / filter configuration | Complete |
| Manual filter testing | Complete |
| Runtime validation | Complete |
| Final dashboard | Complete |

---

## Interaction 4 — Dashboard Export Artifact

### Objective

Export the validated Databricks SQL Dashboard as a `.lvdash.json` file for reproducible import and version control.

### Exact Prompt Sent

User exported the runtime dashboard from Databricks and added `E-Commerce Analytics Dashboard.lvdash.json` to `src/dashboard/`. Documentation updated to reference the export as the primary dashboard deliverable.

### AI Response Summary

Reviewed the export file. It contains:

- **9 datasets** matching KPI-01–04, VIZ-01–04, TBL-01 — all query `gold.*` tables only
- **9 widgets:** 4 counters, bar, histogram, pie, line, table
- **1 global filter:** Product Category (associative multi-select on VIZ-01 and KPI-04 datasets)
- **Dashboard name:** E-Commerce Analytics Dashboard

Differences from `dashboard_queries.sql` documented:

| Item | Export | `dashboard_queries.sql` |
|------|--------|-------------------------|
| Filters | Product Category only | 5 parameters (segment, category, period, dates) |
| KPI-04 | `COUNT(product_id) GROUP BY category` | `COUNT(product_id)` with optional filter |
| VIZ-04 | All periods; monthly aggregation in UI | `period_type` + date range in SQL |

Updated `src/dashboard/README.md`, `DASHBOARD_GUIDE.md` §4 (import), root `README.md`, `candidate-info.md`.

### Files Changed

| File | Change |
|------|--------|
| `src/dashboard/README.md` | Export file, import instructions, filter mapping |
| `src/dashboard/DASHBOARD_GUIDE.md` | Import section §4; export vs SQL comparison |
| `README.md` | Import as recommended dashboard setup |
| `candidate-info.md` | Setup step references export |
| `ai-prompts/08-dashboard-layer.md` | This interaction |

`E-Commerce Analytics Dashboard.lvdash.json` was added by user (Databricks export). No pipeline code modified.

### Validation Status

| Type | Status |
|------|--------|
| Dashboard export in repo | **Complete** |
| Documentation updated | **Complete** |
| Gold-only queries in export | **Verified** (all datasets read `gold.*`) |
| Runtime validation | **Previously complete** (Interaction 3) |

---

## Interaction 5 — Databricks Full-Run Automation + Executive Insights Dashboard

### Objective

Automate the end-to-end run experience so that a single Databricks notebook execution handles seed generation, Bronze/Silver/Gold processing, and validation checks, while also adding a second importable dashboard artifact for executive insights.

### Exact Prompt Sent

User requested one-click operation from Databricks with no manual local data upload, plus an additional `Executive Insights Dashboard.lvdash.json` that can be imported directly.

### AI Response Summary

Implemented and stabilized one-click orchestration in `notebooks/00_run_full_pipeline.ipynb`, then iteratively fixed Databricks environment constraints:

1. Added optional seed generation (`regenerate_seed_data=true|false`) before layer execution.
2. Added automatic dependency bootstrap for `Faker` when missing.
3. Added stage-level PASS/FAIL summary and expected-vs-actual validation report.
4. Added explicit Gold build step via `src/gold/create_gold_tables.py` before running `gold_runtime_validation`.
5. Added robust handling for Databricks filesystem constraints discovered at runtime:
   - `/Volumes/...` direct Python write not supported in this environment.
   - `/dbfs/Volumes/...` direct Python write not supported in this environment.
   - `file:/local_disk0/...` blocked by local filesystem policy.
   - Final approach: generate CSVs under workspace repo path, then copy to volume via `dbutils.fs.cp`.

Also added a second importable dashboard artifact:

- `src/dashboard/Executive Insights Dashboard.lvdash.json`
- Backed by `src/dashboard/executive_insights_queries.sql`
- Gold-only dataset usage preserved.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| One-click automation target | `notebooks/00_run_full_pipeline.ipynb` |
| Seed generation toggle | `regenerate_seed_data` widget |
| Dependency handling | Auto-install `Faker==40.36.0` when missing |
| Gold-stage reliability | Explicit `create_gold_tables.py` call before validation notebook |
| Filesystem compatibility | Workspace path generation + `dbutils.fs.cp` to volume |
| Dashboard deliverable | Added second importable `.lvdash.json` |

### Files Changed

| File | Change |
|------|--------|
| `notebooks/00_run_full_pipeline.ipynb` | One-click automation + resilience updates |
| `src/data_generation/generate_sample_data.py` | Volume-safe CSV write fallback |
| `src/dashboard/executive_insights_queries.sql` | Query set finalized for executive dashboard |
| `src/dashboard/Executive Insights Dashboard.lvdash.json` | Added importable dashboard artifact |
| `src/dashboard/EXECUTIVE_INSIGHTS_DASHBOARD_GUIDE.md` | Added setup and mapping guide |
| `src/dashboard/README.md` | Updated dashboard options/documentation references |

### Validation Status

| Type | Status |
|------|--------|
| Full-run notebook automation logic | **Complete** |
| Runtime blocker diagnosis and fixes | **Complete** |
| Executive dashboard export artifact | **Complete** |
| Gold-only dashboard source rule | **Verified** |
