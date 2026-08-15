# Bronze Layer

Raw CSV ingestion into Databricks — no transformations or cleaning.

## Planned Files

| File | Purpose |
|------|---------|
| `01_ingest_customers.py` | Ingest customers.csv to Bronze |
| `02_ingest_orders.py` | Ingest orders.csv to Bronze |
| `03_ingest_products.py` | Ingest products.csv to Bronze |
| `ingest_all.py` | Orchestrate all Bronze ingestion |

## Responsibilities

- Read CSVs from S3/DBFS
- Create Bronze tables (raw, unchanged data)
- Handle schema inference and data types
- Log ingestion metadata (row counts, timestamp)
