# Data Generation

Sample CSV generator for the assessment pipeline.

> **Status:** Implementation complete. Generator validated — CSVs produced with expected row counts and intentional quality issues.

## Files

| File | Purpose |
|------|---------|
| `generate_sample_data.py` | Creates customers, orders, products CSVs with intentional quality issues |
| `DATA_GENERATION_NOTES.md` | Generation approach, defect inventory, validation rules |

## Output

Generated files are written to `data/`:

| File | Rows |
|------|------|
| `customers.csv` | 10,000 |
| `orders.csv` | 100,000 |
| `products.csv` | 500 |

## Run locally

```bash
cd src/data_generation
python generate_sample_data.py
```

The script runs `validate_generated_data()` before writing CSVs.

## Key constants

| Constant | Value |
|----------|-------|
| `REFERENCE_DATE` | 2026-08-15 |
| Intentional defective rows | 460 total across seven defect types |

## Next step

Upload generated CSVs to the Databricks volume (see `src/bronze/README.md` and `database/seed-data-notes.md`).
