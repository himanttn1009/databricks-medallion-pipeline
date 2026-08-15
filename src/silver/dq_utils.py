"""Shared Silver data quality utilities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from config import (
    CANONICAL_FAILURE_CODES,
    ENTITY_BRONZE_COLUMNS,
    EXPECTED_ROW_COUNTS,
    FAILURE_FLAG_COLUMNS,
    METRIC_CHECK_CONFIGS,
    MetricCheckConfig,
    QUALITY_PASS,
    bronze_table_name,
    dq_metrics_table_name,
    silver_table_name,
)
from schemas import DQ_METRICS_SCHEMA


class SilverProcessingError(Exception):
    """Raised when Silver processing fails for a fatal validation or I/O error."""


@dataclass(frozen=True)
class MetricRow:
    """One row destined for silver.dq_metrics."""

    run_id: str
    check_name: str
    entity: str
    total_rows: int
    passed_rows: int
    failed_rows: int
    pass_pct: Decimal
    threshold_pct: Decimal
    threshold_met: bool
    run_timestamp: datetime


def generate_run_id() -> str:
    """Generate a unique Silver pipeline run identifier."""
    return str(uuid.uuid4())


def ensure_silver_schema_exists(spark: SparkSession) -> None:
    """Create the Silver schema if it does not already exist."""
    from config import SILVER_SCHEMA

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")


def validate_bronze_prerequisites(spark: SparkSession) -> None:
    """Validate that all Bronze tables exist with expected row counts and columns."""
    for entity in EXPECTED_ROW_COUNTS:
        load_bronze_entity(spark, entity, validate_only=True)


def load_bronze_entity(
    spark: SparkSession,
    entity: str,
    *,
    validate_only: bool = False,
) -> DataFrame:
    """
    Load a Bronze entity table after validation.

    Raises SilverProcessingError on missing table, row-count mismatch, or schema issues.
    """
    source_table = bronze_table_name(entity)
    expected_count = EXPECTED_ROW_COUNTS[entity]
    required_columns = ENTITY_BRONZE_COLUMNS[entity]

    try:
        df = spark.table(source_table)
    except Exception as exc:
        raise SilverProcessingError(
            f"Bronze table missing or unreadable for entity '{entity}' "
            f"(source_table='{source_table}'): {exc}"
        ) from exc

    actual_count = df.count()
    if actual_count != expected_count:
        raise SilverProcessingError(
            f"Bronze row-count mismatch for entity '{entity}': "
            f"expected {expected_count}, got {actual_count}. "
            f"source_table='{source_table}'."
        )

    actual_columns = set(df.columns)
    missing = [col for col in required_columns if col not in actual_columns]
    if missing:
        raise SilverProcessingError(
            f"Bronze schema failure for entity '{entity}' "
            f"(source_table='{source_table}'): missing columns {missing}."
        )

    if validate_only:
        return df.limit(0)

    return df


def append_failure_flag(
    df: DataFrame,
    failure_code: str,
    condition: F.Column,
) -> DataFrame:
    """Record a row-level failure for the given DQ code (OR with any prior flag)."""
    flag_col = FAILURE_FLAG_COLUMNS[failure_code]
    if flag_col in df.columns:
        return df.withColumn(flag_col, F.col(flag_col) | condition)
    return df.withColumn(flag_col, condition)


def finalize_quality_columns(
    df: DataFrame,
    processed_timestamp: datetime,
) -> DataFrame:
    """Build quality_check_result, is_valid, and Silver timestamp; drop internal flags."""
    code_exprs = [
        F.when(F.col(FAILURE_FLAG_COLUMNS[code]), F.lit(code))
        for code in CANONICAL_FAILURE_CODES
        if FAILURE_FLAG_COLUMNS[code] in df.columns
    ]

    if code_exprs:
        failed_codes = F.concat_ws(",", *code_exprs)
        result_col = F.when(failed_codes == F.lit(""), F.lit(QUALITY_PASS)).otherwise(
            failed_codes
        )
    else:
        result_col = F.lit(QUALITY_PASS)

    output = (
        df.withColumn("quality_check_result", result_col)
        .withColumn("is_valid", F.col("quality_check_result") == F.lit(QUALITY_PASS))
        .withColumn("_silver_processed_timestamp", F.lit(processed_timestamp))
    )

    internal_cols = [c for c in output.columns if c.startswith("_fc_")]
    if internal_cols:
        output = output.drop(*internal_cols)

    return output


def compute_entity_metric(
    df: DataFrame,
    config: MetricCheckConfig,
    run_id: str,
    run_timestamp: datetime,
) -> MetricRow:
    """Compute one dq_metrics row from an internal failure-flag column."""
    flag_col = FAILURE_FLAG_COLUMNS[config.failure_code]
    if flag_col not in df.columns:
        raise SilverProcessingError(
            f"Cannot compute metric '{config.check_name}' for entity '{config.entity}': "
            f"missing failure flag column '{flag_col}'."
        )

    total_rows = df.count()
    failed_rows = df.filter(F.col(flag_col)).count()
    passed_rows = total_rows - failed_rows
    pass_pct_value = (
        Decimal("100.00") if total_rows == 0 else Decimal(str(round(100.0 * passed_rows / total_rows, 2)))
    )
    threshold = Decimal(str(config.threshold_pct))

    if config.require_exact_threshold:
        threshold_met = pass_pct_value == threshold
    else:
        threshold_met = pass_pct_value > threshold

    return MetricRow(
        run_id=run_id,
        check_name=config.check_name,
        entity=config.entity,
        total_rows=total_rows,
        passed_rows=passed_rows,
        failed_rows=failed_rows,
        pass_pct=pass_pct_value,
        threshold_pct=threshold,
        threshold_met=threshold_met,
        run_timestamp=run_timestamp,
    )


def compute_metrics_for_entity(
    df: DataFrame,
    entity: str,
    run_id: str,
    run_timestamp: datetime,
) -> list[MetricRow]:
    """Compute all configured dq_metrics rows for one entity DataFrame."""
    configs = [cfg for cfg in METRIC_CHECK_CONFIGS if cfg.entity == entity]
    return [compute_entity_metric(df, cfg, run_id, run_timestamp) for cfg in configs]


def write_silver_table(df: DataFrame, entity: str) -> None:
    """Overwrite a Silver entity Delta table."""
    target_table = silver_table_name(entity)
    try:
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target_table)
        )
    except Exception as exc:
        raise SilverProcessingError(
            f"Delta write failed for entity '{entity}' "
            f"(target_table='{target_table}'): {exc}"
        ) from exc


def write_dq_metrics(spark: SparkSession, metrics: Iterable[MetricRow]) -> None:
    """Append dq_metrics rows to silver.dq_metrics."""
    rows = [
        (
            m.run_id,
            m.check_name,
            m.entity,
            m.total_rows,
            m.passed_rows,
            m.failed_rows,
            m.pass_pct,
            m.threshold_pct,
            m.threshold_met,
            m.run_timestamp,
        )
        for m in metrics
    ]

    if len(rows) != 10:
        raise SilverProcessingError(
            f"Expected exactly 10 dq_metrics rows per run, got {len(rows)}."
        )

    metrics_df = spark.createDataFrame(rows, schema=DQ_METRICS_SCHEMA)
    target_table = dq_metrics_table_name()
    try:
        (
            metrics_df.write.format("delta")
            .mode("append")
            .option("mergeSchema", "true")
            .saveAsTable(target_table)
        )
    except Exception as exc:
        raise SilverProcessingError(
            f"Delta write failed for dq_metrics (target_table='{target_table}'): {exc}"
        ) from exc


def build_customer_signup_lookup(bronze_customers: DataFrame) -> DataFrame:
    """Internal MIN(signup_date) lookup per customer_id for BR-05 (SD-01)."""
    return bronze_customers.groupBy("customer_id").agg(
        F.min("signup_date").alias("_min_signup_date")
    )


def distinct_parent_keys(bronze_df: DataFrame, key_column: str) -> DataFrame:
    """Distinct parent primary keys from Bronze for referential integrity."""
    return bronze_df.select(key_column).distinct()
