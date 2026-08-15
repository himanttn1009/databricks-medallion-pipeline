"""Customer segmentation Gold aggregation."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import (
    P75_PERCENTILE,
    SEGMENT_HIGH_VALUE,
    SEGMENT_INACTIVE,
    SEGMENT_ONE_TIME,
    SEGMENT_REPEAT,
)
from gold_utils import to_decimal_2


def _compute_p75(revenue_by_customer: DataFrame) -> float:
    """75th percentile of total_revenue among customers with total_orders >= 1."""
    paying = revenue_by_customer.filter(F.col("total_orders") >= 1)
    if paying.count() == 0:
        return 0.0

    row = paying.agg(
        F.expr(f"percentile_approx(total_revenue, {P75_PERCENTILE})").alias("p75")
    ).collect()[0]
    return float(row["p75"] or 0.0)


def build_customer_segmentation(revenue_by_customer: DataFrame) -> DataFrame:
    """
    Build gold.customer_segmentation from revenue_by_customer (GD-03, GD-09).

    Uses the same per-customer revenue definition; empty segment buckets omitted.
    """
    p75 = _compute_p75(revenue_by_customer)

    labeled = revenue_by_customer.withColumn(
        "segment_type",
        F.when(F.col("total_orders") == 0, F.lit(SEGMENT_INACTIVE))
        .when(F.col("total_orders") == 1, F.lit(SEGMENT_ONE_TIME))
        .when(
            (F.col("total_orders") >= 2) & (F.col("total_revenue") >= F.lit(p75)),
            F.lit(SEGMENT_HIGH_VALUE),
        )
        .when(F.col("total_orders") >= 2, F.lit(SEGMENT_REPEAT)),
    )

    return (
        labeled.groupBy("segment_type")
        .agg(
            F.count("customer_id").alias("customer_count"),
            to_decimal_2(F.avg("total_revenue")).alias("avg_revenue"),
            to_decimal_2(F.sum("total_revenue")).alias("total_revenue"),
        )
        .filter(F.col("customer_count") > 0)
    )
