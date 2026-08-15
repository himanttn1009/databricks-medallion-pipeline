"""Orchestrate full Bronze layer ingestion for all entities."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Sequence

from pyspark.sql import SparkSession

from ingest_utils import BronzeIngestionError, IngestResult, generate_batch_id, ingest_entity

INGEST_SEQUENCE: Sequence[str] = ("customers", "orders", "products")


def main() -> int:
    """Run Bronze ingestion for customers, orders, and products."""
    spark = SparkSession.builder.appName("bronze-ingest-all").getOrCreate()
    batch_id = generate_batch_id()
    results: list[IngestResult] = []
    failed_entity: str | None = None
    failure_message: str | None = None

    print(f"Starting Bronze ingestion (batch_id={batch_id})")

    for entity in INGEST_SEQUENCE:
        ingest_timestamp = datetime.now(timezone.utc)
        try:
            result = ingest_entity(
                spark,
                entity=entity,
                batch_id=batch_id,
                ingest_timestamp=ingest_timestamp,
            )
            results.append(result)
            print(
                f"[SUCCESS] {result.entity}: {result.row_count} rows -> "
                f"{result.target_table}"
            )
        except BronzeIngestionError as exc:
            failed_entity = entity
            failure_message = str(exc)
            print(f"[FAILED] {entity}: {exc}", file=sys.stderr)
            break
        except Exception as exc:
            failed_entity = entity
            failure_message = str(exc)
            print(f"[FAILED] {entity}: {exc}", file=sys.stderr)
            break

    print("\n--- Bronze Ingestion Summary ---")
    print(f"batch_id: {batch_id}")
    print(f"succeeded: {len(results)}/{len(INGEST_SEQUENCE)}")
    for result in results:
        print(
            f"  - {result.entity}: {result.row_count} rows -> {result.target_table}"
        )

    if failed_entity:
        print(f"\nStopped after first failure ({failed_entity}): {failure_message}")
        return 1

    print("\nAll Bronze entities ingested successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
