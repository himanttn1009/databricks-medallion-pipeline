# Tests

Test suite for data quality validation and pipeline integration.

## Status

| Area | Status |
|------|--------|
| Data quality tests | **Not implemented** |
| Pipeline integration tests | **Not implemented** |
| Manual runtime validation | Complete (Bronze → Silver → Gold → Dashboard) |

Automated tests are referenced in `design-notes.md` (Testing Strategy) and `requirements-analysis.md` but were not implemented in this submission. Runtime validation was performed manually in Databricks.

## Planned Structure

| File (planned) | Purpose |
|----------------|---------|
| `test_data_quality.py` | Verify Silver checks catch intentional ~460 defective rows |
| `test_gold_logic.py` | Verify Gold aggregation calculations |
| `test_pipeline_integration.py` | End-to-end Bronze → Silver → Gold flow |

## Manual Validation Performed

| Layer | Validation |
|-------|------------|
| Data generation | Pre-write `validate_generated_data()` + independent CSV review |
| Bronze | Row counts 10,000 / 500 / 100,000; defects preserved |
| Silver | 10 DQ metrics per run; defect detection; `is_valid` flags |
| Gold | Four tables with expected row counts; assignment aggregations |
| Dashboard | 9 widgets; 5 filters; KPI baseline vs Gold |

See layer READMEs and `debugging-notes.md` for observed results.

## Running Tests (future)

```bash
# Planned — not yet available
pytest tests/
```
