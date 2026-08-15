"""Sales by product Gold aggregation."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from gold_utils import to_decimal_2


def build_sales_by_product(
    qualifying_orders: DataFrame,
    valid_products: DataFrame,
) -> DataFrame:
    """
    Build gold.sales_by_product.

    Qualifying orders inner-joined to valid products (GD-01, GD-02).
    Products with zero qualifying orders are omitted.
    """
    joined = qualifying_orders.join(valid_products, on="product_id", how="inner")

    aggregated = joined.groupBy("product_id", "product_name", "category").agg(
        F.countDistinct("order_id").alias("total_orders"),
        F.sum("total_amount").alias("_sum_amount"),
    )

    return aggregated.select(
        "product_id",
        "product_name",
        "category",
        "total_orders",
        to_decimal_2(F.col("_sum_amount")).alias("total_revenue"),
        to_decimal_2(F.col("_sum_amount") / F.col("total_orders")).alias("avg_order_value"),
    )
