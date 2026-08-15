"""Uniqueness data quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from config import CODE_UNIQUENESS
from dq_utils import append_failure_flag


def apply_uniqueness(df: DataFrame, key_column: str) -> DataFrame:
    """
    Flag all rows participating in duplicate-key groups.

    Does not deduplicate or remove rows.
    """
    window = Window.partitionBy(key_column)
    duplicate_row = F.col(key_column).isNotNull() & (
        F.count(F.lit(1)).over(window) > 1
    )
    return append_failure_flag(df, CODE_UNIQUENESS, duplicate_row)
