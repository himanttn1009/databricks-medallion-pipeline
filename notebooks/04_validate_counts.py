# Databricks notebook source
# COMMAND ----------
# Quick validation counts

checks = [
    ("bronze.customers", 10000),
    ("bronze.products", 500),
    ("bronze.orders", 100000),
    ("silver.customers", 10000),
    ("silver.products", 500),
    ("silver.orders", 100000),
    ("gold.sales_by_product", 500),
    ("gold.revenue_by_customer", 9940),
    ("gold.customer_segmentation", 4),
    ("gold.daily_weekly_trends", 2679),
]

for table_name, expected in checks:
    actual = spark.table(table_name).count()
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status} | {table_name}: actual={actual}, expected={expected}")

print("\nLatest silver.dq_metrics (10 rows):")
display(
    spark.sql(
        """
        SELECT *
        FROM silver.dq_metrics
        ORDER BY run_timestamp DESC
        LIMIT 10
        """
    )
)
