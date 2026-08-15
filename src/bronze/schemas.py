"""Explicit PySpark schemas for Bronze CSV ingestion."""

from __future__ import annotations

from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# Business columns are nullable in Bronze to preserve raw source fidelity.

CUSTOMERS_BUSINESS_SCHEMA = StructType(
    [
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("customer_name", StringType(), nullable=True),
        StructField("email", StringType(), nullable=True),
        StructField("country", StringType(), nullable=True),
        StructField("signup_date", DateType(), nullable=True),
        StructField("customer_segment", StringType(), nullable=True),
        StructField("lifetime_value", DecimalType(18, 2), nullable=True),
    ]
)

PRODUCTS_BUSINESS_SCHEMA = StructType(
    [
        StructField("product_id", IntegerType(), nullable=True),
        StructField("product_name", StringType(), nullable=True),
        StructField("category", StringType(), nullable=True),
        StructField("price", DecimalType(18, 2), nullable=True),
        StructField("cost", DecimalType(18, 2), nullable=True),
        StructField("stock_quantity", IntegerType(), nullable=True),
        StructField("reorder_level", IntegerType(), nullable=True),
    ]
)

ORDERS_BUSINESS_SCHEMA = StructType(
    [
        StructField("order_id", IntegerType(), nullable=True),
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("order_date", DateType(), nullable=True),
        StructField("product_id", IntegerType(), nullable=True),
        StructField("quantity", IntegerType(), nullable=True),
        StructField("unit_price", DecimalType(18, 2), nullable=True),
        StructField("total_amount", DecimalType(18, 2), nullable=True),
        StructField("order_status", StringType(), nullable=True),
        StructField("payment_date", DateType(), nullable=True),
    ]
)

METADATA_SCHEMA = StructType(
    [
        StructField("_ingest_timestamp", TimestampType(), nullable=False),
        StructField("_source_file", StringType(), nullable=False),
        StructField("_ingest_batch_id", StringType(), nullable=False),
    ]
)

AUDIT_LOG_SCHEMA = StructType(
    [
        StructField("run_id", StringType(), nullable=False),
        StructField("layer", StringType(), nullable=False),
        StructField("entity", StringType(), nullable=False),
        StructField("status", StringType(), nullable=False),
        StructField("row_count", LongType(), nullable=True),
        StructField("source_path", StringType(), nullable=True),
        StructField("target_table", StringType(), nullable=False),
        StructField("message", StringType(), nullable=True),
        StructField("run_timestamp", TimestampType(), nullable=False),
    ]
)

ENTITY_BUSINESS_SCHEMAS: dict[str, StructType] = {
    "customers": CUSTOMERS_BUSINESS_SCHEMA,
    "products": PRODUCTS_BUSINESS_SCHEMA,
    "orders": ORDERS_BUSINESS_SCHEMA,
}


def expected_business_columns(entity: str) -> list[str]:
    """Return ordered business column names for an entity."""
    schema = ENTITY_BUSINESS_SCHEMAS[entity]
    return [field.name for field in schema.fields]


def bronze_read_schema(entity: str) -> StructType:
    """Return the schema used when reading CSV (business columns only)."""
    return ENTITY_BUSINESS_SCHEMAS[entity]
