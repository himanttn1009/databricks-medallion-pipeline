# Seed Data Notes

## Source

Seed CSVs are produced locally by:

```
src/data_generation/generate_sample_data.py
```

Written to `data/` in the repository. The generator uses `REFERENCE_DATE = 2026-08-15` and embeds intentional quality defects for Silver-layer validation.

## Row Counts

| Dataset | Expected Rows |
|---------|---------------|
| customers | 10,000 |
| orders | 100,000 |
| products | 500 |

## Intentional Quality Issues

~460 defective rows across seven types. Full inventory:

- `src/data_generation/DATA_GENERATION_NOTES.md`
- `data-quality-strategy.md`
- `data/README.md`

## Loading Approach

### Local generation

```bash
cd src/data_generation
python generate_sample_data.py
```

Pre-write validation (`validate_generated_data()`) runs automatically.

### Upload to Databricks

Target Unity Catalog volume:

```
/Volumes/workspace/default/medallion_data/
```

**Option A — Catalog Explorer UI**

1. Catalog → workspace → default → Volumes → medallion_data
2. Upload `customers.csv`, `products.csv`, `orders.csv`

**Option B — dbutils**

```python
volume_path = "/Volumes/workspace/default/medallion_data"
dbutils.fs.cp("file:/path/to/customers.csv", f"{volume_path}/customers.csv")
dbutils.fs.cp("file:/path/to/products.csv", f"{volume_path}/products.csv")
dbutils.fs.cp("file:/path/to/orders.csv", f"{volume_path}/orders.csv")
```

**Verify:**

```python
display(dbutils.fs.ls("/Volumes/workspace/default/medallion_data"))
```

### Bronze ingest

After upload, run `src/bronze/ingest_all.py` (see `src/bronze/README.md`).

Bronze preserves all intentional defects — no cleansing at ingest time.
