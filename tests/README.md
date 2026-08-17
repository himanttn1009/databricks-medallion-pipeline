# Tests

Data quality validation for generated seed CSVs and (planned) pipeline integration.

## Status

| Area | Status |
|------|--------|
| Data quality tests (`test_data_quality.py`) | **Implemented** — stdlib `unittest`, CSV defect counts |
| Pipeline integration tests | Not implemented |
| Manual Databricks runtime validation | Complete (Bronze → Silver → Gold → Dashboard) |

## What `test_data_quality.py` covers

Validates intentional defects from `DATA_GENERATION_NOTES.md` §7 against `data/*.csv`:

| Test | Expected |
|------|----------|
| Row counts | 10,000 / 500 / 100,000 |
| NULL customer emails | 50 |
| Duplicate `customer_id` rows | 10 |
| NULL `order.customer_id` | 100 |
| NULL `order.product_id` | 200 |
| Orphan `customer_id` (ghost range 90001–90050) | 50 |
| Orphan `product_id` (ghost range 901–930) | 30 |
| Duplicate `order_id` rows | 20 |
| Total explicit defect participants | 460 |

No Spark or Databricks required — reads CSVs directly.

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Last run:** 9 tests, all PASS (local CSV validation).

## Planned (not implemented)

| File | Purpose |
|------|---------|
| `test_gold_logic.py` | Gold segmentation rules unit tests |
| `test_pipeline_integration.py` | End-to-end Bronze → Silver → Gold in Databricks |

Manual runtime validation: see layer READMEs and `debugging-notes.md`.
