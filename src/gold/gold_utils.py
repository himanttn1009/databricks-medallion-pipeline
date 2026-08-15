"""Shared Gold layer utilities."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from config import (
    COMPLETED_STATUS,
    ENTITY_SILVER_COLUMNS,
    EXPECTED_SILVER_ROW_COUNTS,
    GOLD_SCHEMA,
    GOLD_TABLE_COLUMNS,
    SEGMENT_TYPES,
    gold_table_name,
    silver_table_name,
)


class GoldProcessingError(Exception):
    """Raised when Gold processing fails for a fatal validation or I/O error."""


def ensure_gold_schema_exists(spark: SparkSession) -> None:
    """Create the Gold schema if it does not already exist."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")


def validate_silver_prerequisites(spark: SparkSession) -> None:
    """Validate Silver tables exist with expected row counts and required columns."""
    for entity in EXPECTED_SILVER_ROW_COUNTS:
        load_silver_entity(spark, entity, validate_only=True)


def load_silver_entity(
    spark: SparkSession,
    entity: str,
    *,
    validate_only: bool = False,
) -> DataFrame:
    """
    Load a Silver entity table after validation.

    Raises GoldProcessingError on missing table, row-count mismatch, or schema issues.
    """
    source_table = silver_table_name(entity)
    expected_count = EXPECTED_SILVER_ROW_COUNTS[entity]
    required_columns = ENTITY_SILVER_COLUMNS[entity]

    try:
        df = spark.table(source_table)
    except Exception as exc:
        raise GoldProcessingError(
            f"Silver table missing or unreadable for entity '{entity}' "
            f"(source_table='{source_table}'): {exc}"
        ) from exc

    actual_count = df.count()
    if actual_count != expected_count:
        raise GoldProcessingError(
            f"Silver row-count mismatch for entity '{entity}': "
            f"expected {expected_count}, got {actual_count}. "
            f"source_table='{source_table}'."
        )

    actual_columns = set(df.columns)
    missing = [col for col in required_columns if col not in actual_columns]
    if missing:
        raise GoldProcessingError(
            f"Silver schema failure for entity '{entity}' "
            f"(source_table='{source_table}'): missing columns {missing}."
        )

    if validate_only:
        return df.limit(0)

    return df


def load_valid_customers(customers_df: DataFrame) -> DataFrame:
    """Return valid Silver customers with dimension columns."""
    return customers_df.filter(F.col("is_valid")).select(
        "customer_id",
        "customer_name",
        "customer_segment",
    )


def load_valid_products(products_df: DataFrame) -> DataFrame:
    """Return valid Silver products with dimension columns."""
    return products_df.filter(F.col("is_valid")).select(
        "product_id",
        "product_name",
        "category",
    )


def load_qualifying_orders(orders_df: DataFrame) -> DataFrame:
    """Return qualifying completed valid orders for Gold analytics."""
    return orders_df.filter(
        F.col("is_valid") & (F.col("order_status") == F.lit(COMPLETED_STATUS))
    ).select(
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "total_amount",
    )


def to_decimal_2(column: F.Column) -> F.Column:
    """Cast and round a numeric column to DECIMAL(18,2)."""
    return F.round(column.cast("decimal(18,2)"), 2).cast("decimal(18,2)")


def write_gold_table(df: DataFrame, table: str) -> None:
    """Overwrite a Gold Delta table."""
    target_table = gold_table_name(table)
    try:
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target_table)
        )
    except Exception as exc:
        raise GoldProcessingError(
            f"Delta write failed for Gold table '{table}' "
            f"(target_table='{target_table}'): {exc}"
        ) from exc


def _validate_columns(df: DataFrame, table: str) -> None:
    """Ensure DataFrame has expected output columns."""
    expected = GOLD_TABLE_COLUMNS[table]
    actual = set(df.columns)
    missing = [col for col in expected if col not in actual]
    if missing:
        raise GoldProcessingError(
            f"Gold schema failure for table '{table}': missing columns {missing}."
        )


def _validate_no_duplicate_keys(df: DataFrame, table: str, key_column: str) -> None:
    """Ensure grain key has no duplicates."""
    duplicate_count = (
        df.groupBy(key_column).count().filter(F.col("count") > 1).count()
    )
    if duplicate_count > 0:
        raise GoldProcessingError(
            f"Gold grain violation for table '{table}': "
            f"duplicate values in '{key_column}'."
        )


def validate_gold_dataframe(df: DataFrame, table: str) -> None:
    """Validate a Gold DataFrame before or after write."""
    _validate_columns(df, table)

    if table == "sales_by_product":
        _validate_no_duplicate_keys(df, table, "product_id")
    elif table == "revenue_by_customer":
        _validate_no_duplicate_keys(df, table, "customer_id")
    elif table == "customer_segmentation":
        _validate_no_duplicate_keys(df, table, "segment_type")
        invalid_segments = df.filter(~F.col("segment_type").isin(*SEGMENT_TYPES)).count()
        if invalid_segments > 0:
            raise GoldProcessingError(
                f"Gold segmentation failure: invalid segment_type values in '{table}'."
            )
    elif table == "daily_weekly_trends":
        dup_periods = (
            df.groupBy("period_type", "period_start")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )
        if dup_periods > 0:
            raise GoldProcessingError(
                f"Gold grain violation for table '{table}': "
                "duplicate (period_type, period_start) combinations."
            )


def validate_gold_outputs(spark: SparkSession) -> dict[str, int]:
    """
    Validate all four Gold tables exist with expected schemas and grain.

    Returns row counts per table.
    """
    counts: dict[str, int] = {}
    for table in GOLD_TABLE_COLUMNS:
        target = gold_table_name(table)
        try:
            df = spark.table(target)
        except Exception as exc:
            raise GoldProcessingError(
                f"Gold table missing or unreadable (target_table='{target}'): {exc}"
            ) from exc
        validate_gold_dataframe(df, table)
        counts[table] = df.count()
    return counts
