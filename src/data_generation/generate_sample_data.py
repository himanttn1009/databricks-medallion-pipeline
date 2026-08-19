#!/usr/bin/env python3
"""
Generate synthetic e-commerce CSV datasets for the Databricks Medallion pipeline.

NULL handling: Python None internally; written as empty CSV fields (see write_csv).
Design specification: src/data_generation/DATA_GENERATION_NOTES.md
"""

from __future__ import annotations

import argparse
import csv
import errno
import random
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from faker import Faker

# ---------------------------------------------------------------------------
# Configuration / constants
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
FAKER_LOCALE = "en_US"
# Fixed reference date for fully reproducible date generation across runs.
REFERENCE_DATE = date(2026, 8, 15)

CUSTOMER_ROW_COUNT = 10_000
PRODUCT_ROW_COUNT = 500
ORDER_ROW_COUNT = 100_000

NULL_EMAIL_COUNT = 50
DUPLICATE_CUSTOMER_ID_ROWS = 10
DUPLICATE_CUSTOMER_ID_PAIRS = DUPLICATE_CUSTOMER_ID_ROWS // 2

NULL_ORDER_CUSTOMER_ID = 100
NULL_ORDER_PRODUCT_ID = 200
ORPHAN_CUSTOMER_ID_COUNT = 50
ORPHAN_PRODUCT_ID_COUNT = 30
DUPLICATE_ORDER_ID_ROWS = 20
DUPLICATE_ORDER_ID_PAIRS = DUPLICATE_ORDER_ID_ROWS // 2

TOTAL_EXPLICIT_DEFECT_ROWS = (
    NULL_EMAIL_COUNT
    + DUPLICATE_CUSTOMER_ID_ROWS
    + NULL_ORDER_CUSTOMER_ID
    + NULL_ORDER_PRODUCT_ID
    + ORPHAN_CUSTOMER_ID_COUNT
    + ORPHAN_PRODUCT_ID_COUNT
    + DUPLICATE_ORDER_ID_ROWS
)

GHOST_CUSTOMER_ID_START = 90_001
GHOST_CUSTOMER_ID_END = 90_050
GHOST_PRODUCT_ID_START = 901
GHOST_PRODUCT_ID_END = 930

SIGNUP_DATE_START = date(2020, 1, 1)

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
CUSTOMER_SEGMENT_WEIGHTS = (0.20, 0.50, 0.30)

ORDER_STATUSES = ("Completed", "Pending", "Cancelled")
ORDER_STATUS_WEIGHTS = (0.70, 0.20, 0.10)

COUNTRIES = (
    "United States",
    "United Kingdom",
    "Canada",
    "Germany",
    "France",
    "Australia",
    "India",
    "Japan",
    "Brazil",
    "Netherlands",
)

PRODUCT_CATEGORIES = (
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Beauty",
    "Toys",
    "Automotive",
    "Health",
    "Office",
    "Grocery",
)

CUSTOMER_COLUMNS = (
    "customer_id",
    "customer_name",
    "email",
    "country",
    "signup_date",
    "customer_segment",
    "lifetime_value",
)

PRODUCT_COLUMNS = (
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
)

ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_status",
    "payment_date",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"

# ---------------------------------------------------------------------------
# Defect pool containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CustomerDefectPools:
    null_email: set[int]
    duplicate_customer_id: set[int]


@dataclass(frozen=True)
class OrderDefectPools:
    null_customer_id: set[int]
    null_product_id: set[int]
    orphan_customer_id: set[int]
    orphan_product_id: set[int]
    duplicate_order_id: set[int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def random_date_between(rng: random.Random, start: date, end: date) -> date:
    if start > end:
        start, end = end, start
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))


def allocate_disjoint_pools(
    row_count: int,
    pool_sizes: list[int],
    rng: random.Random,
) -> list[set[int]]:
    indices = list(range(row_count))
    rng.shuffle(indices)
    offset = 0
    pools: list[set[int]] = []
    for size in pool_sizes:
        pool = set(indices[offset : offset + size])
        pools.append(pool)
        offset += size
    return pools


def verify_disjoint(pools: list[set[int]], labels: list[str]) -> None:
    for i in range(len(pools)):
        for j in range(i + 1, len(pools)):
            overlap = pools[i] & pools[j]
            if overlap:
                raise ValueError(
                    f"Defect pools overlap ({labels[i]} & {labels[j]}): {sorted(overlap)[:5]}..."
                )


def count_duplicate_participants(rows: list[dict[str, Any]], key: str) -> int:
    values = [row[key] for row in rows if row[key] is not None]
    freq = Counter(values)
    duplicate_values = {value for value, n in freq.items() if n > 1}
    return sum(1 for row in rows if row[key] in duplicate_values)


def validate_duplicate_pair_structure(
    rows: list[dict[str, Any]],
    key: str,
    expected_participant_rows: int,
    expected_pairs: int,
    label: str,
) -> list[str]:
    """Ensure duplicate keys form exactly N pairs of frequency 2."""
    errors: list[str] = []
    values = [row[key] for row in rows if row[key] is not None]
    freq = Counter(values)
    duplicate_freq = {value: count for value, count in freq.items() if count > 1}

    if len(duplicate_freq) != expected_pairs:
        errors.append(
            f"{label}: expected {expected_pairs} duplicate {key} values, "
            f"got {len(duplicate_freq)}"
        )

    invalid_counts = {value: count for value, count in duplicate_freq.items() if count != 2}
    if invalid_counts:
        sample = list(invalid_counts.items())[:3]
        errors.append(
            f"{label}: duplicate {key} values must appear exactly twice; "
            f"invalid frequencies: {sample}"
        )

    participant_rows = sum(duplicate_freq.values())
    if participant_rows != expected_participant_rows:
        errors.append(
            f"{label}: expected {expected_participant_rows} participant rows, "
            f"got {participant_rows}"
        )

    return errors


def count_null(rows: list[dict[str, Any]], column: str) -> int:
    return sum(1 for row in rows if row[column] is None)


def count_orphan_fk(
    rows: list[dict[str, Any]],
    fk_column: str,
    valid_ids: set[int],
) -> int:
    return sum(
        1
        for row in rows
        if row[fk_column] is not None and row[fk_column] not in valid_ids
    )


def inject_duplicate_primary_keys(
    rows: list[dict[str, Any]],
    duplicate_indices: set[int],
    key: str,
    expected_pairs: int,
) -> None:
    ordered = sorted(duplicate_indices)
    if len(ordered) != expected_pairs * 2:
        raise ValueError(
            f"duplicate index pool for {key} must contain {expected_pairs * 2} rows, "
            f"got {len(ordered)}"
        )
    for pair_index in range(expected_pairs):
        first_idx = ordered[pair_index * 2]
        second_idx = ordered[pair_index * 2 + 1]
        rows[second_idx][key] = rows[first_idx][key]


# ---------------------------------------------------------------------------
# Defect pool reservation
# ---------------------------------------------------------------------------


def reserve_customer_defect_pools(rng: random.Random) -> CustomerDefectPools:
    pools = allocate_disjoint_pools(
        CUSTOMER_ROW_COUNT,
        [NULL_EMAIL_COUNT, DUPLICATE_CUSTOMER_ID_ROWS],
        rng,
    )
    verify_disjoint(pools, ["null_email", "duplicate_customer_id"])
    return CustomerDefectPools(
        null_email=pools[0],
        duplicate_customer_id=pools[1],
    )


def reserve_order_defect_pools(rng: random.Random) -> OrderDefectPools:
    pools = allocate_disjoint_pools(
        ORDER_ROW_COUNT,
        [
            NULL_ORDER_CUSTOMER_ID,
            NULL_ORDER_PRODUCT_ID,
            ORPHAN_CUSTOMER_ID_COUNT,
            ORPHAN_PRODUCT_ID_COUNT,
            DUPLICATE_ORDER_ID_ROWS,
        ],
        rng,
    )
    verify_disjoint(
        pools,
        [
            "null_customer_id",
            "null_product_id",
            "orphan_customer_id",
            "orphan_product_id",
            "duplicate_order_id",
        ],
    )
    return OrderDefectPools(
        null_customer_id=pools[0],
        null_product_id=pools[1],
        orphan_customer_id=pools[2],
        orphan_product_id=pools[3],
        duplicate_order_id=pools[4],
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_products(
    rng: random.Random,
    fake: Faker,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for product_id in range(1, PRODUCT_ROW_COUNT + 1):
        category = rng.choice(PRODUCT_CATEGORIES)
        cost = round_money(rng.uniform(5.0, 200.0))
        price = round_money(cost * rng.uniform(1.15, 2.5))
        stock_quantity = rng.randint(0, 500)
        reorder_level = rng.randint(5, max(5, stock_quantity // 4))
        products.append(
            {
                "product_id": product_id,
                "product_name": fake.catch_phrase(),
                "category": category,
                "price": price,
                "cost": cost,
                "stock_quantity": stock_quantity,
                "reorder_level": reorder_level,
            }
        )
    return products


def generate_customers(
    rng: random.Random,
    fake: Faker,
    defect_pools: CustomerDefectPools,
    reference_date: date,
) -> list[dict[str, Any]]:
    customers: list[dict[str, Any]] = []

    for idx in range(CUSTOMER_ROW_COUNT):
        customer_id = idx + 1
        email = None if idx in defect_pools.null_email else fake.email()
        segment = rng.choices(CUSTOMER_SEGMENTS, weights=CUSTOMER_SEGMENT_WEIGHTS, k=1)[0]
        lifetime_value = round_money(rng.lognormvariate(4.0, 0.6))

        customers.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.name(),
                "email": email,
                "country": rng.choice(COUNTRIES),
                "signup_date": random_date_between(rng, SIGNUP_DATE_START, reference_date),
                "customer_segment": segment,
                "lifetime_value": lifetime_value,
            }
        )

    inject_duplicate_primary_keys(
        customers,
        defect_pools.duplicate_customer_id,
        "customer_id",
        DUPLICATE_CUSTOMER_ID_PAIRS,
    )
    return customers


def build_product_lookup(products: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(product["product_id"]): product for product in products}


def build_customer_lookup(customers: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Map customer_id to the first encountered row.

    When duplicate customer_id rows exist, order generation and signup validation
    use the first row's attributes (including signup_date).
    """
    lookup: dict[int, dict[str, Any]] = {}
    for customer in customers:
        customer_id = int(customer["customer_id"])
        if customer_id not in lookup:
            lookup[customer_id] = customer
    return lookup


def assign_order_status_and_payment(
    rng: random.Random,
    order_date: date,
    reference_date: date,
) -> tuple[str, date | None]:
    status = rng.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]
    if status == "Completed":
        payment_offset = rng.randint(0, 3)
        payment_date = order_date + timedelta(days=payment_offset)
        if payment_date > reference_date:
            payment_date = order_date
        return status, payment_date
    return status, None


def generate_orders(
    rng: random.Random,
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    defect_pools: OrderDefectPools,
    reference_date: date,
) -> list[dict[str, Any]]:
    customer_lookup = build_customer_lookup(customers)
    valid_customer_ids = list(customer_lookup.keys())
    valid_product_ids = [int(product["product_id"]) for product in products]
    product_lookup = build_product_lookup(products)

    orders: list[dict[str, Any]] = []
    for idx in range(ORDER_ROW_COUNT):
        order_id = idx + 1
        customer_id = rng.choice(valid_customer_ids)
        product_id = rng.choice(valid_product_ids)

        customer = customer_lookup[customer_id]
        signup_date = customer["signup_date"]
        order_date = random_date_between(rng, signup_date, reference_date)

        product = product_lookup[product_id]
        quantity = rng.randint(1, 5)
        unit_price = round_money(float(product["price"]) * rng.uniform(0.95, 1.05))
        total_amount = round_money(quantity * unit_price)
        order_status, payment_date = assign_order_status_and_payment(
            rng, order_date, reference_date
        )

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "order_status": order_status,
                "payment_date": payment_date,
            }
        )

    inject_order_defects(orders, defect_pools)
    return orders


def inject_order_defects(
    orders: list[dict[str, Any]],
    defect_pools: OrderDefectPools,
) -> None:
    ghost_customer_ids = list(range(GHOST_CUSTOMER_ID_START, GHOST_CUSTOMER_ID_END + 1))
    ghost_product_ids = list(range(GHOST_PRODUCT_ID_START, GHOST_PRODUCT_ID_END + 1))

    for idx in defect_pools.null_customer_id:
        orders[idx]["customer_id"] = None

    for idx in defect_pools.null_product_id:
        orders[idx]["product_id"] = None

    for i, idx in enumerate(sorted(defect_pools.orphan_customer_id)):
        orders[idx]["customer_id"] = ghost_customer_ids[i]

    for i, idx in enumerate(sorted(defect_pools.orphan_product_id)):
        orders[idx]["product_id"] = ghost_product_ids[i]

    inject_duplicate_primary_keys(
        orders,
        defect_pools.duplicate_order_id,
        "order_id",
        DUPLICATE_ORDER_ID_PAIRS,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class DataGenerationValidationError(Exception):
    """Raised when generated data fails validation."""


def validate_generated_data(
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    reference_date: date,
) -> None:
    errors: list[str] = []

    if len(customers) != CUSTOMER_ROW_COUNT:
        errors.append(f"customers row count: expected {CUSTOMER_ROW_COUNT}, got {len(customers)}")
    if len(products) != PRODUCT_ROW_COUNT:
        errors.append(f"products row count: expected {PRODUCT_ROW_COUNT}, got {len(products)}")
    if len(orders) != ORDER_ROW_COUNT:
        errors.append(f"orders row count: expected {ORDER_ROW_COUNT}, got {len(orders)}")

    null_email = count_null(customers, "email")
    if null_email != NULL_EMAIL_COUNT:
        errors.append(f"NULL email count: expected {NULL_EMAIL_COUNT}, got {null_email}")

    dup_customer_rows = count_duplicate_participants(customers, "customer_id")
    if dup_customer_rows != DUPLICATE_CUSTOMER_ID_ROWS:
        errors.append(
            "duplicate customer_id participant rows: "
            f"expected {DUPLICATE_CUSTOMER_ID_ROWS}, got {dup_customer_rows}"
        )
    errors.extend(
        validate_duplicate_pair_structure(
            customers,
            "customer_id",
            DUPLICATE_CUSTOMER_ID_ROWS,
            DUPLICATE_CUSTOMER_ID_PAIRS,
            "customers",
        )
    )

    null_order_customer = count_null(orders, "customer_id")
    if null_order_customer != NULL_ORDER_CUSTOMER_ID:
        errors.append(
            f"NULL order customer_id count: expected {NULL_ORDER_CUSTOMER_ID}, got {null_order_customer}"
        )

    null_order_product = count_null(orders, "product_id")
    if null_order_product != NULL_ORDER_PRODUCT_ID:
        errors.append(
            f"NULL order product_id count: expected {NULL_ORDER_PRODUCT_ID}, got {null_order_product}"
        )

    valid_customer_ids = {int(customer["customer_id"]) for customer in customers}
    valid_product_ids = {int(product["product_id"]) for product in products}

    orphan_customer = count_orphan_fk(orders, "customer_id", valid_customer_ids)
    if orphan_customer != ORPHAN_CUSTOMER_ID_COUNT:
        errors.append(
            f"orphan customer_id count: expected {ORPHAN_CUSTOMER_ID_COUNT}, got {orphan_customer}"
        )

    orphan_product = count_orphan_fk(orders, "product_id", valid_product_ids)
    if orphan_product != ORPHAN_PRODUCT_ID_COUNT:
        errors.append(
            f"orphan product_id count: expected {ORPHAN_PRODUCT_ID_COUNT}, got {orphan_product}"
        )

    dup_order_rows = count_duplicate_participants(orders, "order_id")
    if dup_order_rows != DUPLICATE_ORDER_ID_ROWS:
        errors.append(
            "duplicate order_id participant rows: "
            f"expected {DUPLICATE_ORDER_ID_ROWS}, got {dup_order_rows}"
        )
    errors.extend(
        validate_duplicate_pair_structure(
            orders,
            "order_id",
            DUPLICATE_ORDER_ID_ROWS,
            DUPLICATE_ORDER_ID_PAIRS,
            "orders",
        )
    )

    explicit_defect_rows = (
        null_email
        + dup_customer_rows
        + null_order_customer
        + null_order_product
        + orphan_customer
        + orphan_product
        + dup_order_rows
    )
    if explicit_defect_rows != TOTAL_EXPLICIT_DEFECT_ROWS:
        errors.append(
            f"total explicit defect rows: expected {TOTAL_EXPLICIT_DEFECT_ROWS}, "
            f"got {explicit_defect_rows}"
        )

    ghost_customer_in_parents = valid_customer_ids & set(
        range(GHOST_CUSTOMER_ID_START, GHOST_CUSTOMER_ID_END + 1)
    )
    if ghost_customer_in_parents:
        errors.append(f"ghost customer_id found in customers: {sorted(ghost_customer_in_parents)[:5]}")

    ghost_product_in_parents = valid_product_ids & set(
        range(GHOST_PRODUCT_ID_START, GHOST_PRODUCT_ID_END + 1)
    )
    if ghost_product_in_parents:
        errors.append(f"ghost product_id found in products: {sorted(ghost_product_in_parents)[:5]}")

    customer_lookup = build_customer_lookup(customers)

    for index, product in enumerate(products):
        price = float(product["price"])
        cost = float(product["cost"])
        if price <= cost:
            errors.append(f"product[{index}] price must be > cost (id={product['product_id']})")
        for numeric in ("price", "cost", "stock_quantity", "reorder_level"):
            if float(product[numeric]) < 0:
                errors.append(f"product[{index}] negative {numeric}")

    for index, customer in enumerate(customers):
        if customer["customer_segment"] not in CUSTOMER_SEGMENTS:
            errors.append(f"customer[{index}] invalid segment")
        if float(customer["lifetime_value"]) < 0:
            errors.append(f"customer[{index}] negative lifetime_value")
        if customer["signup_date"] > reference_date:
            errors.append(f"customer[{index}] signup_date after reference date")

    for index, order in enumerate(orders):
        if order["order_status"] not in ORDER_STATUSES:
            errors.append(f"order[{index}] invalid order_status")

        quantity = int(order["quantity"])
        unit_price = float(order["unit_price"])
        total_amount = float(order["total_amount"])
        expected_total = round_money(quantity * unit_price)

        if quantity < 0 or unit_price < 0 or total_amount < 0:
            errors.append(f"order[{index}] negative numeric value")

        if total_amount != expected_total:
            errors.append(
                f"order[{index}] total_amount mismatch: {total_amount} != {expected_total}"
            )

        status = order["order_status"]
        payment_date = order["payment_date"]
        if status == "Completed" and payment_date is None:
            errors.append(f"order[{index}] Completed order missing payment_date")
        if status in ("Pending", "Cancelled") and payment_date is not None:
            errors.append(f"order[{index}] {status} order must have NULL payment_date")

        customer_id = order["customer_id"]
        if customer_id is not None and customer_id in customer_lookup:
            signup_date = customer_lookup[customer_id]["signup_date"]
            order_date = order["order_date"]
            if order_date < signup_date:
                errors.append(
                    f"order[{index}] order_date {order_date} before signup {signup_date}"
                )
            if order_date > reference_date:
                errors.append(f"order[{index}] order_date after reference date")

    if errors:
        print("Data generation validation failed:", file=sys.stderr)
        for message in errors[:50]:
            print(f"  - {message}", file=sys.stderr)
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more", file=sys.stderr)
        raise DataGenerationValidationError(f"{len(errors)} validation error(s)")

    print("Validation summary:")
    print(f"  reference_date: {reference_date.isoformat()}")
    print(f"  customers: {len(customers):,} rows")
    print(f"  products:  {len(products):,} rows")
    print(f"  orders:    {len(orders):,} rows")
    print(f"  NULL email: {null_email}")
    print(f"  duplicate customer_id participants: {dup_customer_rows}")
    print(f"  NULL order customer_id: {null_order_customer}")
    print(f"  NULL order product_id: {null_order_product}")
    print(f"  orphan customer_id: {orphan_customer}")
    print(f"  orphan product_id: {orphan_product}")
    print(f"  duplicate order_id participants: {dup_order_rows}")
    print(f"  total explicit defect rows: {explicit_defect_rows}")


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------


def format_cell(value: Any) -> str:
    """
    Format a value for CSV output.

    None is written as an empty field (empty string to the CSV writer).
    Dates are ISO formatted (YYYY-MM-DD).
    """
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: format_cell(row[column]) for column in columns})
        try:
            temp_path.replace(path)
        except OSError as exc:
            # Databricks Unity Catalog Volumes can reject atomic rename/replace.
            # Fall back to direct write to target path when operation isn't supported.
            if exc.errno != errno.EOPNOTSUPP:
                raise
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow({column: format_cell(row[column]) for column in columns})
            if temp_path.exists():
                temp_path.unlink()
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def write_datasets(
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    sorted_customers = sorted(customers, key=lambda row: int(row["customer_id"]))
    sorted_products = sorted(products, key=lambda row: int(row["product_id"]))
    sorted_orders = sorted(orders, key=lambda row: int(row["order_id"]))

    write_csv(output_dir / "customers.csv", CUSTOMER_COLUMNS, sorted_customers)
    write_csv(output_dir / "products.csv", PRODUCT_COLUMNS, sorted_products)
    write_csv(output_dir / "orders.csv", ORDER_COLUMNS, sorted_orders)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic e-commerce CSV datasets with intentional data quality defects."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory for CSV output (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--reference-date",
        type=str,
        default=REFERENCE_DATE.isoformat(),
        help=f"Fixed reference date for generation (default: {REFERENCE_DATE.isoformat()})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reference_date = date.fromisoformat(args.reference_date)
    output_dir: Path = args.output_dir

    rng = random.Random(RANDOM_SEED)
    fake = Faker(FAKER_LOCALE)
    Faker.seed(RANDOM_SEED)
    fake.seed_instance(RANDOM_SEED)

    customer_pools = reserve_customer_defect_pools(rng)
    order_pools = reserve_order_defect_pools(rng)

    products = generate_products(rng, fake)
    customers = generate_customers(rng, fake, customer_pools, reference_date)
    orders = generate_orders(rng, customers, products, order_pools, reference_date)

    validate_generated_data(customers, products, orders, reference_date)
    write_datasets(customers, products, orders, output_dir)

    print(f"Wrote CSV files to {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DataGenerationValidationError:
        raise SystemExit(1)
