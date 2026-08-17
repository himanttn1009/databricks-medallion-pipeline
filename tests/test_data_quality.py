"""
Data quality tests for generated seed CSVs.

Validates intentional defect populations documented in DATA_GENERATION_NOTES.md §7.
Uses stdlib only (csv + unittest) — no pipeline or Databricks dependency.
"""

from __future__ import annotations

import csv
import unittest
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

CUSTOMER_ROWS = 10_000
PRODUCT_ROWS = 500
ORDER_ROWS = 100_000

NULL_EMAIL_COUNT = 50
DUPLICATE_CUSTOMER_ID_ROWS = 10
NULL_ORDER_CUSTOMER_ID = 100
NULL_ORDER_PRODUCT_ID = 200
ORPHAN_CUSTOMER_ID_COUNT = 50
ORPHAN_PRODUCT_ID_COUNT = 30
DUPLICATE_ORDER_ID_ROWS = 20

VALID_CUSTOMER_ID_MAX = 10_000
VALID_PRODUCT_ID_MAX = 500
GHOST_CUSTOMER_ID_START = 90_001
GHOST_CUSTOMER_ID_END = 90_050
GHOST_PRODUCT_ID_START = 901
GHOST_PRODUCT_ID_END = 930


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _duplicate_participant_count(values: list[int | None]) -> int:
    """Count rows participating in duplicate-key groups (value appears > 1 time)."""
    non_null = [value for value in values if value is not None]
    counts = Counter(non_null)
    return sum(count for count in counts.values() if count > 1)


class SeedDataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.customers = _read_csv(DATA_DIR / "customers.csv")
        cls.products = _read_csv(DATA_DIR / "products.csv")
        cls.orders = _read_csv(DATA_DIR / "orders.csv")

    def test_csv_row_counts(self) -> None:
        self.assertEqual(len(self.customers), CUSTOMER_ROWS)
        self.assertEqual(len(self.products), PRODUCT_ROWS)
        self.assertEqual(len(self.orders), ORDER_ROWS)

    def test_customers_null_email_count(self) -> None:
        null_emails = sum(1 for row in self.customers if not row["email"].strip())
        self.assertEqual(null_emails, NULL_EMAIL_COUNT)

    def test_customers_duplicate_customer_id_rows(self) -> None:
        customer_ids = [_parse_int(row["customer_id"]) for row in self.customers]
        duplicate_rows = _duplicate_participant_count(customer_ids)
        self.assertEqual(duplicate_rows, DUPLICATE_CUSTOMER_ID_ROWS)

    def test_orders_null_customer_id_count(self) -> None:
        null_customer_ids = sum(
            1 for row in self.orders if _parse_int(row["customer_id"]) is None
        )
        self.assertEqual(null_customer_ids, NULL_ORDER_CUSTOMER_ID)

    def test_orders_null_product_id_count(self) -> None:
        null_product_ids = sum(
            1 for row in self.orders if _parse_int(row["product_id"]) is None
        )
        self.assertEqual(null_product_ids, NULL_ORDER_PRODUCT_ID)

    def test_orders_orphan_customer_id_count(self) -> None:
        orphan_customer_ids = 0
        for row in self.orders:
            customer_id = _parse_int(row["customer_id"])
            if customer_id is None:
                continue
            if customer_id < 1 or customer_id > VALID_CUSTOMER_ID_MAX:
                orphan_customer_ids += 1
        self.assertEqual(orphan_customer_ids, ORPHAN_CUSTOMER_ID_COUNT)
        ghost_ids = {
            _parse_int(row["customer_id"])
            for row in self.orders
            if GHOST_CUSTOMER_ID_START
            <= (_parse_int(row["customer_id"]) or 0)
            <= GHOST_CUSTOMER_ID_END
        }
        self.assertEqual(len(ghost_ids), ORPHAN_CUSTOMER_ID_COUNT)

    def test_orders_orphan_product_id_count(self) -> None:
        orphan_product_ids = 0
        for row in self.orders:
            product_id = _parse_int(row["product_id"])
            if product_id is None:
                continue
            if product_id < 1 or product_id > VALID_PRODUCT_ID_MAX:
                orphan_product_ids += 1
        self.assertEqual(orphan_product_ids, ORPHAN_PRODUCT_ID_COUNT)
        ghost_ids = {
            _parse_int(row["product_id"])
            for row in self.orders
            if GHOST_PRODUCT_ID_START
            <= (_parse_int(row["product_id"]) or 0)
            <= GHOST_PRODUCT_ID_END
        }
        self.assertEqual(len(ghost_ids), ORPHAN_PRODUCT_ID_COUNT)

    def test_orders_duplicate_order_id_rows(self) -> None:
        order_ids = [_parse_int(row["order_id"]) for row in self.orders]
        duplicate_rows = _duplicate_participant_count(order_ids)
        self.assertEqual(duplicate_rows, DUPLICATE_ORDER_ID_ROWS)

    def test_total_explicit_defect_participants(self) -> None:
        customer_ids = [_parse_int(row["customer_id"]) for row in self.customers]
        order_ids = [_parse_int(row["order_id"]) for row in self.orders]

        customer_defects = sum(1 for row in self.customers if not row["email"].strip())
        customer_defects += _duplicate_participant_count(customer_ids)

        order_defects = sum(
            1 for row in self.orders if _parse_int(row["customer_id"]) is None
        )
        order_defects += sum(
            1 for row in self.orders if _parse_int(row["product_id"]) is None
        )
        order_defects += sum(
            1
            for row in self.orders
            if (cid := _parse_int(row["customer_id"])) is not None
            and (cid < 1 or cid > VALID_CUSTOMER_ID_MAX)
        )
        order_defects += sum(
            1
            for row in self.orders
            if (pid := _parse_int(row["product_id"])) is not None
            and (pid < 1 or pid > VALID_PRODUCT_ID_MAX)
        )
        order_defects += _duplicate_participant_count(order_ids)

        self.assertEqual(customer_defects + order_defects, 460)


if __name__ == "__main__":
    unittest.main()
