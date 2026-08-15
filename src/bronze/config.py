"""Centralized configuration for Bronze CSV ingestion."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# Schema and table names
# ---------------------------------------------------------------------------

BRONZE_SCHEMA: Final[str] = "bronze"
AUDIT_SCHEMA: Final[str] = "audit"

BRONZE_TABLE_CUSTOMERS: Final[str] = "customers"
BRONZE_TABLE_PRODUCTS: Final[str] = "products"
BRONZE_TABLE_ORDERS: Final[str] = "orders"
AUDIT_TABLE_INGESTION_LOG: Final[str] = "ingestion_log"

LAYER_BRONZE: Final[str] = "bronze"

# ---------------------------------------------------------------------------
# Source paths (configurable via environment variable)
# ---------------------------------------------------------------------------

DEFAULT_DBFS_INPUT_BASE: Final[str] = "dbfs:/FileStore/medallion_pipeline/data"


def get_dbfs_input_base() -> str:
    """Return the DBFS base path for source CSV files."""
    return os.environ.get("MEDALLION_DBFS_INPUT_BASE", DEFAULT_DBFS_INPUT_BASE).rstrip("/")


def get_entity_source_path(entity: str) -> str:
    """Return the full source path for an entity CSV file."""
    filename = ENTITY_SOURCE_FILES[entity]
    return f"{get_dbfs_input_base()}/{filename}"


ENTITY_SOURCE_FILES: Final[dict[str, str]] = {
    "customers": "customers.csv",
    "products": "products.csv",
    "orders": "orders.csv",
}

# ---------------------------------------------------------------------------
# Expected row counts (validated at ingest time)
# ---------------------------------------------------------------------------

EXPECTED_ROW_COUNTS: Final[dict[str, int]] = {
    "customers": 10_000,
    "products": 500,
    "orders": 100_000,
}

# ---------------------------------------------------------------------------
# Fully qualified table names
# ---------------------------------------------------------------------------


def bronze_table_name(entity: str) -> str:
    """Return fully qualified Bronze table name for an entity."""
    table = {
        "customers": BRONZE_TABLE_CUSTOMERS,
        "products": BRONZE_TABLE_PRODUCTS,
        "orders": BRONZE_TABLE_ORDERS,
    }[entity]
    return f"{BRONZE_SCHEMA}.{table}"


def audit_table_name() -> str:
    """Return fully qualified audit ingestion log table name."""
    return f"{AUDIT_SCHEMA}.{AUDIT_TABLE_INGESTION_LOG}"


# ---------------------------------------------------------------------------
# CSV reader options
# ---------------------------------------------------------------------------

CSV_READER_OPTIONS: Final[dict[str, str]] = {
    "header": "true",
    "dateFormat": "yyyy-MM-dd",
    "timestampFormat": "yyyy-MM-dd'T'HH:mm:ss",
    "nullValue": "",
    "mode": "FAILFAST",
    "quote": '"',
    "escape": '"',
    "multiLine": "false",
}

# Audit status values
AUDIT_STATUS_SUCCESS: Final[str] = "SUCCESS"
AUDIT_STATUS_FAILED: Final[str] = "FAILED"


@dataclass(frozen=True)
class EntityConfig:
    """Configuration bundle for a single Bronze entity ingest."""

    entity: str
    source_path: str
    target_table: str
    expected_row_count: int


def get_entity_config(entity: str) -> EntityConfig:
    """Build entity configuration from centralized constants."""
    if entity not in EXPECTED_ROW_COUNTS:
        raise ValueError(f"Unknown entity: {entity}")
    return EntityConfig(
        entity=entity,
        source_path=get_entity_source_path(entity),
        target_table=bronze_table_name(entity),
        expected_row_count=EXPECTED_ROW_COUNTS[entity],
    )
