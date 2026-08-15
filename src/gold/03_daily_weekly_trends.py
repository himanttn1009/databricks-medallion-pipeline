"""Daily and weekly trends Gold aggregation."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import PERIOD_DAILY, PERIOD_WEEKLY
from gold_utils import to_decimal_2


def build_daily_weekly_trends(qualifying_orders: DataFrame) -> DataFrame:
    """
    Build gold.daily_weekly_trends.

    Uses qualifying orders only (GD-14). Daily and weekly rows in one table.
    Weekly rows: order_date NULL, period_start = Monday week anchor (GD-04, GD-05).
    """
    daily = (
        qualifying_orders.groupBy("order_date")
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.sum("total_amount").alias("_sum_amount"),
        )
        .withColumn("period_type", F.lit(PERIOD_DAILY))
        .withColumn("period_start", F.col("order_date"))
        .select(
            F.col("order_date"),
            "period_type",
            "period_start",
            "total_orders",
            to_decimal_2(F.col("_sum_amount")).alias("total_revenue"),
        )
    )

    weekly = (
        qualifying_orders.withColumn(
            "period_start",
            F.date_trunc("week", F.col("order_date")).cast("date"),
        )
        .groupBy("period_start")
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.sum("total_amount").alias("_sum_amount"),
        )
        .withColumn("period_type", F.lit(PERIOD_WEEKLY))
        .withColumn("order_date", F.lit(None).cast("date"))
        .select(
            "order_date",
            "period_type",
            "period_start",
            "total_orders",
            to_decimal_2(F.col("_sum_amount")).alias("total_revenue"),
        )
    )

    return daily.unionByName(weekly)
