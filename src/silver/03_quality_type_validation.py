"""Type validation data quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import (
    CODE_TYPE_VALIDATION,
    CUSTOMER_SEGMENTS,
    ORDER_STATUSES,
    REFERENCE_DATE,
)
from dq_utils import append_failure_flag


def _invalid_enum(column: F.Column, allowed: tuple[str, ...]) -> F.Column:
    """True when value is non-null and not in the allowed enumeration."""
    return column.isNotNull() & ~column.isin(*allowed)


def _future_date(column: F.Column) -> F.Column:
    """True when date is after the fixed project REFERENCE_DATE."""
    return column.isNotNull() & (column > F.lit(REFERENCE_DATE))


def _negative(column: F.Column) -> F.Column:
    """True when numeric value is strictly negative."""
    return column.isNotNull() & (column < F.lit(0))


def apply_type_validation_customers(df: DataFrame) -> DataFrame:
    """Apply type validation rules to customers."""
    failures = (
        _invalid_enum(F.col("customer_segment"), CUSTOMER_SEGMENTS)
        | _future_date(F.col("signup_date"))
        | _negative(F.col("lifetime_value"))
    )
    return append_failure_flag(df, CODE_TYPE_VALIDATION, failures)


def apply_type_validation_products(df: DataFrame) -> DataFrame:
    """Apply type validation rules to products."""
    failures = (
        _negative(F.col("price"))
        | _negative(F.col("cost"))
        | _negative(F.col("stock_quantity"))
        | _negative(F.col("reorder_level"))
    )
    return append_failure_flag(df, CODE_TYPE_VALIDATION, failures)


def apply_type_validation_orders(df: DataFrame) -> DataFrame:
    """Apply type validation rules to orders."""
    failures = (
        _invalid_enum(F.col("order_status"), ORDER_STATUSES)
        | _future_date(F.col("order_date"))
        | _future_date(F.col("payment_date"))
        | _negative(F.col("quantity"))
        | _negative(F.col("unit_price"))
        | _negative(F.col("total_amount"))
    )
    return append_failure_flag(df, CODE_TYPE_VALIDATION, failures)
