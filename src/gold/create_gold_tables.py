"""Orchestrate Gold table creation."""

from __future__ import annotations

import sys

from pyspark.sql import SparkSession

from gold_utils import (
    GoldProcessingError,
    ensure_gold_schema_exists,
    load_qualifying_orders,
    load_silver_entity,
    load_valid_customers,
    load_valid_products,
    validate_gold_dataframe,
    validate_gold_outputs,
    validate_silver_prerequisites,
    write_gold_table,
)
from importlib import import_module

sales_by_product = import_module("01_sales_by_product")
revenue_by_customer = import_module("02_revenue_by_customer")
daily_weekly_trends = import_module("03_daily_weekly_trends")
customer_segmentation = import_module("04_customer_segmentation")


def main() -> int:
    """Run the full Gold aggregation pipeline."""
    spark = SparkSession.builder.appName("gold-create-tables").getOrCreate()

    print("Starting Gold processing")

    try:
        ensure_gold_schema_exists(spark)
        validate_silver_prerequisites(spark)

        silver_customers = load_silver_entity(spark, "customers")
        silver_products = load_silver_entity(spark, "products")
        silver_orders = load_silver_entity(spark, "orders")

        valid_customers = load_valid_customers(silver_customers)
        valid_products = load_valid_products(silver_products)
        qualifying_orders = load_qualifying_orders(silver_orders)

        gold_sales = sales_by_product.build_sales_by_product(
            qualifying_orders,
            valid_products,
        )
        validate_gold_dataframe(gold_sales, "sales_by_product")
        write_gold_table(gold_sales, "sales_by_product")

        gold_revenue = revenue_by_customer.build_revenue_by_customer(
            valid_customers,
            qualifying_orders,
            valid_products,
        )
        validate_gold_dataframe(gold_revenue, "revenue_by_customer")
        write_gold_table(gold_revenue, "revenue_by_customer")

        gold_trends = daily_weekly_trends.build_daily_weekly_trends(qualifying_orders)
        validate_gold_dataframe(gold_trends, "daily_weekly_trends")
        write_gold_table(gold_trends, "daily_weekly_trends")

        gold_segments = customer_segmentation.build_customer_segmentation(gold_revenue)
        validate_gold_dataframe(gold_segments, "customer_segmentation")
        write_gold_table(gold_segments, "customer_segmentation")

        row_counts = validate_gold_outputs(spark)

    except GoldProcessingError as exc:
        print(f"[FAILED] Gold processing: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FAILED] Gold processing: {exc}", file=sys.stderr)
        return 1

    print("\n--- Gold Processing Summary ---")
    for table, count in row_counts.items():
        print(f"  - gold.{table}: {count} rows")
    print("\nGold processing completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
