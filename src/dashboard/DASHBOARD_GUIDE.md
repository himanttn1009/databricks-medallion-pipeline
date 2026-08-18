# Databricks SQL Dashboard Guide

Manual setup guide for the E-Commerce Revenue Dashboard. Queries are versioned in `dashboard_queries.sql`; the validated dashboard UI is exported as `E-Commerce Analytics Dashboard.lvdash.json`.

> **Dashboard design:** COMPLETE  
> **Dashboard SQL implementation:** COMPLETE  
> **Databricks Dashboard UI:** COMPLETE (`.lvdash.json` export)  
> **Runtime validation:** COMPLETE (manual)

---

## 1. Dashboard objective

Provide business stakeholders with a **Gold-only** view of:

- Portfolio revenue and order volume
- Product performance (top sellers)
- Customer revenue distribution and behavioral segmentation
- Daily/weekly revenue trends
- Customer-level revenue and order detail

The dashboard consumes curated Gold tables produced by the medallion pipeline. It does **not** read Bronze or Silver.

---

## 2. Prerequisites

| Requirement | Detail |
|-------------|--------|
| Databricks workspace | SQL access (Free Edition Serverless supported) |
| Gold tables | `gold.sales_by_product`, `gold.revenue_by_customer`, `gold.customer_segmentation`, `gold.daily_weekly_trends` |
| Gold pipeline | `create_gold_tables.py` completed successfully |
| SQL warehouse | Running SQL warehouse or serverless SQL endpoint |
| Repo files | `src/dashboard/dashboard_queries.sql`, `E-Commerce Analytics Dashboard.lvdash.json` |

**Validated Gold baseline (reference only):**

| Table | Rows |
|-------|------|
| `gold.sales_by_product` | 500 |
| `gold.revenue_by_customer` | 9,940 |
| `gold.customer_segmentation` | 4 |
| `gold.daily_weekly_trends` | 2,679 |

---

## 3. Gold tables used

| Gold table | Widgets |
|------------|---------|
| `gold.revenue_by_customer` | KPI-01, KPI-02, KPI-03, VIZ-02, TBL-01 |
| `gold.sales_by_product` | KPI-04, VIZ-01 |
| `gold.customer_segmentation` | VIZ-03 |
| `gold.daily_weekly_trends` | VIZ-04 |

**Gold-only rule:** Never query `bronze.*`, `silver.*`, or `silver.dq_metrics` from dashboard queries.

---

## 4. How to import the dashboard export (recommended)

The file **`E-Commerce Analytics Dashboard.lvdash.json`** is a Databricks Lakeview dashboard export containing the runtime-validated dashboard configuration.

### Import steps

1. Open **Databricks** → **SQL** → **Dashboards**.
2. Click **Import dashboard** (or **Create** → **Import**).
3. Upload `src/dashboard/E-Commerce Analytics Dashboard.lvdash.json`.
4. Name: `E-Commerce Analytics Dashboard` (or keep imported name).
5. After import, open each dataset and **Run** once to confirm Gold table access.
6. Open the **Global Filters** page and verify **Product Category** filter loads.

### What the export contains

| Component | Count | Details |
|-----------|-------|---------|
| Datasets | 9 | KPI-01 through KPI-04, VIZ-01 through VIZ-04, TBL-01 |
| Widgets | 9 | 4 counters, bar, histogram, pie, line, table |
| Global filters | 1 | Product Category (associative multi-select on VIZ-01 + KPI-04 datasets) |
| Gold tables used | 4 | All queries read `gold.*` only |

### Export vs `dashboard_queries.sql`

| Topic | `.lvdash.json` export | `dashboard_queries.sql` |
|-------|----------------------|-------------------------|
| Purpose | Recreate validated Databricks UI | Parameterized SQL reference |
| Filters | Product Category only (associative) | 5 parameters (`customer_segment`, `product_category`, `period_type`, dates) |
| KPI-04 SQL | `COUNT(product_id) GROUP BY category` (counter sums across categories) | `COUNT(product_id)` with optional category filter |
| VIZ-04 | All trend rows; line chart aggregates by month in UI | `period_type` + date range parameters in SQL |

To add customer-segment or date filters, extend the imported dashboard using the parameterized SQL in `dashboard_queries.sql` (sections 15–16).

> **Note:** Filter widget internal paths (`dashboards/01f198d45...`) are Databricks workspace IDs. They are rewritten on import; no manual edit needed.

---

## 5. How to create the dashboard manually (alternative)

If you prefer not to import the JSON:

1. Open **Databricks** → **SQL** → **Dashboards**.
2. Click **Create dashboard**.
3. Name: `E-Commerce Revenue Dashboard (Gold)`.
4. Add a short description: *Business analytics from Gold layer; completed valid orders only.*
5. Save the empty dashboard — queries are added in the next section.

---

## 6. How to create each query (manual build)

For each widget below:

1. In the dashboard editor, click **Create** → **Query** (or add from SQL editor and pin to dashboard).
2. Copy the corresponding SQL block from `dashboard_queries.sql` (search for `-- QUERY: KPI-01`, etc.).
3. Paste into the SQL editor.
4. Run the query once to verify it returns data.
5. Save the query with the widget ID as the name (e.g. `KPI-01 Total Revenue`).
6. Add a **visualization** tile linked to that query (see sections 8–13).
7. Arrange tiles per the layout in section 14.

Repeat for all 9 queries.

---

## 7. Query → visualization mapping

| Query ID | Visualization | Gold source |
|----------|---------------|-------------|
| KPI-01 | Counter | `gold.revenue_by_customer` |
| KPI-02 | Counter | `gold.revenue_by_customer` |
| KPI-03 | Counter | `gold.revenue_by_customer` |
| KPI-04 | Counter | `gold.sales_by_product` |
| VIZ-01 | Bar chart | `gold.sales_by_product` |
| VIZ-02 | Histogram | `gold.revenue_by_customer` |
| VIZ-03 | Pie chart | `gold.customer_segmentation` |
| VIZ-04 | Line chart | `gold.daily_weekly_trends` |
| TBL-01 | Table | `gold.revenue_by_customer` |

---

## 8. Exact visualization type for each widget

| Widget | Databricks viz type |
|--------|---------------------|
| KPI-01 | **Counter** |
| KPI-02 | **Counter** |
| KPI-03 | **Counter** |
| KPI-04 | **Counter** |
| VIZ-01 | **Bar chart** (horizontal recommended) |
| VIZ-02 | **Histogram** |
| VIZ-03 | **Pie chart** |
| VIZ-04 | **Line chart** |
| TBL-01 | **Table** |

---

## 9. KPI configuration

For each KPI query (KPI-01 through KPI-04):

1. Select visualization type **Counter**.
2. **Value column:**
   - KPI-01 → `total_revenue`
   - KPI-02 → `total_orders`
   - KPI-03 → `customer_count`
   - KPI-04 → `product_count`
3. Format KPI-01 as currency (2 decimal places) if the UI supports it.
4. Title each counter clearly (e.g. "Total Revenue").

---

## 10. Histogram configuration (VIZ-02)

1. Query: `VIZ-02` from `dashboard_queries.sql`.
2. Visualization: **Histogram**.
3. **X-axis / Value:** `total_revenue`
4. **Count / Frequency:** automatic (Databricks bins the distribution).
5. Include zero-revenue customers — do not filter `total_revenue = 0` in SQL.
6. Optional color: `customer_segment` (marketing tier) for legend only.

---

## 11. Pie chart configuration (VIZ-03)

1. Query: `VIZ-03` from `dashboard_queries.sql`.
2. Visualization: **Pie chart**.
3. **Slice labels:** `segment_type` (behavioral: High-Value, Repeat, One-Time, Inactive).
4. **Slice size / measure:** `customer_count` (primary).
5. Do **not** use `customer_segment` (Premium/Standard/Basic) — that is marketing tier, not behavioral segmentation.

---

## 12. Bar chart configuration (VIZ-01)

1. Query: `VIZ-01` from `dashboard_queries.sql`.
2. Visualization: **Bar chart** (horizontal recommended for long product names).
3. **X-axis / Value:** `total_revenue`
4. **Y-axis / Category:** `product_name`
5. **Color (optional):** `category`
6. **Tooltip:** `total_orders`, `category`
7. Sort is defined in SQL (`total_revenue DESC`); limit 10 in SQL.

---

## 13. Line chart configuration (VIZ-04)

1. Query: `VIZ-04` from `dashboard_queries.sql`.
2. Visualization: **Line chart**.
3. **X-axis:** `period_start`
4. **Y-axis (primary):** `total_revenue`
5. **Y-axis (optional secondary):** `total_orders`
6. Map dashboard parameters `:period_type`, `:start_date`, `:end_date` to this query only.

---

## 14. Table configuration (TBL-01)

1. Query: `TBL-01` from `dashboard_queries.sql`.
2. Visualization: **Table**.
3. Display all columns returned by the query.
4. Default sort: `total_revenue DESC` (in SQL).
5. Row limit: 500 (in SQL).

---

## 15. Dashboard layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  E-Commerce Revenue Dashboard (Gold)                                        │
├──────────────┬──────────────┬──────────────┬──────────────────────────────┤
│ KPI-01       │ KPI-02       │ KPI-03       │ KPI-04                        │
│ Total Revenue│ Total Orders │ Customers    │ Active Products               │
├──────────────────────────────┬──────────────────────────────────────────────┤
│ VIZ-01 Top 10 Products       │ VIZ-04 Revenue Trend                        │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ VIZ-02 Customer Revenue        │ VIZ-03 Customer Segmentation                │
│ Distribution (Histogram)     │ (Pie — behavioral segment_type)             │
├──────────────────────────────┴──────────────────────────────────────────────┤
│ TBL-01 Customer Revenue & Order Detail                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filters: Category | Customer Segment | Period Type | Start Date | End Date │
└─────────────────────────────────────────────────────────────────────────────┘
```

Place the filter bar at the top or bottom of the dashboard.

---

## 16. Parameter / filter creation (manual / extended filters)

Create these **dashboard-level parameters** in the Databricks SQL Dashboard UI:

| Parameter | Type | Suggested setup |
|-----------|------|-----------------|
| `customer_segment` | Multi-select (Array or Query) | Query: `SELECT DISTINCT customer_segment FROM gold.revenue_by_customer ORDER BY 1` |
| `product_category` | Multi-select (Array or Query) | Query: `SELECT DISTINCT category FROM gold.sales_by_product ORDER BY 1` |
| `period_type` | Single-select (Text/Enum) | Values: `DAILY`, `WEEKLY` |
| `start_date` | Date | Default from helper query below |
| `end_date` | Date | Default from helper query below |

**Helper — default date range (DAILY):**

```sql
SELECT
  MIN(period_start) AS default_start_date,
  MAX(period_start) AS default_end_date
FROM gold.daily_weekly_trends
WHERE period_type = 'DAILY';
```

Map each parameter to the queries listed in section 16.

**Multi-select empty = all rows:** Queries use `COALESCE(cardinality(:param), 0) = 0 OR ... IN (SELECT EXPLODE(:param))`. When no values are selected, leave the parameter unset or empty so all rows pass the filter.

---

## 17. Parameter-to-query mapping

| Parameter | KPI-01 | KPI-02 | KPI-03 | KPI-04 | VIZ-01 | VIZ-02 | VIZ-03 | VIZ-04 | TBL-01 |
|-----------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| `customer_segment` | ✓ | ✓ | ✓ | | | ✓ | | | ✓ |
| `product_category` | | | | ✓ | ✓ | | | | |
| `period_type` | | | | | | | | ✓ | |
| `start_date` | | | | | | | | ✓ | |
| `end_date` | | | | | | | | ✓ | |

### Important: date filter scope

**Date filters (`start_date`, `end_date`, `period_type`) affect ONLY the Revenue Trend visualization (VIZ-04).**

KPI cards and customer/product charts use **lifetime Gold aggregates** from `gold.revenue_by_customer` and `gold.sales_by_product`. Those tables do not have an order-date dimension. Date slicing would require order-level Gold data, which is intentionally not created.

---

## 18. Expected default values

| Parameter | Default |
|-----------|---------|
| `customer_segment` | All (empty / unset → all marketing tiers) |
| `product_category` | All (empty / unset → all categories) |
| `period_type` | `DAILY` |
| `start_date` | `MIN(period_start)` from `gold.daily_weekly_trends` where `period_type = 'DAILY'` |
| `end_date` | `MAX(period_start)` from `gold.daily_weekly_trends` where `period_type = 'DAILY'` |

**Unfiltered KPI expectations (reference from Gold runtime):**

| KPI | Observed (default filters) |
|-----|---------------------------|
| Total Revenue | 40.03M |
| Total Orders | 69.58K |
| Customer Count | 9,940 (displayed as 9.94K) |
| Active Products | 500 |

---

## 19. Validation checklist

After building the dashboard UI:

- [x] All 9 queries run without error in SQL editor
- [x] No query references `bronze.*` or `silver.*`
- [x] KPI-01 equals `SUM(gold.revenue_by_customer.total_revenue)` (unfiltered)
- [x] KPI-03 shows 9,940 customers (unfiltered)
- [x] KPI-04 shows 500 products (unfiltered)
- [x] VIZ-01 returns ≤ 10 rows
- [x] VIZ-02 includes customers with `total_revenue = 0`
- [x] VIZ-03 shows 4 behavioral `segment_type` values
- [x] VIZ-04 responds to date and period_type filters only
- [x] `customer_segment` filter narrows KPIs, histogram, and table — not pie chart
- [x] `product_category` filter narrows product KPI and bar chart only
- [x] Assignment minimum: bar + histogram + pie present

---

## 20. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Parameter syntax error | Array param not configured | Set parameter type to Array in dashboard UI; or use Query-based multi-select |
| Empty KPI after filter | Over-restrictive selection | Clear filter or select all values |
| Pie chart shows wrong segments | Used `customer_segment` | Use VIZ-03 (`segment_type` behavioral) |
| Trend chart empty | Date range outside data | Reset `start_date`/`end_date` using helper query |
| KPI revenue ≠ trend sum | Expected | KPIs are lifetime; trend is date-filtered (DD-01) |
| Country filter requested | Not in Gold (GD-07) | Do not join Silver; country filter is out of scope |
| `cardinality` error | Scalar param instead of Array | Configure multi-select as Array type |

---

## 21. Important Gold-only rule

The dashboard is the **consumption layer** for Gold analytics:

- **Read:** `gold.sales_by_product`, `gold.revenue_by_customer`, `gold.customer_segmentation`, `gold.daily_weekly_trends`
- **Never read:** Bronze, Silver, DQ metrics, or source CSVs
- **Never recompute** revenue from raw orders — use Gold `total_revenue` and `total_orders`
- **Never modify** Gold tables from dashboard queries

Revenue in Gold reflects completed, valid orders only (enforced upstream in Silver/Gold). The dashboard displays those values as-is.
