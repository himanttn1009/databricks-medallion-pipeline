"""Referential integrity data quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import CODE_REFERENTIAL_INTEGRITY
from dq_utils import append_failure_flag


def apply_referential_integrity(
    orders_df: DataFrame,
    valid_customer_ids: DataFrame,
    valid_product_ids: DataFrame,
) -> DataFrame:
    """
    Flag orders with non-null orphan foreign keys.

    Parent keys are distinct values from Bronze parent tables (SD-04).
    NULL FKs are not RI failures (completeness owns NULLs).
    """
    customers = valid_customer_ids.select(
        F.col("customer_id").alias("_valid_customer_id")
    )
    products = valid_product_ids.select(
        F.col("product_id").alias("_valid_product_id")
    )

    joined = (
        orders_df.join(customers, orders_df.customer_id == customers._valid_customer_id, "left")
        .join(products, orders_df.product_id == products._valid_product_id, "left")
    )

    orphan_customer = F.col("customer_id").isNotNull() & F.col("_valid_customer_id").isNull()
    orphan_product = F.col("product_id").isNotNull() & F.col("_valid_product_id").isNull()
    condition = orphan_customer | orphan_product

    flagged = append_failure_flag(joined, CODE_REFERENTIAL_INTEGRITY, condition)
    return flagged.drop("_valid_customer_id", "_valid_product_id")
