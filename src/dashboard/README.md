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
gold.revenue_by_customer ─────┼──► dashboard_queries.sql ──► Databricks SQL Dashboard (manual UI)
gold.customer_segmentation ───┤
gold.daily_weekly_trends ─────┘
```

| Rule | Detail |
|------|--------|
| Data source | Gold only — never Bronze or Silver |
| Revenue | Use Gold `total_revenue` / `total_orders` columns |
| UI build | Manual in Databricks SQL Dashboard (see `DASHBOARD_GUIDE.md`) |
| DQ | Dashboard does not re-run Silver DQ checks |

## File structure

| File | Purpose |
|------|---------|
| `dashboard_queries.sql` | 9 widget queries (4 KPIs + 4 visualizations + 1 table) |
| `DASHBOARD_GUIDE.md` | Manual dashboard setup, viz config, filters, validation |
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

| Parameter | Applies to |
|-----------|------------|
| `customer_segment` | KPI-01–03, VIZ-02, TBL-01 |
| `product_category` | KPI-04, VIZ-01 |
| `period_type` | VIZ-04 only |
| `start_date` | VIZ-04 only |
| `end_date` | VIZ-04 only |

Date filters affect **only** the revenue trend chart. KPI and customer/product widgets use lifetime Gold aggregates.

## Segment terminology

| Field | Table | Values | Meaning |
|-------|-------|--------|---------|
| `customer_segment` | `gold.revenue_by_customer` | Premium, Standard, Basic | Marketing tier (filter) |
| `segment_type` | `gold.customer_segmentation` | High-Value, Repeat, One-Time, Inactive | Behavioral segment (pie chart) |

## Setup instructions

1. Ensure Gold tables exist (run `src/gold/create_gold_tables.py`).
2. Open `dashboard_queries.sql` and create each query in Databricks SQL.
3. Follow `DASHBOARD_GUIDE.md` to wire visualizations, layout, and parameters.
4. Run the validation checklist in the guide.

## Validation status

| Check | Status |
|-------|--------|
| SQL queries implemented | Complete |
| Setup guide documented | Complete |
| Databricks Dashboard UI created | Complete (manual) |
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
