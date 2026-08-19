# AI Prompts — Debugging

## Objective

Document debugging and issue-resolution activities across the pipeline — static code review findings, implementation fixes, runtime interpretation, and manual Databricks Dashboard troubleshooting.

**Stage status:**

| Activity | Status |
|----------|--------|
| Bronze static review issues | Documented |
| Silver implementation fixes | Documented |
| Silver runtime metric interpretation | Documented |
| Dashboard manual UI issues | Documented |
| Consolidated debugging notes | `debugging-notes.md` |

---

## Interaction 1 — Bronze Static Review & Fixes

### Objective

Senior-level static review of Bronze implementation; identify operational gaps before Databricks runtime.

### Exact Prompt Sent

Bronze static code review interaction (see `ai-prompts/05-bronze-layer.md` Interaction 3).

### AI Response Summary

Review identified: partial orchestrator failure handling, column-order validation gap, Unity Catalog assumptions, defect preservation not runtime-proven. Verdict: **APPROVE WITH MINOR RESERVATIONS**.

### What I Accepted

- Fail-fast orchestration improvement.
- Column-order validation in `ingest_utils.py`.

### What I Rejected

- Claiming runtime success before Databricks execution.

### Why

Operational gaps should be fixed or explicitly documented before runtime validation.

### Changes Made

- `src/bronze/ingest_all.py` — fail-fast on entity failure
- `src/bronze/ingest_utils.py` — column-order validation

### Validation

Static review complete. Runtime validation performed separately.

---

## Interaction 2 — Silver NULL-Key Uniqueness Fix

### Objective

Fix uniqueness check incorrectly flagging NULL primary keys.

### Exact Prompt Sent

Silver static fix interaction during implementation (see `ai-prompts/06-silver-layer.md`).

### AI Response Summary

Added `F.col(key_column).isNotNull() & (count > 1)` in `02_quality_uniqueness.py` so NULL PKs are not treated as duplicate-key failures.

### What I Accepted

- NULL exclusion from uniqueness duplicate groups.

### What I Rejected

- Changing uniqueness threshold to accommodate NULLs (defects should still be flagged by other checks).

### Why

NULL keys are completeness/type issues, not uniqueness duplicates.

### Changes Made

- `src/silver/02_quality_uniqueness.py`

### Validation

Static fix. Confirmed in Silver runtime validation (Interaction 4 in `06-silver-layer.md`).

---

## Interaction 3 — Silver Runtime Metric Interpretation

### Objective

Interpret `UNIQUENESS_*` NOT MET results during Databricks runtime validation.

### Exact Prompt Sent

No separate prompt — user executed Silver in Databricks and provided observed metrics.

### AI Response Summary

`UNIQUENESS_CUSTOMERS` (99.9%) and `UNIQUENESS_ORDERS` (99.98%) NOT MET are **expected** due to intentional duplicate keys in Bronze (10 + 20 rows). All other metrics MET. Run ID: `a147c198-45cf-456e-9343-8763d7a75945`.

### What I Accepted

- NOT MET uniqueness as expected behavior, not implementation bug.

### What I Rejected

- Lowering uniqueness threshold to force MET.

### Why

Assignment requires detecting duplicate keys; thresholds correctly surface intentional defects.

### Changes Made

None — documentation only (`ai-prompts/06-silver-layer.md` Interaction 4).

### Validation

Runtime validation complete. See `src/silver/README.md`.

---

## Interaction 4 — Dashboard Manual UI Troubleshooting

### Objective

Resolve issues encountered during manual Databricks SQL Dashboard configuration.

### Exact Prompt Sent

Manual implementation outside Cursor (see `ai-prompts/08-dashboard-layer.md` Interaction 3).

### AI Response Summary

Four issues documented:

1. Counter widgets defaulted to `COUNT(*)` — fixed by setting correct Gold value fields.
2. Customer Count showed `500` with active filter — fixed by resetting filters.
3. `Missing selection for parameter: product_category` — fixed with `All` default.
4. Pie chart misconfiguration — fixed with `segment_type` + `customer_count`.

### What I Accepted

- Manual UI configuration as the correct approach for Databricks CE.

### What I Rejected

- Claiming AI configured the dashboard UI.

### Why

Dashboard UI has no code artifact; manual steps documented in `DASHBOARD_GUIDE.md` and `debugging-notes.md`.

### Changes Made

None in repository — Databricks UI only.

### Validation

All 9 widgets and 5 filters PASS. KPI baseline matches Gold tables.

---

## Interaction 5 — Databricks Automation Runtime Troubleshooting

### Objective

Stabilize one-click execution in `00_run_full_pipeline.ipynb` across Databricks runtime constraints and ensure end-to-end reliability.

### Exact Prompt Sent

User repeatedly requested fully automated execution from Databricks only (no manual local upload), then shared runtime stack traces as blockers appeared.

### AI Response Summary

Resolved multiple environment-specific failures in sequence:

1. **`OSError: [Errno 95] Operation not supported` on `/Volumes/...`**
   - Root cause: atomic replace/rename behavior unsupported in this runtime path.
   - Fix: updated CSV write path handling and fallback logic.

2. **`OSError: [Errno 95] Operation not supported` on `/dbfs/Volumes/...`**
   - Root cause: direct Python file writes still restricted for that mount behavior.
   - Fix: moved generation to workspace path and copy to volume via `dbutils.fs.cp`.

3. **`LocalFilesystemAccessDeniedException` for `file:/local_disk0/...`**
   - Root cause: policy denies non-Workspace local filesystem access.
   - Fix: removed `/local_disk0` dependency; used `repo_path/data` workspace location instead.

4. **Gold stage failure after cleanup**
   - Root cause: validation notebook failed when Gold tables were not rebuilt first.
   - Fix: explicit Gold table build (`create_gold_tables.py`) before `gold_runtime_validation`.

### What I Accepted

- Iterative runtime hardening using real Databricks trace evidence.
- Workspace-path-first strategy for filesystem compatibility.
- Explicit Gold build step in orchestrator notebook.

### What I Rejected

- Claiming success before rerun confirmation after each patch.
- Reintroducing manual data upload as the primary path.

### Why

The assignment goal was one-click automation from Databricks. Runtime constraints varied by environment, so each fix needed to be trace-driven and minimal.

### Changes Made

- `notebooks/00_run_full_pipeline.ipynb`
- `src/data_generation/generate_sample_data.py`

### Validation

Notebook logic now includes stage summaries, explicit Gold build, and compatibility-oriented file handling for constrained Databricks environments.

---

## Consolidated Reference

Full issue list with symptoms and resolutions: `debugging-notes.md`
