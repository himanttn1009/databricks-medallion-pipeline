"""Centralized configuration for Gold layer processing."""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Schema and table names
# ---------------------------------------------------------------------------

SILVER_SCHEMA: Final[str] = "silver"
GOLD_SCHEMA: Final[str] = "gold"

SILVER_TABLE_CUSTOMERS: Final[str] = "customers"
SILVER_TABLE_PRODUCTS: Final[str] = "products"
SILVER_TABLE_ORDERS: Final[str] = "orders"

GOLD_TABLE_SALES_BY_PRODUCT: Final[str] = "sales_by_product"
GOLD_TABLE_REVENUE_BY_CUSTOMER: Final[str] = "revenue_by_customer"
GOLD_TABLE_CUSTOMER_SEGMENTATION: Final[str] = "customer_segmentation"
GOLD_TABLE_DAILY_WEEKLY_TRENDS: Final[str] = "daily_weekly_trends"

# ---------------------------------------------------------------------------
# Silver row counts (validated prerequisites)
# ---------------------------------------------------------------------------

EXPECTED_SILVER_ROW_COUNTS: Final[dict[str, int]] = {
    "customers": 10_000,
    "products": 500,
    "orders": 100_000,
}

# ---------------------------------------------------------------------------
# Business constants
# ---------------------------------------------------------------------------

COMPLETED_STATUS: Final[str] = "Completed"

SEGMENT_INACTIVE: Final[str] = "Inactive"
SEGMENT_ONE_TIME: Final[str] = "One-Time"
SEGMENT_REPEAT: Final[str] = "Repeat"
SEGMENT_HIGH_VALUE: Final[str] = "High-Value"

SEGMENT_TYPES: Final[tuple[str, ...]] = (
    SEGMENT_HIGH_VALUE,
    SEGMENT_REPEAT,
    SEGMENT_ONE_TIME,
    SEGMENT_INACTIVE,
)

PERIOD_DAILY: Final[str] = "DAILY"
PERIOD_WEEKLY: Final[str] = "WEEKLY"

P75_PERCENTILE: Final[float] = 0.75

# ---------------------------------------------------------------------------
# Required Silver columns (minimal for Gold)
# ---------------------------------------------------------------------------

SILVER_CUSTOMERS_COLUMNS: Final[tuple[str, ...]] = (
    "customer_id",
    "customer_name",
    "customer_segment",
    "is_valid",
)

SILVER_PRODUCTS_COLUMNS: Final[tuple[str, ...]] = (
    "product_id",
    "product_name",
    "category",
    "is_valid",
)

SILVER_ORDERS_COLUMNS: Final[tuple[str, ...]] = (
    "order_id",
    "customer_id",
    "product_id",
    "order_date",
    "total_amount",
    "order_status",
    "is_valid",
)

ENTITY_SILVER_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "customers": SILVER_CUSTOMERS_COLUMNS,
    "products": SILVER_PRODUCTS_COLUMNS,
    "orders": SILVER_ORDERS_COLUMNS,
}

# ---------------------------------------------------------------------------
# Gold output schemas (column names for validation)
# ---------------------------------------------------------------------------

SALES_BY_PRODUCT_COLUMNS: Final[tuple[str, ...]] = (
    "product_id",
    "product_name",
    "category",
    "total_orders",
    "total_revenue",
    "avg_order_value",
)

REVENUE_BY_CUSTOMER_COLUMNS: Final[tuple[str, ...]] = (
    "customer_id",
    "customer_name",
    "customer_segment",
    "total_orders",
    "total_revenue",
    "avg_order_value",
    "lifetime_value_actual",
)

CUSTOMER_SEGMENTATION_COLUMNS: Final[tuple[str, ...]] = (
    "segment_type",
    "customer_count",
    "avg_revenue",
    "total_revenue",
)

DAILY_WEEKLY_TRENDS_COLUMNS: Final[tuple[str, ...]] = (
    "order_date",
    "period_type",
    "period_start",
    "total_orders",
    "total_revenue",
)

GOLD_TABLE_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    GOLD_TABLE_SALES_BY_PRODUCT: SALES_BY_PRODUCT_COLUMNS,
    GOLD_TABLE_REVENUE_BY_CUSTOMER: REVENUE_BY_CUSTOMER_COLUMNS,
    GOLD_TABLE_CUSTOMER_SEGMENTATION: CUSTOMER_SEGMENTATION_COLUMNS,
    GOLD_TABLE_DAILY_WEEKLY_TRENDS: DAILY_WEEKLY_TRENDS_COLUMNS,
}


def silver_table_name(entity: str) -> str:
    """Return fully qualified Silver table name."""
    table = {
        "customers": SILVER_TABLE_CUSTOMERS,
        "products": SILVER_TABLE_PRODUCTS,
        "orders": SILVER_TABLE_ORDERS,
    }[entity]
    return f"{SILVER_SCHEMA}.{table}"


def gold_table_name(table: str) -> str:
    """Return fully qualified Gold table name."""
    return f"{GOLD_SCHEMA}.{table}"
