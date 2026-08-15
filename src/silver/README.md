# Silver Layer

Data quality checks, validation, and flagging — do not silently delete bad rows.

## Planned Files

| File | Purpose |
|------|---------|
| `01_quality_completeness.py` | Completeness checks |
| `02_quality_uniqueness.py` | Uniqueness checks |
| `03_quality_type_validation.py` | Type/format validation |
| `04_quality_referential_integrity.py` | Referential integrity checks |
| `05_quality_business_logic.py` | Business rule validation |
| `create_silver_tables.py` | Orchestrate Silver table creation |

## Responsibilities

- Flag bad rows via `quality_check_result` column
- Generate quality metrics report (% passed per check)
- Preserve traceability of invalid records
