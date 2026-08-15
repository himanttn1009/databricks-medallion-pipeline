"""Bronze ingestion entry point for customers."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from ingest_utils import generate_batch_id, ingest_entity


def main() -> int:
    """Ingest customers.csv into bronze.customers."""
    spark = SparkSession.builder.appName("bronze-ingest-customers").getOrCreate()
    batch_id = generate_batch_id()
    ingest_timestamp = datetime.now(timezone.utc)

    try:
        result = ingest_entity(
            spark,
            entity="customers",
            batch_id=batch_id,
            ingest_timestamp=ingest_timestamp,
        )
        print(
            f"[SUCCESS] {result.entity}: {result.row_count} rows -> {result.target_table} "
            f"(batch_id={result.batch_id})"
        )
        return 0
    except Exception as exc:
        print(f"[FAILED] customers ingestion: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
