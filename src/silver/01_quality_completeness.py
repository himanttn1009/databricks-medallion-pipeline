"""Completeness data quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import CODE_COMPLETENESS
from dq_utils import append_failure_flag


def apply_completeness_customers(df: DataFrame) -> DataFrame:
    """Flag customers with NULL email."""
    return append_failure_flag(df, CODE_COMPLETENESS, F.col("email").isNull())


def apply_completeness_orders(df: DataFrame) -> DataFrame:
    """Flag orders with NULL customer_id or product_id."""
    condition = F.col("customer_id").isNull() | F.col("product_id").isNull()
    return append_failure_flag(df, CODE_COMPLETENESS, condition)
