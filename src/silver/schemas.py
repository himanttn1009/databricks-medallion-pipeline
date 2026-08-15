"""Spark schemas for Silver outputs."""

from __future__ import annotations

from pyspark.sql.types import (
    BooleanType,
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

DQ_METRICS_SCHEMA = StructType(
    [
        StructField("run_id", StringType(), nullable=False),
        StructField("check_name", StringType(), nullable=False),
        StructField("entity", StringType(), nullable=False),
        StructField("total_rows", LongType(), nullable=False),
        StructField("passed_rows", LongType(), nullable=False),
        StructField("failed_rows", LongType(), nullable=False),
        StructField("pass_pct", DecimalType(5, 2), nullable=False),
        StructField("threshold_pct", DecimalType(5, 2), nullable=False),
        StructField("threshold_met", BooleanType(), nullable=False),
        StructField("run_timestamp", TimestampType(), nullable=False),
    ]
)
