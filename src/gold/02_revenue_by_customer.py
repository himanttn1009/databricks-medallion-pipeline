"""Revenue by customer Gold aggregation."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from gold_utils import to_decimal_2


def build_revenue_by_customer(
    valid_customers: DataFrame,
    qualifying_orders: DataFrame,
    valid_products: DataFrame,
) -> DataFrame:
    """
    Build gold.revenue_by_customer.

    Valid customers LEFT JOIN qualifying orders with valid product (GD-11, GD-13).
    Includes customers with zero qualifying orders.
    """
    orders_attributed = qualifying_orders.join(
        valid_products.select("product_id"),
        on="product_id",
        how="inner",
    )

    order_aggs = orders_attributed.groupBy("customer_id").agg(
        F.countDistinct("order_id").alias("total_orders"),
        F.sum("total_amount").alias("_sum_amount"),
    )

    joined = valid_customers.join(order_aggs, on="customer_id", how="left")

    with_orders = joined.withColumn(
        "total_orders",
        F.coalesce(F.col("total_orders"), F.lit(0)),
    ).withColumn(
        "total_revenue",
        to_decimal_2(F.coalesce(F.col("_sum_amount"), F.lit(0))),
    )

    return with_orders.select(
        "customer_id",
        "customer_name",
        "customer_segment",
        "total_orders",
        "total_revenue",
        F.when(
            F.col("total_orders") > 0,
            to_decimal_2(F.col("total_revenue") / F.col("total_orders")),
        )
        .otherwise(F.lit(None).cast("decimal(18,2)"))
        .alias("avg_order_value"),
        F.col("total_revenue").alias("lifetime_value_actual"),
    )
