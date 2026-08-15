"""Shared Bronze CSV ingestion utilities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType

from config import (
    AUDIT_SCHEMA,
    AUDIT_STATUS_FAILED,
    AUDIT_STATUS_SUCCESS,
    BRONZE_SCHEMA,
    CSV_READER_OPTIONS,
    EntityConfig,
    LAYER_BRONZE,
    audit_table_name,
    get_entity_config,
)
from schemas import (
    AUDIT_LOG_SCHEMA,
    bronze_read_schema,
    expected_business_columns,
)


class BronzeIngestionError(Exception):
    """Raised when Bronze ingestion fails for a recoverable validation or I/O error."""


@dataclass(frozen=True)
class IngestResult:
    """Outcome of a single entity Bronze ingestion."""

    entity: str
    status: str
    row_count: int
    source_path: str
    target_table: str
    batch_id: str
    message: str


def generate_batch_id() -> str:
    """Generate a unique batch identifier for a pipeline run."""
    return str(uuid.uuid4())


def ensure_schemas_exist(spark: SparkSession) -> None:
    """Create Bronze and audit schemas if they do not already exist."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {AUDIT_SCHEMA}")


def _path_exists(spark: SparkSession, path: str) -> bool:
    """Check whether a Hadoop-compatible path exists."""
    jvm = spark._jvm
    hadoop_path = jvm.org.apache.hadoop.fs.Path(path)
    fs = hadoop_path.getFileSystem(spark._jsc.hadoopConfiguration())
    return fs.exists(hadoop_path)


def _validate_source_exists(spark: SparkSession, entity: str, source_path: str) -> None:
    """Fail if the source CSV path does not exist."""
    if not _path_exists(spark, source_path):
        raise BronzeIngestionError(
            f"Source file missing for entity '{entity}' at path '{source_path}'."
        )


def _validate_source_not_empty(spark: SparkSession, entity: str, source_path: str) -> None:
    """Fail if the source file has no data rows (header-only or empty)."""
    line_count = spark.read.text(source_path).count()
    if line_count == 0:
        raise BronzeIngestionError(
            f"Source file is empty for entity '{entity}' at path '{source_path}'."
        )
    if line_count == 1:
        raise BronzeIngestionError(
            f"Source file contains only a header row for entity '{entity}' "
            f"at path '{source_path}'."
        )


def _read_csv_header_columns(spark: SparkSession, source_path: str) -> list[str]:
    """Read CSV header column names without loading data rows."""
    header_df = (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "false")
        .load(source_path)
        .limit(0)
    )
    return list(header_df.columns)


def validate_csv_header(entity: str, actual_columns: list[str], expected_columns: list[str]) -> None:
    """
    Validate CSV header against the expected business schema.

    Detects missing required columns, unexpected extra columns, and incorrect
    column order. Spark CSV reads with an explicit schema map columns by position.
    """
    if actual_columns == expected_columns:
        return

    actual_set = set(actual_columns)
    expected_set = set(expected_columns)

    missing = [col for col in expected_columns if col not in actual_set]
    extra = [col for col in actual_columns if col not in expected_set]

    parts = [f"CSV header mismatch for entity '{entity}'."]
    if missing:
        parts.append(f"Missing columns: {missing}.")
    if extra:
        parts.append(f"Unexpected extra columns: {extra}.")
    if not missing and not extra:
        parts.append("Column order does not match expected schema.")
    parts.append(f"Expected column order: {expected_columns}.")
    parts.append(f"Actual column order: {actual_columns}.")
    raise BronzeIngestionError(" ".join(parts))


def read_csv_with_schema(
    spark: SparkSession,
    source_path: str,
    schema: StructType,
) -> DataFrame:
    """
    Read a CSV file using explicit schema and strict parsing options.

    Empty fields are interpreted as NULL. Malformed records fail fast.
    """
    reader = spark.read.format("csv")
    for key, value in CSV_READER_OPTIONS.items():
        reader = reader.option(key, value)
    return reader.schema(schema).load(source_path)


def add_metadata_columns(
    df: DataFrame,
    source_path: str,
    batch_id: str,
    ingest_timestamp: datetime,
) -> DataFrame:
    """Append Bronze ingestion metadata columns without altering business values."""
    return (
        df.withColumn("_ingest_timestamp", lit(ingest_timestamp))
        .withColumn("_source_file", lit(source_path))
        .withColumn("_ingest_batch_id", lit(batch_id))
    )


def validate_row_count(
    entity: str,
    actual_count: int,
    expected_count: int,
    source_path: str,
    target_table: str,
) -> None:
    """Fail if the ingested row count does not match the expected count."""
    if actual_count != expected_count:
        raise BronzeIngestionError(
            f"Row-count mismatch for entity '{entity}': "
            f"expected {expected_count}, got {actual_count}. "
            f"source_path='{source_path}', target_table='{target_table}'."
        )


def write_bronze_table(df: DataFrame, target_table: str) -> None:
    """Overwrite the Bronze Delta table for full-refresh idempotency."""
    try:
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target_table)
        )
    except Exception as exc:
        raise BronzeIngestionError(
            f"Delta write failed for target table '{target_table}': {exc}"
        ) from exc


def verify_post_write_row_count(
    spark: SparkSession,
    entity: str,
    target_table: str,
    expected_count: int,
    source_path: str,
) -> int:
    """Lightweight post-write verification of persisted row count."""
    actual_count = spark.table(target_table).count()
    validate_row_count(
        entity=entity,
        actual_count=actual_count,
        expected_count=expected_count,
        source_path=source_path,
        target_table=target_table,
    )
    return actual_count


def write_audit_record(
    spark: SparkSession,
    *,
    run_id: str,
    entity: str,
    status: str,
    row_count: Optional[int],
    source_path: str,
    target_table: str,
    message: str,
    run_timestamp: datetime,
) -> None:
    """Append one ingestion audit record to audit.ingestion_log."""
    audit_df = spark.createDataFrame(
        [
            (
                run_id,
                LAYER_BRONZE,
                entity,
                status,
                row_count,
                source_path,
                target_table,
                message,
                run_timestamp,
            )
        ],
        schema=AUDIT_LOG_SCHEMA,
    )
    (
        audit_df.write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(audit_table_name())
    )


def ingest_entity(
    spark: SparkSession,
    entity: str,
    batch_id: str,
    ingest_timestamp: Optional[datetime] = None,
) -> IngestResult:
    """
    Ingest one entity CSV into its Bronze Delta table.

    Preserves all source defects; performs validation and audit logging.
    """
    config = get_entity_config(entity)
    run_timestamp = ingest_timestamp or datetime.now(timezone.utc)
    expected_columns = expected_business_columns(entity)

    try:
        ensure_schemas_exist(spark)

        _validate_source_exists(spark, entity, config.source_path)
        _validate_source_not_empty(spark, entity, config.source_path)

        actual_header = _read_csv_header_columns(spark, config.source_path)
        validate_csv_header(entity, actual_header, expected_columns)

        business_df = read_csv_with_schema(
            spark,
            config.source_path,
            bronze_read_schema(entity),
        )

        row_count = business_df.count()
        validate_row_count(
            entity=entity,
            actual_count=row_count,
            expected_count=config.expected_row_count,
            source_path=config.source_path,
            target_table=config.target_table,
        )

        bronze_df = add_metadata_columns(
            business_df,
            source_path=config.source_path,
            batch_id=batch_id,
            ingest_timestamp=run_timestamp,
        )

        write_bronze_table(bronze_df, config.target_table)
        verify_post_write_row_count(
            spark,
            entity=entity,
            target_table=config.target_table,
            expected_count=config.expected_row_count,
            source_path=config.source_path,
        )

        message = (
            f"Successfully ingested {row_count} rows into {config.target_table}."
        )
        write_audit_record(
            spark,
            run_id=batch_id,
            entity=entity,
            status=AUDIT_STATUS_SUCCESS,
            row_count=row_count,
            source_path=config.source_path,
            target_table=config.target_table,
            message=message,
            run_timestamp=run_timestamp,
        )

        return IngestResult(
            entity=entity,
            status=AUDIT_STATUS_SUCCESS,
            row_count=row_count,
            source_path=config.source_path,
            target_table=config.target_table,
            batch_id=batch_id,
            message=message,
        )

    except BronzeIngestionError as exc:
        write_audit_record(
            spark,
            run_id=batch_id,
            entity=entity,
            status=AUDIT_STATUS_FAILED,
            row_count=None,
            source_path=config.source_path,
            target_table=config.target_table,
            message=str(exc),
            run_timestamp=run_timestamp,
        )
        raise

    except Exception as exc:
        safe_message = (
            f"Ingestion failed for entity '{entity}' "
            f"(source_path='{config.source_path}', "
            f"target_table='{config.target_table}'): {exc}"
        )
        write_audit_record(
            spark,
            run_id=batch_id,
            entity=entity,
            status=AUDIT_STATUS_FAILED,
            row_count=None,
            source_path=config.source_path,
            target_table=config.target_table,
            message=safe_message,
            run_timestamp=run_timestamp,
        )
        raise BronzeIngestionError(safe_message) from exc
