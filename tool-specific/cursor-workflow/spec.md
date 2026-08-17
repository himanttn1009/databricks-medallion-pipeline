# Design Specification

Medallion pipeline for synthetic e-commerce CSV sources → Databricks Delta tables → SQL Dashboard.

**Status:** Design complete across all layers. Implementation and runtime validation complete. See `design-notes.md` for full detail.

## Scope

- Three CSV sources: customers (10K), products (500), orders (100K)
- Four pipeline layers: Bronze, Silver, Gold, Dashboard
- Intentional ~460 data quality defects for Silver validation
- Databricks Free Edition with Unity Catalog

## Architecture

```
data/*.csv → Bronze (raw Delta) → Silver (DQ flags + metrics) → Gold (aggregations) → Dashboard (Gold-only SQL)
```

| Layer | Reads | Writes |
|-------|-------|--------|
| Bronze | CSV volume | `bronze.*`, `audit.ingestion_log` |
| Silver | `bronze.*` | `silver.*`, `silver.dq_metrics` |
| Gold | `silver.*` WHERE `is_valid=true` | `gold.*` (4 tables) |
| Dashboard | `gold.*` | — (read-only) |

## Data Model

Authoritative schemas: `data-model.md`

| Schema | Key tables |
|--------|------------|
| `bronze` | customers, products, orders |
| `silver` | customers, products, orders, dq_metrics |
| `gold` | sales_by_product, revenue_by_customer, customer_segmentation, daily_weekly_trends |

## Layer Designs

### Bronze

- Raw CSV ingest with metadata columns (`_ingest_timestamp`, `_source_file`, `_ingest_batch_id`)
- Fail-fast validation: header, column order, row counts, FAILFAST CSV parse
- No cleansing — preserve intentional defects
- See `design-notes.md` §3, `src/bronze/README.md`

### Silver

- Five DQ scripts: completeness, uniqueness, type validation, referential integrity, business logic
- Row-level `quality_check_result` + `is_valid`; all Bronze rows preserved
- 10 `dq_metrics` rows per run (`run_id`, entity, check_name)
- `REFERENCE_DATE = 2026-08-15`
- See `design-notes.md` §4, `src/silver/README.md`

### Gold

- Four aggregations; `is_valid=true` + `order_status='Completed'` filter
- Customer segmentation: High-Value / Repeat / One-Time / Inactive (P75 threshold)
- Daily + weekly trends in single table (`period_type`)
- No `country` column (GD-07)
- See `design-notes.md` §5, `src/gold/README.md`

### Dashboard

- 9 widgets: 4 KPIs + 4 visualizations + 1 table
- Gold-only sources; 5 filters
- Date filters apply to Revenue Trend only (DD-01)
- Manual Databricks SQL UI assembly
- See `design-notes.md` §6, `src/dashboard/DASHBOARD_GUIDE.md`

## Data Quality Rules

Full strategy: `data-quality-strategy.md`

| Check | Entity | Key rules |
|-------|--------|-----------|
| Completeness | customers, orders | email NOT NULL; order FKs NOT NULL |
| Uniqueness | customers, orders | PK uniqueness (NULL keys excluded) |
| Type validation | all | Enums, non-negative amounts, valid dates |
| Referential integrity | orders | FKs exist in Bronze parents |
| Business logic | products, orders | price > cost; amount consistency; payment dates |

## Testing Approach

- Generator: `validate_generated_data()` pre-write
- Manual Databricks runtime validation per layer
- Automated `pytest` suite: planned, not implemented (`tests/README.md`)

## Resolved Decisions

| ID | Decision |
|----|----------|
| SD-06 | `REFERENCE_DATE = 2026-08-15` |
| GD-07 | No `country` in Gold |
| GD-09 | P75 for High-Value segmentation |
| DD-01 | Date filters → VIZ-04 only |
| DD-08 | Pie measure = `customer_count` on `segment_type` |

Open decisions: none blocking submission. See `requirements-analysis.md` §17 for resolved ambiguities.
