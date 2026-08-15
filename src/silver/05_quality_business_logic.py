"""Business-rule data quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import AMOUNT_TOLERANCE, CODE_BUSINESS_LOGIC
from dq_utils import append_failure_flag


def apply_business_logic_products(df: DataFrame) -> DataFrame:
    """BR-01: product price must be greater than cost."""
    condition = F.col("price").isNotNull() & F.col("cost").isNotNull() & (
        F.col("price") <= F.col("cost")
    )
    return append_failure_flag(df, CODE_BUSINESS_LOGIC, condition)


def apply_business_logic_orders(
    orders_df: DataFrame,
    customer_signup_lookup: DataFrame,
) -> DataFrame:
    """
    Apply order business rules BR-02 through BR-05.

    BR-05 uses MIN(signup_date) lookup (SD-01) and skips NULL/orphan customers.
    """
    joined = orders_df.join(customer_signup_lookup, on="customer_id", how="left")

    amount_mismatch = F.abs(
        F.col("total_amount").cast("double")
        - (F.col("quantity") * F.col("unit_price").cast("double"))
    ) > F.lit(AMOUNT_TOLERANCE)

    completed_missing_payment = (F.col("order_status") == F.lit("Completed")) & F.col(
        "payment_date"
    ).isNull()

    pending_cancelled_with_payment = F.col("order_status").isin(
        "Pending", "Cancelled"
    ) & F.col("payment_date").isNotNull()

    order_before_signup = (
        F.col("customer_id").isNotNull()
        & F.col("_min_signup_date").isNotNull()
        & F.col("order_date").isNotNull()
        & (F.col("order_date") < F.col("_min_signup_date"))
    )

    failures = (
        amount_mismatch
        | completed_missing_payment
        | pending_cancelled_with_payment
        | order_before_signup
    )

    flagged = append_failure_flag(joined, CODE_BUSINESS_LOGIC, failures)
    return flagged.drop("_min_signup_date")
