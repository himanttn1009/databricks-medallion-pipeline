# Final AI Usage Summary

## Overview

AI (primarily **Cursor**) was used across the full assessment lifecycle: requirements analysis, architecture design, data generation, Bronze/Silver/Gold implementation, dashboard SQL/documentation, debugging, and documentation. Each major activity has prompt history in `ai-prompts/` with accept/reject reasoning.

Human validation was applied at every stage — design reviews before implementation, static code checks, and manual Databricks runtime validation before claiming success.

## By Lifecycle Phase

| Phase | AI Role | Key Outcomes |
|-------|---------|--------------|
| Requirement analysis | Structured assignment into `requirements-analysis.md` | Ambiguities flagged; acceptance criteria mapped |
| Architecture | Medallion design in `design-notes.md` | Layer boundaries, data flow, decision IDs |
| Data modeling | Schemas in `data-model.md` | Bronze/Silver/Gold column definitions |
| Data generation | Generator design + `generate_sample_data.py` | 10K/500/100K rows; 460 intentional defects |
| Implementation | Layer-by-layer PySpark + SQL | Bronze ingest, Silver DQ, Gold aggregations, dashboard queries |
| Testing | Validation logic design; manual runtime checks | Generator pre-write validation; Databricks row-count verification |
| Debugging | Static review findings; issue documentation | Bronze fail-fast; Silver NULL-key fix; dashboard UI issues |
| Code review | Senior-level static reviews per layer | Documented in `ai-prompts/` and `debugging-notes.md` |
| Documentation | READMEs, guides, prompt history | Layer docs, `DASHBOARD_GUIDE.md`, workflow artifacts |
| Reflection | Workflow and lessons learned | `reflection.md`, this summary |

## What I Accepted vs Rejected

### Accepted

- Gold-only dashboard contract (no Bronze/Silver reads).
- Flag-only Silver DQ — preserve all rows, never silently delete defects.
- Fixed `REFERENCE_DATE = 2026-08-15` for reproducibility.
- `silver.dq_metrics` grain: 10 rows per `(run_id, entity, check_name)`.
- Manual Databricks SQL Dashboard assembly (appropriate for CE scope).
- PySpark/DataFrame Gold implementation (not SQL files).
- No `country` in Gold (`GD-07`); country filter rejected for dashboard.

### Rejected

- Automatic dashboard-as-code / API deployment.
- Country filter via Silver join in dashboard (Gold-only constraint).
- Date filters on lifetime KPI aggregates (trends only).
- `current_date()` for Silver reference date (replaced with fixed date).
- Claiming runtime success without Databricks execution evidence.
- Empty duplicate `ai-prompts/` stub files (removed).

## Validation Approach

1. **Design review** — Spec approved before implementation per layer.
2. **Static verification** — File inventory, forbidden API grep, schema alignment.
3. **Generator validation** — `validate_generated_data()` + independent CSV review.
4. **Databricks runtime** — Bronze → Silver → Gold executed; row counts and DQ metrics recorded.
5. **Dashboard manual test** — 9 widgets, 5 filters, KPI baseline vs Gold tables.

## Reusable Patterns

- **Design-only interaction → implementation interaction** per layer.
- **Explicit prompt constraints** (`DO NOT modify Bronze`, `DO NOT claim runtime`).
- **Decision IDs** in design docs for cross-reference.
- **Layer README + design-notes section** as dual documentation.
- **Prompt history** with Interaction N structure: objective, prompt, summary, accepted/rejected, files changed, validation status.
- **Spark Connect safe APIs** enforced project-wide after Bronze lessons.

## Prompt History Locations

| Activity | File |
|----------|------|
| Data generation | `ai-prompts/04-data-generation.md` |
| Bronze | `ai-prompts/05-bronze-layer.md` |
| Silver | `ai-prompts/06-silver-layer.md` |
| Gold | `ai-prompts/07-gold-layer.md` |
| Dashboard | `ai-prompts/08-dashboard-layer.md` |
| Debugging | `ai-prompts/debugging.md` |
| Documentation | `ai-prompts/documentation.md` |
