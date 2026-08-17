# Bronze Layer

Raw CSV ingestion into Delta Lake tables with minimal transformation. Bronze preserves source fidelity — all intentional data defects survive for Silver-layer quality processing.

> **Status:** Implementation complete. **Runtime validated** — row counts 10,000 / 500 / 100,000 confirmed in Databricks.

## Overview

```
/Volumes/workspace/default/medallion_data/*.csv
        │
        ▼
  ingest_utils.py  (shared validation + read + metadata + write)
        │
        ├── bronze.customers   (10,000 rows)
        ├── bronze.products    (500 rows)
        └── bronze.orders      (100,000 rows)
        │
        └── audit.ingestion_log  (append, one record per entity per run)
```

## Prerequisites

- Databricks **Free Edition** with **Unity Catalog** enabled
- Cluster with **PySpark** and **Delta Lake** (standard on Databricks Runtime)
- Source CSV files in the Unity Catalog managed volume (see below)
- Read access to the volume; write access to create/update `bronze` and `audit` schemas/tables

No additional Python packages are required beyond the Databricks runtime.

## Source CSV Location — Unity Catalog Volume

The Bronze layer reads from the managed volume:

```
/Volumes/workspace/default/medallion_data/
```

Expected files:

| File | Full path |
|------|-----------|
| `customers.csv` | `/Volumes/workspace/default/medallion_data/customers.csv` |
| `products.csv` | `/Volumes/workspace/default/medallion_data/products.csv` |
| `orders.csv` | `/Volumes/workspace/default/medallion_data/orders.csv` |

### Option A — Databricks UI (Catalog Explorer)

1. Open **Catalog** → **workspace** → **default** → **Volumes** → **medallion_data**.
2. Upload `customers.csv`, `products.csv`, and `orders.csv` from the repository `data/` directory.

### Option B — Notebook `dbutils`

```python
volume_path = "/Volumes/workspace/default/medallion_data"

# After uploading CSVs to a temporary workspace path:
dbutils.fs.cp("file:/path/to/customers.csv", f"{volume_path}/customers.csv")
dbutils.fs.cp("file:/path/to/products.csv", f"{volume_path}/products.csv")
dbutils.fs.cp("file:/path/to/orders.csv", f"{volume_path}/orders.csv")
```

### Option C — Verify files are present

```python
display(dbutils.fs.ls("/Volumes/workspace/default/medallion_data"))
```

You should see `customers.csv`, `products.csv`, and `orders.csv`.

## Configurable Input Path

Default source base path: `/Volumes/workspace/default/medallion_data/`

Override via environment variable before running (same mechanism as before):

```python
import os
os.environ["MEDALLION_DBFS_INPUT_BASE"] = "/Volumes/workspace/default/medallion_data"
```

Or set `MEDALLION_DBFS_INPUT_BASE` on the cluster as an environment variable / job parameter.

Entity source paths are derived in `config.py` — do not hardcode paths in individual scripts.

## Module Layout

| File | Purpose |
|------|---------|
| `config.py` | Paths, table names, expected row counts, CSV options |
| `schemas.py` | Explicit `StructType` schemas for each entity |
| `ingest_utils.py` | Shared ingestion, validation, metadata, audit logic |
| `01_ingest_customers.py` | Thin entry point for customers |
| `02_ingest_orders.py` | Thin entry point for orders |
| `03_ingest_products.py` | Thin entry point for products |
| `ingest_all.py` | Orchestrator for all three entities |

## Bronze Tables

| Table | Expected rows | Source file |
|-------|---------------|-------------|
| `bronze.customers` | 10,000 | `customers.csv` |
| `bronze.products` | 500 | `products.csv` |
| `bronze.orders` | 100,000 | `orders.csv` |

Each table contains:

- All source business columns (unchanged, nullable)
- `_ingest_timestamp` — entity-level ingestion timestamp
- `_source_file` — configured volume source path
- `_ingest_batch_id` — shared run identifier (one per `ingest_all.py` run)

Tables are **Delta**, **overwrite** mode, **not partitioned**.

## Audit Table

`audit.ingestion_log` — append-only history of ingestion runs.

| Column | Description |
|--------|-------------|
| `run_id` | Batch/run identifier (`_ingest_batch_id`) |
| `layer` | Always `bronze` |
| `entity` | `customers`, `orders`, or `products` |
| `status` | `SUCCESS` or `FAILED` |
| `row_count` | Rows ingested (null on failure) |
| `source_path` | Volume CSV path |
| `target_table` | Fully qualified Bronze table |
| `message` | Success or error summary |
| `run_timestamp` | Entity ingestion timestamp |

## Running in Databricks

### Setup Python path

Clone or sync the repo to Databricks Repos, then add the Bronze module directory to `sys.path`:

```python
import sys
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/bronze")
```

Adjust the path to match your Repos location.

### Run all entities (recommended)

**Notebook:**

```python
import sys
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/bronze")

from ingest_all import main

exit_code = main()
if exit_code != 0:
    raise RuntimeError("Bronze ingestion failed")
```

Orchestration order: **customers → orders → products**. One `batch_id` is shared across all entities in a single `ingest_all.py` run. The orchestrator **stops after the first entity failure**; entities that completed successfully before the failure retain their Bronze tables and `SUCCESS` audit records.

### Run individual entities

```python
import sys
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/bronze")

from importlib import import_module

for module_name in ("01_ingest_customers", "02_ingest_orders", "03_ingest_products"):
    module = import_module(module_name)
    exit_code = module.main()
    if exit_code != 0:
        raise RuntimeError(f"{module_name} failed")
```

Or run a single entity:

```python
from importlib import import_module
customers = import_module("01_ingest_customers")
customers.main()
```

Each standalone script generates its own `batch_id`.

### Verify results

```sql
SELECT COUNT(*) FROM bronze.customers;   -- expect 10000
SELECT COUNT(*) FROM bronze.products;    -- expect 500
SELECT COUNT(*) FROM bronze.orders;      -- expect 100000

SELECT * FROM audit.ingestion_log ORDER BY run_timestamp DESC;
```

## Validation Performed

Bronze **does** validate:

- Source file exists and is not empty
- CSV header matches expected schema (missing/extra columns and incorrect column order fail)
- Malformed CSV records (`mode=FAILFAST`)
- Row count matches expected values (pre-write and post-write)
- Delta write success

Bronze **does not** perform data-quality cleaning. The following defects are **preserved** for Silver:

| Defect | Count |
|--------|-------|
| NULL customer emails | 50 |
| Duplicate `customer_id` rows | 10 |
| NULL `order.customer_id` | 100 |
| NULL `order.product_id` | 200 |
| Orphan `customer_id` in orders | 50 |
| Orphan `product_id` in orders | 30 |
| Duplicate `order_id` rows | 20 |

No deduplication, filtering, FK repair, or quality flags are applied in Bronze.

## NULL Handling

- CSV empty fields are read with `nullValue=""` → Spark `NULL`
- No `coalesce`, default fills, or imputation
- Nullable business columns remain NULL exactly as in source

## Rerun Behavior

- **Bronze tables:** `overwrite` mode — re-running replaces table contents (idempotent full refresh)
- **Audit log:** `append` mode — each run adds new history records
- Re-running with the same source data yields the same row counts and preserved defects

## Error Handling

Failures include context: entity name, source path, target table, and expected vs actual row counts where applicable. Common fatal errors:

| Error | Cause |
|-------|-------|
| Source file missing | CSV not present in configured volume path |
| Empty source file | Zero-byte or header-only file |
| Header mismatch | Column names differ, extra/missing columns, or column order differs from schema |
| Malformed CSV | Unparseable values (`FAILFAST`) |
| Row-count mismatch | Source row count ≠ expected |
| Delta write failure | Permissions, metastore, or cluster issues |

Failed entity ingestions write a `FAILED` record to `audit.ingestion_log`.

## Important Limitation

**Bronze is not a cleansing layer.** It lands raw data with ingestion metadata only. All validation, deduplication, referential-integrity checks, and business-rule enforcement happen in **Silver**.
