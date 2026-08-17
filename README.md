# Databricks Medallion Pipeline

AI Capability Assessment — production-oriented medallion architecture pipeline for e-commerce sales data.

## Overview

```
Source CSVs → Bronze → Silver → Gold → Databricks SQL Dashboard
```

| Layer | Status |
|-------|--------|
| Data generation | Complete + validated |
| Bronze | Complete + runtime validated |
| Silver | Complete + runtime validated |
| Gold | Complete + runtime validated |
| Dashboard SQL & docs | Complete |
| Databricks Dashboard UI | Complete (manual) |
| Automated test suite | Not implemented |

## Prerequisites

- Databricks Free Edition (or equivalent) with Unity Catalog
- Python 3.x, PySpark, SQL
- Delta Lake (included in Databricks Runtime)
- Cursor (or other AI assistant) for development workflow

## Quick Start

### 1. Generate seed data (local)

```bash
cd src/data_generation
python generate_sample_data.py
```

Output: `data/customers.csv`, `data/products.csv`, `data/orders.csv`

See `src/data_generation/DATA_GENERATION_NOTES.md` for intentional quality issues.

### 2. Upload CSVs to Databricks

Upload to the Unity Catalog volume:

```
/Volumes/workspace/default/medallion_data/
```

See `src/bronze/README.md` for upload options.

### 3. Run the pipeline (Databricks notebook)

Run each layer in order:

```python
import sys

# Bronze
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/bronze")
from ingest_all import main as bronze_main
bronze_main()

# Silver
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/silver")
from create_silver_tables import main as silver_main
silver_main()

# Gold
sys.path.insert(0, "/Workspace/Repos/<user>/databricks-medallion-pipeline/src/gold")
from create_gold_tables import main as gold_main
gold_main()
```

### 4. Build the dashboard (manual)

1. Create SQL queries from `src/dashboard/dashboard_queries.sql`
2. Follow `src/dashboard/DASHBOARD_GUIDE.md` to configure the Databricks SQL Dashboard UI

## Expected Runtime Row Counts

| Table | Rows |
|-------|------|
| `bronze.customers` / `silver.customers` | 10,000 |
| `bronze.products` / `silver.products` | 500 |
| `bronze.orders` / `silver.orders` | 100,000 |
| `silver.dq_metrics` | 10 per run |
| `gold.sales_by_product` | 500 |
| `gold.revenue_by_customer` | 9,940 |
| `gold.customer_segmentation` | 4 |
| `gold.daily_weekly_trends` | 2,679 |

## Project References

| Document | Purpose |
|----------|---------|
| `assignment/assignment-requirements.md` | Assignment source of truth |
| `requirements-analysis.md` | Requirements and decisions |
| `design-notes.md` | Architecture and layer design |
| `data-model.md` | Schemas and entities |
| `data-quality-strategy.md` | DQ rules and thresholds |
| `tool-workflow.md` | AI workflow (Part A) |
| `debugging-notes.md` | Issues and resolutions |
| `reflection.md` | Assessment reflection |
| `final-ai-usage-summary.md` | AI usage summary |

## Repository Layout

| Path | Purpose |
|------|---------|
| `src/data_generation/` | Sample CSV generator |
| `src/bronze/` | Raw ingestion |
| `src/silver/` | Data quality and validation |
| `src/gold/` | Business aggregations |
| `src/dashboard/` | Dashboard SQL and setup guide |
| `data/` | Generated CSV seed data |
| `database/` | Schema reference and setup notes |
| `tests/` | Data quality and pipeline tests (planned) |
| `docs/` | Supplementary documentation index |
| `ai-prompts/` | AI interaction history (see `ai-prompts/README.md`) |
| `tool-specific/cursor-workflow/` | Cursor workflow artifacts |
| `assignment/` | Assignment source of truth |

## Layer Documentation

| Layer | README |
|-------|--------|
| Data generation | `src/data_generation/README.md` |
| Bronze | `src/bronze/README.md` |
| Silver | `src/silver/README.md` |
| Gold | `src/gold/README.md` |
| Dashboard | `src/dashboard/README.md` |

## Engineering Rules

See `.cursor/rules/project-engineering.mdc` for medallion layer boundaries, DQ principles, and workflow expectations.
