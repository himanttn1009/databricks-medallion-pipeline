"""Orchestrate Silver table creation and DQ metrics reporting."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from dq_utils import (
    SilverProcessingError,
    build_customer_signup_lookup,
    compute_metrics_for_entity,
    distinct_parent_keys,
    ensure_silver_schema_exists,
    finalize_quality_columns,
    generate_run_id,
    load_bronze_entity,
    validate_bronze_prerequisites,
    write_dq_metrics,
    write_silver_table,
)
from importlib import import_module

completeness = import_module("01_quality_completeness")
uniqueness = import_module("02_quality_uniqueness")
type_validation = import_module("03_quality_type_validation")
referential_integrity = import_module("04_quality_referential_integrity")
business_logic = import_module("05_quality_business_logic")


def main() -> int:
    """Run the full Silver DQ pipeline."""
    spark = SparkSession.builder.appName("silver-create-tables").getOrCreate()
    run_id = generate_run_id()
    run_timestamp = datetime.now(timezone.utc)
    all_metrics = []

    print(f"Starting Silver processing (run_id={run_id})")

    try:
        ensure_silver_schema_exists(spark)
        validate_bronze_prerequisites(spark)

        bronze_customers = load_bronze_entity(spark, "customers")
        bronze_products = load_bronze_entity(spark, "products")
        bronze_orders = load_bronze_entity(spark, "orders")

        customers_df = bronze_customers
        customers_df = completeness.apply_completeness_customers(customers_df)
        customers_df = uniqueness.apply_uniqueness(customers_df, "customer_id")
        customers_df = type_validation.apply_type_validation_customers(customers_df)
        all_metrics.extend(
            compute_metrics_for_entity(customers_df, "customers", run_id, run_timestamp)
        )
        silver_customers = finalize_quality_columns(customers_df, run_timestamp)

        products_df = bronze_products
        products_df = type_validation.apply_type_validation_products(products_df)
        products_df = business_logic.apply_business_logic_products(products_df)
        all_metrics.extend(
            compute_metrics_for_entity(products_df, "products", run_id, run_timestamp)
        )
        silver_products = finalize_quality_columns(products_df, run_timestamp)

        valid_customer_ids = distinct_parent_keys(bronze_customers, "customer_id")
        valid_product_ids = distinct_parent_keys(bronze_products, "product_id")
        customer_signup_lookup = build_customer_signup_lookup(bronze_customers)

        orders_df = bronze_orders
        orders_df = completeness.apply_completeness_orders(orders_df)
        orders_df = uniqueness.apply_uniqueness(orders_df, "order_id")
        orders_df = type_validation.apply_type_validation_orders(orders_df)
        orders_df = referential_integrity.apply_referential_integrity(
            orders_df,
            valid_customer_ids,
            valid_product_ids,
        )
        orders_df = business_logic.apply_business_logic_orders(
            orders_df,
            customer_signup_lookup,
        )
        all_metrics.extend(
            compute_metrics_for_entity(orders_df, "orders", run_id, run_timestamp)
        )
        silver_orders = finalize_quality_columns(orders_df, run_timestamp)

        write_silver_table(silver_customers, "customers")
        write_silver_table(silver_products, "products")
        write_silver_table(silver_orders, "orders")
        write_dq_metrics(spark, all_metrics)

    except SilverProcessingError as exc:
        print(f"[FAILED] Silver processing: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FAILED] Silver processing: {exc}", file=sys.stderr)
        return 1

    print("\n--- Silver Processing Summary ---")
    print(f"run_id: {run_id}")
    print(f"metrics_rows: {len(all_metrics)}")
    for metric in all_metrics:
        status = "MET" if metric.threshold_met else "NOT MET"
        print(
            f"  - {metric.check_name}: {metric.pass_pct}% pass "
            f"(threshold {metric.threshold_pct}%, {status})"
        )
    print("\nSilver processing completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
