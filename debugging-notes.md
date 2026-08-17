# Debugging Notes

## Overview

Record of issues encountered, root causes, and resolutions during pipeline development. Issues span Bronze static review, Silver implementation fixes, Gold/Dashboard design clarifications, and manual Databricks Dashboard UI configuration.

## Issues

### Issue 1 — Bronze orchestrator partial failure handling

- **Symptom:** If one entity ingest failed mid-run, orchestrator behavior was unclear.
- **Root cause:** Initial `ingest_all.py` did not fail fast on first entity error.
- **Resolution:** Added fail-fast orchestration — first entity failure stops the run with context (entity, path, row counts).
- **AI involvement:** Identified in Bronze static code review (Interaction 3); fix applied in Interaction 4.

### Issue 2 — Bronze column-order validation gap

- **Symptom:** CSV with correct columns in wrong order could pass header check inconsistently.
- **Root cause:** Header validation did not enforce column order against expected schema.
- **Resolution:** Column-order validation added to `ingest_utils.py` before read/write.
- **AI involvement:** Static review finding; fix documented in `ai-prompts/05-bronze-layer.md`.

### Issue 3 — Spark Connect / JVM API incompatibility (Bronze)

- **Symptom:** Risk of `spark._jvm`, `spark._jsc`, or Hadoop FileSystem usage on Databricks Serverless.
- **Root cause:** Some Spark patterns are not Spark Connect compatible.
- **Resolution:** Enforced DataFrame + Delta APIs only across Bronze, Silver, and Gold. Documented in all layer READMEs.
- **AI involvement:** Design constraint carried forward from Bronze runtime lessons to Silver/Gold implementation.

### Issue 4 — Silver NULL primary keys flagged as UNIQUENESS failures

- **Symptom:** NULL `customer_id` or `order_id` values could be counted in duplicate-key groups.
- **Root cause:** Uniqueness check used `count > 1` without excluding NULL keys.
- **Resolution:** Added `key_column.isNotNull() & (count > 1)` in `02_quality_uniqueness.py`.
- **AI involvement:** Static fix during Silver implementation review.

### Issue 5 — Silver `REFERENCE_DATE` inconsistency

- **Symptom:** Design draft used `current_date()` for future-date validation; data generation uses fixed `2026-08-15`.
- **Root cause:** Ambiguous reference date between generator and Silver.
- **Resolution:** Finalized `REFERENCE_DATE = 2026-08-15` in `src/silver/config.py` for deterministic runs.
- **AI involvement:** Design clarification interaction documented in `ai-prompts/06-silver-layer.md`.

### Issue 6 — Silver uniqueness metrics NOT MET (expected)

- **Symptom:** `UNIQUENESS_CUSTOMERS` (99.9%) and `UNIQUENESS_ORDERS` (99.98%) below 100% threshold.
- **Root cause:** Intentional duplicate keys in Bronze source data (10 customer, 20 order duplicate rows).
- **Resolution:** No code change — expected behavior. Documented as acceptance criteria pass with explanation.
- **AI involvement:** Runtime validation interpretation in Silver Interaction 4.

### Issue 7 — Dashboard Counter defaulted to COUNT(*)

- **Symptom:** KPI widgets showed row counts instead of Gold metric values.
- **Root cause:** Databricks SQL Dashboard Counter visualization defaults to `COUNT(*)`.
- **Resolution:** Manually set value fields: `total_revenue`, `total_orders`, `customer_count`, `product_count`.
- **AI involvement:** None — manual UI fix recorded in `ai-prompts/08-dashboard-layer.md` Interaction 3.

### Issue 8 — Dashboard Customer Count showed 500 with filter active

- **Symptom:** Customer Count KPI displayed `500` instead of expected `9.94K`.
- **Root cause:** Active dashboard filter (likely Product Category) affecting wrong widget scope during testing.
- **Resolution:** Reset all filters to default; baseline restored to `9.94K`.
- **AI involvement:** None — manual troubleshooting.

### Issue 9 — Missing dashboard parameter selection

- **Symptom:** Error: `Missing selection for parameter: product_category`
- **Root cause:** Product Category filter had no default selection configured.
- **Resolution:** Set multiple-value filter default to `All`.
- **AI involvement:** None — manual UI configuration.

### Issue 10 — Customer Segmentation pie chart misconfiguration

- **Symptom:** Pie chart did not show four behavioral segments correctly.
- **Root cause:** Wrong dimension/measure mapping in initial viz config.
- **Resolution:** Set dimension = `segment_type`, measure = `customer_count` (not revenue).
- **AI involvement:** None — manual UI fix; aligns with design spec DD-08.

## Code Review Notes

| Layer | Verdict | Notes |
|-------|---------|-------|
| Bronze | Approve with minor reservations | Core ingest logic assignment-aligned; runtime validated |
| Silver | Approved | Flag-only DQ; 10 metrics per run; Spark Connect safe |
| Gold | Approved | Silver-only reads; overwrite mode; four aggregations |
| Dashboard | Approved | Gold-only SQL; manual UI per `DASHBOARD_GUIDE.md` |

Static reviews performed before Databricks runtime validation. Full prompt history in `ai-prompts/`.
