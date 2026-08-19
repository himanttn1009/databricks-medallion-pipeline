# Executive Insights Dashboard Guide

Second dashboard variant for executive-level monitoring using Gold tables only.

## Purpose

This dashboard complements the main `E-Commerce Analytics Dashboard` with a
decision-focused lens:

- high-value customer monitoring
- inactive customer watch
- top customer concentration
- average-order-value distribution
- trend monitoring by daily/weekly granularity

## Data Contract (Gold-only)

Allowed:

- `gold.sales_by_product`
- `gold.revenue_by_customer`
- `gold.customer_segmentation`
- `gold.daily_weekly_trends`

Forbidden:

- `bronze.*`
- `silver.*`
- raw CSV paths

## Query File

Use:

- `src/dashboard/executive_insights_queries.sql`

It contains 9 widgets:

- 4 KPI queries (EX-KPI-01..04)
- 4 visualization queries (EX-VIZ-01..04)
- 1 table query (EX-TBL-01)

## Recommended Widgets

| Query | Suggested Visualization |
|------|--------------------------|
| EX-KPI-01 | Counter (Revenue) |
| EX-KPI-02 | Counter (High-Value Customers) |
| EX-KPI-03 | Counter (Inactive Customers) |
| EX-KPI-04 | Counter (Active Categories) |
| EX-VIZ-01 | Horizontal Bar (Top 10 Customers by Revenue) |
| EX-VIZ-02 | Histogram (Avg Order Value Distribution) |
| EX-VIZ-03 | Pie (Behavioral Segment Share) |
| EX-VIZ-04 | Line (Revenue Trend) |
| EX-TBL-01 | Table (Customer Priority View) |

## Parameters

Create dashboard-level parameters:

- `customer_segment` (multi-select)
- `product_category` (multi-select)
- `period_type` (single-select: DAILY/WEEKLY; default DAILY)
- `start_date` (date)
- `end_date` (date)

## Build Steps (Manual)

1. Open Databricks SQL > Dashboards > Create dashboard.
2. Name: `Executive Insights Dashboard`.
3. Create 9 queries from `executive_insights_queries.sql` (one block at a time).
4. Configure visualizations per table above.
5. Add parameters and map to queries.
6. Save and run all tiles.

## Validation Checklist

- [ ] All 9 queries run without SQL error
- [ ] All queries read `gold.*` only
- [ ] EX-KPI-01 returns revenue value
- [ ] EX-KPI-02/03 counters are non-negative
- [ ] EX-VIZ-01 returns 10 rows max
- [ ] EX-VIZ-04 responds to `period_type` and date range
- [ ] EX-TBL-01 sorted by revenue descending

## Notes

- This dashboard is separate from the exported
  `E-Commerce Analytics Dashboard.lvdash.json`.
- If desired, you can export this dashboard too after manual creation and store
  it alongside the existing `.lvdash.json` file.
