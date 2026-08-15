# Gold Layer

Business-ready aggregations for analytics consumption.

## Planned Files

| File | Purpose |
|------|---------|
| `01_sales_by_product.sql` | Sales by product aggregation |
| `02_revenue_by_customer.sql` | Revenue by customer aggregation |
| `03_daily_weekly_trends.sql` | Daily/weekly trends aggregation |
| `04_customer_segmentation.sql` | Customer segmentation aggregation |
| `create_gold_tables.py` | Orchestrate Gold table creation |

## Required Aggregation Tables

1. **Sales by Product** — product_id, product_name, category, total_orders, total_revenue, avg_order_value
2. **Revenue by Customer** — customer_id, customer_name, customer_segment, total_orders, total_revenue, avg_order_value, lifetime_value_actual
3. **Customer Segmentation** — segment_type, customer_count, avg_revenue, total_revenue
