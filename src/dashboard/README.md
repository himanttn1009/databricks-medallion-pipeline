# Dashboard Layer

Databricks SQL Dashboard queries and manual setup guide for Gold-layer business analytics.

> **Dashboard design:** COMPLETE  
> **Dashboard SQL implementation:** COMPLETE  
> **Databricks Dashboard UI:** COMPLETE (manual)  
> **Runtime validation:** COMPLETE (manual)

## Purpose

Deliver assignment-required visualizations (bar chart, histogram, pie chart) plus KPI counters, revenue trends, and customer detail — all sourced from **Gold tables only**.

## Architecture

```
gold.sales_by_product ────────┐
gold.revenue_by_customer ─────┼──► dashboard_queries.sql ──► Databricks SQL Dashboard
gold.customer_segmentation ───┤         │
gold.daily_weekly_trends ─────┘         └── E-Commerce Analytics Dashboard.lvdash.json (export)
```

| Rule | Detail |
|------|--------|
| Data source | Gold only — never Bronze or Silver |
| Revenue | Use Gold `total_revenue` / `total_orders` columns |
| UI build | Import `.lvdash.json` **or** manual setup per `DASHBOARD_GUIDE.md` |
| DQ | Dashboard does not re-run Silver DQ checks |

## File structure

| File | Purpose |
|------|---------|
| `dashboard_queries.sql` | 9 parameterized widget queries (reference / manual build) |
| `executive_insights_queries.sql` | 9 additional executive-insight queries (second dashboard variant) |
| `E-Commerce Analytics Dashboard.lvdash.json` | **Databricks dashboard export** — import to recreate UI |
| `DASHBOARD_GUIDE.md` | Setup guide (import + manual), viz config, filters, validation |
| `EXECUTIVE_INSIGHTS_DASHBOARD_GUIDE.md` | Manual setup guide for second dashboard variant |
| `README.md` | This overview |

## Widget inventory

| ID | Type | Title | Gold source |
|----|------|-------|-------------|
| KPI-01 | Counter | Total Revenue | `gold.revenue_by_customer` |
| KPI-02 | Counter | Total Orders | `gold.revenue_by_customer` |
| KPI-03 | Counter | Customer Count | `gold.revenue_by_customer` |
| KPI-04 | Counter | Active Products | `gold.sales_by_product` |
| VIZ-01 | Bar chart | Top 10 Products by Revenue | `gold.sales_by_product` |
| VIZ-02 | Histogram | Customer Revenue Distribution | `gold.revenue_by_customer` |
| VIZ-03 | Pie chart | Customer Segmentation | `gold.customer_segmentation` |
| VIZ-04 | Line chart | Revenue Trend | `gold.daily_weekly_trends` |
| TBL-01 | Table | Customer Revenue & Order Detail | `gold.revenue_by_customer` |

## Filter inventory

| Parameter | Applies to | In `.lvdash.json` export |
|-----------|------------|--------------------------|
| `customer_segment` | KPI-01–03, VIZ-02, TBL-01 | Not in export — add manually via `dashboard_queries.sql` |
| `product_category` | KPI-04, VIZ-01 | **Yes** — Global Filters (associative multi-select) |
| `period_type` | VIZ-04 only | Not in export — trend uses all periods in dataset |
| `start_date` | VIZ-04 only | Not in export |
| `end_date` | VIZ-04 only | Not in export |

Date filters affect **only** the revenue trend chart. KPI and customer/product widgets use lifetime Gold aggregates.

## Segment terminology

| Field | Table | Values | Meaning |
|-------|-------|--------|---------|
| `customer_segment` | `gold.revenue_by_customer` | Premium, Standard, Basic | Marketing tier (filter) |
| `segment_type` | `gold.customer_segmentation` | High-Value, Repeat, One-Time, Inactive | Behavioral segment (pie chart) |

## Setup instructions

### Option A — Import dashboard export (recommended)

1. Ensure Gold tables exist (run `src/gold/create_gold_tables.py`).
2. In Databricks: **SQL** → **Dashboards** → **Import** (or **Create** → **Import dashboard**).
3. Select `E-Commerce Analytics Dashboard.lvdash.json` from this folder.
4. Confirm all 9 datasets resolve against your `gold.*` tables.
5. Open the dashboard and verify widgets load (see validation checklist in `DASHBOARD_GUIDE.md`).

### Option B — Manual build

1. Ensure Gold tables exist (run `src/gold/create_gold_tables.py`).
2. Open `dashboard_queries.sql` and create each query in Databricks SQL.
3. Follow `DASHBOARD_GUIDE.md` to wire visualizations, layout, and parameters.
4. Run the validation checklist in the guide.

### Option C — Executive Insights dashboard (new)

1. Create a new dashboard: `Executive Insights Dashboard`.
2. Build queries from `executive_insights_queries.sql`.
3. Follow `EXECUTIVE_INSIGHTS_DASHBOARD_GUIDE.md`.
4. (Optional) Export as `.lvdash.json` after setup.

### Export vs SQL reference

| Artifact | Role |
|----------|------|
| `.lvdash.json` | Runtime dashboard as built in Databricks (actual widget + filter config) |
| `dashboard_queries.sql` | Parameterized Gold-only SQL reference (`:customer_segment`, date filters, etc.) |

The export uses **Databricks associative filters** for Product Category. Additional parameters in `dashboard_queries.sql` (customer segment, period type, dates) can be added manually if needed — see `DASHBOARD_GUIDE.md` §15–16.

## Validation status

| Check | Status |
|-------|--------|
| SQL queries implemented | Complete |
| Setup guide documented | Complete |
| Databricks Dashboard UI created | Complete (imported `.lvdash.json` + manual validation) |
| Query execution in Databricks | Complete |
| Dashboard runtime validation | Complete |

### Observed baseline (default filters)

| KPI | Value |
|-----|-------|
| Total Revenue | 40.03M |
| Total Orders | 69.58K |
| Customer Count | 9.94K |
| Active Products | 500 |

## Related documentation

- `design-notes.md` §6 — Dashboard design
- `assignment/assignment-requirements.md` §9 — Assignment requirements
- `ai-prompts/08-dashboard-layer.md` — AI prompt history
