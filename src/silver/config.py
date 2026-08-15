"""Centralized configuration for Silver data quality processing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

# ---------------------------------------------------------------------------
# Schema and table names
# ---------------------------------------------------------------------------

BRONZE_SCHEMA: Final[str] = "bronze"
SILVER_SCHEMA: Final[str] = "silver"

BRONZE_TABLE_CUSTOMERS: Final[str] = "customers"
BRONZE_TABLE_PRODUCTS: Final[str] = "products"
BRONZE_TABLE_ORDERS: Final[str] = "orders"

SILVER_TABLE_CUSTOMERS: Final[str] = "customers"
SILVER_TABLE_PRODUCTS: Final[str] = "products"
SILVER_TABLE_ORDERS: Final[str] = "orders"
SILVER_TABLE_DQ_METRICS: Final[str] = "dq_metrics"

# ---------------------------------------------------------------------------
# Row counts (must match Bronze)
# ---------------------------------------------------------------------------

EXPECTED_ROW_COUNTS: Final[dict[str, int]] = {
    "customers": 10_000,
    "products": 500,
    "orders": 100_000,
}

# ---------------------------------------------------------------------------
# Type validation reference date (SD-06)
# ---------------------------------------------------------------------------

REFERENCE_DATE: Final[date] = date(2026, 8, 15)

# ---------------------------------------------------------------------------
# DQ failure codes (canonical order SD-09)
# ---------------------------------------------------------------------------

CODE_COMPLETENESS: Final[str] = "COMPLETENESS"
CODE_UNIQUENESS: Final[str] = "UNIQUENESS"
CODE_TYPE_VALIDATION: Final[str] = "TYPE_VALIDATION"
CODE_REFERENTIAL_INTEGRITY: Final[str] = "REFERENTIAL_INTEGRITY"
CODE_BUSINESS_LOGIC: Final[str] = "BUSINESS_LOGIC"

CANONICAL_FAILURE_CODES: Final[tuple[str, ...]] = (
    CODE_COMPLETENESS,
    CODE_UNIQUENESS,
    CODE_TYPE_VALIDATION,
    CODE_REFERENTIAL_INTEGRITY,
    CODE_BUSINESS_LOGIC,
)

FAILURE_FLAG_COLUMNS: Final[dict[str, str]] = {
    CODE_COMPLETENESS: "_fc_completeness",
    CODE_UNIQUENESS: "_fc_uniqueness",
    CODE_TYPE_VALIDATION: "_fc_type_validation",
    CODE_REFERENTIAL_INTEGRITY: "_fc_referential_integrity",
    CODE_BUSINESS_LOGIC: "_fc_business_logic",
}

QUALITY_PASS: Final[str] = "PASS"

# ---------------------------------------------------------------------------
# Business rule constants
# ---------------------------------------------------------------------------

AMOUNT_TOLERANCE: Final[float] = 0.01

CUSTOMER_SEGMENTS: Final[tuple[str, ...]] = ("Premium", "Standard", "Basic")
ORDER_STATUSES: Final[tuple[str, ...]] = ("Pending", "Completed", "Cancelled")

# ---------------------------------------------------------------------------
# Bronze column expectations
# ---------------------------------------------------------------------------

BRONZE_METADATA_COLUMNS: Final[tuple[str, ...]] = (
    "_ingest_timestamp",
    "_source_file",
    "_ingest_batch_id",
)

CUSTOMERS_COLUMNS: Final[tuple[str, ...]] = (
    "customer_id",
    "customer_name",
    "email",
    "country",
    "signup_date",
    "customer_segment",
    "lifetime_value",
) + BRONZE_METADATA_COLUMNS

PRODUCTS_COLUMNS: Final[tuple[str, ...]] = (
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
) + BRONZE_METADATA_COLUMNS

ORDERS_COLUMNS: Final[tuple[str, ...]] = (
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_status",
    "payment_date",
) + BRONZE_METADATA_COLUMNS

ENTITY_BRONZE_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "customers": CUSTOMERS_COLUMNS,
    "products": PRODUCTS_COLUMNS,
    "orders": ORDERS_COLUMNS,
}


def bronze_table_name(entity: str) -> str:
    """Return fully qualified Bronze table name."""
    table = {
        "customers": BRONZE_TABLE_CUSTOMERS,
        "products": BRONZE_TABLE_PRODUCTS,
        "orders": BRONZE_TABLE_ORDERS,
    }[entity]
    return f"{BRONZE_SCHEMA}.{table}"


def silver_table_name(entity: str) -> str:
    """Return fully qualified Silver entity table name."""
    table = {
        "customers": SILVER_TABLE_CUSTOMERS,
        "products": SILVER_TABLE_PRODUCTS,
        "orders": SILVER_TABLE_ORDERS,
    }[entity]
    return f"{SILVER_SCHEMA}.{table}"


def dq_metrics_table_name() -> str:
    """Return fully qualified Silver DQ metrics table name."""
    return f"{SILVER_SCHEMA}.{SILVER_TABLE_DQ_METRICS}"


@dataclass(frozen=True)
class MetricCheckConfig:
    """Configuration for one silver.dq_metrics row."""

    entity: str
    check_name: str
    failure_code: str
    threshold_pct: float
    require_exact_threshold: bool


METRIC_CHECK_CONFIGS: Final[tuple[MetricCheckConfig, ...]] = (
    MetricCheckConfig("customers", "COMPLETENESS_CUSTOMERS", CODE_COMPLETENESS, 99.0, False),
    MetricCheckConfig("customers", "UNIQUENESS_CUSTOMERS", CODE_UNIQUENESS, 100.0, True),
    MetricCheckConfig("customers", "TYPE_VALIDATION_CUSTOMERS", CODE_TYPE_VALIDATION, 99.0, False),
    MetricCheckConfig("products", "TYPE_VALIDATION_PRODUCTS", CODE_TYPE_VALIDATION, 99.0, False),
    MetricCheckConfig("products", "BUSINESS_LOGIC_PRODUCTS", CODE_BUSINESS_LOGIC, 99.0, False),
    MetricCheckConfig("orders", "COMPLETENESS_ORDERS", CODE_COMPLETENESS, 99.0, False),
    MetricCheckConfig("orders", "UNIQUENESS_ORDERS", CODE_UNIQUENESS, 100.0, True),
    MetricCheckConfig("orders", "TYPE_VALIDATION_ORDERS", CODE_TYPE_VALIDATION, 99.0, False),
    MetricCheckConfig("orders", "REFERENTIAL_INTEGRITY_ORDERS", CODE_REFERENTIAL_INTEGRITY, 99.9, False),
    MetricCheckConfig("orders", "BUSINESS_LOGIC_ORDERS", CODE_BUSINESS_LOGIC, 99.0, False),
)
