# Data Generation

Sample CSV generator for the assessment pipeline.

## Planned Files

| File | Purpose |
|------|---------|
| `generate_sample_data.py` | Python/PySpark script to create customers, orders, products CSVs with intentional quality issues |

## Output

Generated files will be written to `data/`:

- `customers.csv` (10,000 rows)
- `orders.csv` (100,000 rows)
- `products.csv` (500 rows)

## Notes

See `DATA_GENERATION_NOTES.md` for generation approach and quality issue documentation.
